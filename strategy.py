
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# =====================================
# 1. Load and Merge Data
# =====================================

comex = pd.read_csv("COMEX_GC_data.csv")
binance = pd.read_csv("binance_xauusdt_1m.csv")

comex["timestamp"] = pd.to_datetime(
    comex["Datetime"], utc=True
)

binance["timestamp"] = pd.to_datetime(
    binance["open_time"], utc=True
)

start = pd.Timestamp("2026-11-10 20:00", tz="UTC")
end = pd.Timestamp("2026-11-11 09:00", tz="UTC")

comex = comex[comex["timestamp"].between(start, end)].copy()
binance = binance[binance["timestamp"].between(start, end)].copy()

comex["timestamp"] = comex["timestamp"].dt.floor("min")
binance["timestamp"] = binance["timestamp"].dt.floor("min")

spread_df = pd.merge(
    comex[["timestamp", "Close"]],
    binance[["timestamp", "close"]],
    on="timestamp",
    how="inner"
)

spread_df["Close"] = pd.to_numeric(spread_df["Close"])
spread_df["close"] = pd.to_numeric(spread_df["close"])

# Spread = COMEX - Binance
spread_df["spread"] = (
    spread_df["Close"] - spread_df["close"]
)

spread_df = spread_df.set_index("timestamp").sort_index()

# =====================================
# 2. Strategy Parameters
# =====================================

WINDOW = 120
ENTRY_Z = 1.5
ADD_STEP_Z = 0.1
STOP_Z = 3.0
MAX_LAYERS = 10

CAPITAL = 10000
LAYER_SIZE = 1.0

# =====================================
# 3. Calculate Z-score
# =====================================

spread_df["rolling_mean"] = (
    spread_df["spread"].rolling(WINDOW).mean().shift(1)
)

spread_df["rolling_std"] = (
    spread_df["spread"].rolling(WINDOW).std().shift(1)
)

spread_df["z_score"] = (
    (spread_df["spread"] - spread_df["rolling_mean"])
    / spread_df["rolling_std"]
)


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# =====================================
# 1. Fixed Parameters
# =====================================

ADD_STEP_Z = 0.1
STOP_Z = 3.0
MAX_LAYERS = 10
CAPITAL = 10000
LAYER_SIZE = 1.0

# =====================================
# 2. Backtest Function
# =====================================

def backtest(entry_z):

    position = 0
    entry_spreads = []
    realized_pnl = 0.0
    equity = [CAPITAL]

    for i in range(121, len(spread_df)):

        previous = spread_df.iloc[i - 1]
        current = spread_df.iloc[i]

        z = previous["z_score"]
        price = current["spread"]

        # Skip market closure gaps
        if (
            spread_df.index[i] - spread_df.index[i - 1]
            > pd.Timedelta(minutes=1)
        ):
            equity.append(equity[-1])
            continue

        if position != 0:

            # Exit
            if position * z >= 0 or -position * z >= STOP_Z:

                pnl = sum(
                    position * (price - entry)
                    * LAYER_SIZE
                    for entry in entry_spreads
                )

                realized_pnl += pnl
                position = 0
                entry_spreads = []

            # Additional entry
            elif len(entry_spreads) < MAX_LAYERS:

                next_level = (
                    entry_z
                    + len(entry_spreads) * ADD_STEP_Z
                )

                if -position * z >= next_level:
                    entry_spreads.append(price)

        # Initial entry
        elif entry_z <= abs(z) < STOP_Z:

            position = -1 if z > 0 else 1
            entry_spreads = [price]

        unrealized_pnl = sum(
            position * (price - entry)
            * LAYER_SIZE
            for entry in entry_spreads
        )

        equity.append(
            CAPITAL + realized_pnl + unrealized_pnl
        )

    equity = pd.Series(
        equity,
        index=spread_df.index[120:]
    )

    returns = equity.pct_change().dropna()

    annual_factor = 252 * 23 * 60

    if returns.std() == 0:
        return np.nan

    sharpe = (
        returns.mean()
        / returns.std()
        * np.sqrt(annual_factor)
    )

    return sharpe, equity



# =====================================
# 1. Sharpe Ratio Sensitivity Analysis
# =====================================

entry_values = np.round(
    np.arange(1.50, 2.001, 0.01), 3
)

sharpe_values = []

for entry_z in entry_values:

    sharpe, equity = backtest(entry_z)
    sharpe_values.append(sharpe)

    print(
        f"Entry Z = {entry_z:.2f}, "
        f"Sharpe = {sharpe:.4f}"
    )

plt.figure(figsize=(10, 5))
plt.plot(entry_values, sharpe_values, marker="o")

plt.xlabel("Entry Z-score")
plt.ylabel("Annualized Sharpe Ratio")
plt.title("Sharpe Ratio vs Entry Z-score")
plt.grid(True)
plt.tight_layout()

plt.savefig("1.png", dpi=300)
plt.close()


# =====================================
# 2. Equity Curves at 0.10 Intervals
# =====================================

equity_entries = np.round(
    np.arange(1.50, 2.001, 0.10), 2
)

for i, entry_z in enumerate(equity_entries, start=2):

    sharpe, equity = backtest(entry_z)

    plt.figure(figsize=(12, 5))

    plt.plot(
        equity.index,
        equity.values,
        label=f"Entry Z = {entry_z:.2f}"
    )

    plt.xlabel("Time (UTC)")
    plt.ylabel("Portfolio Equity")
    plt.title(
        f"Equity Curve - Entry Z = {entry_z:.2f}"
    )

    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    # plt.savefig(f"{i}.png", dpi=300)
    # plt.close()

    print(
        f"Saved {i}.png "
        f"(Entry Z = {entry_z:.2f}, "
        f"Sharpe = {sharpe:.4f})"
    )


