import requests
import pandas as pd
import time

# binance future API
BASE_URL = "https://fapi.binance.com"
endpoint = "/fapi/v1/continuousKlines"

# download 50000 candles of XAUUSDT 1-minute data
def download_historical_data(
    pair = 'XAUUSDT',
    interval = '1m',
    total_candles = 50000,
    batch_size = 500
):
    all_data = []
    end_time = None

    while len(all_data) < total_candles:
        params = {
            'pair': pair,
            'contractType': 'TRADIFI_PERPETUAL',
            'interval': interval,
            'limit': batch_size
        }

        if end_time is not None:
            params['endTime'] = end_time

        # request historical data
        response = requests.get(BASE_URL + endpoint, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        # update the end_time for the next batch to avoid duplicates
        oldest_time = data[0][0]
        end_time = oldest_time - 1

        # check if the request was successful
        if not isinstance(data, list) or len(data) == 0:
            raise ValueError(f"Unexpected API response: {data}")

        all_data.extend(data)

        time.sleep(0.5)  # to avoid hitting rate limits

    return all_data[:total_candles]


# convert the json into pandas dataframe
columns = [
    "open_time", "open", "high", "low",
    "close", "volume", "close_time",
    "quote_volume", "trades",
    "taker_buy_base", "taker_buy_quote",
    "ignore"
]
df = pd.DataFrame(download_historical_data(), columns=columns)

# convert timestamps
df['open_time'] = pd.to_datetime(
    df['open_time'],
    unit = 'ms',
    utc = True
)

# convert prices to numeric values
for col in ['open', 'high', 'low', 'close', 'volume']:
    df[col] = pd.to_numeric(df[col])

# keep columns needed
df = df[['open_time', 'open', 'high', 'low', 'close', 'volume']]

# sort by open_time and drop duplicates
df = (
    df.drop_duplicates(subset='open_time')
      .sort_values('open_time')
      .reset_index(drop=True)
)

print(df.head())
print('Number of candles:', len(df))

# save historical data to csv file
df.to_csv('binance_xauusdt_1m.csv', index=False) # no need to save index from pandas
print("Historical data saved to binance_xauusdt_1m.csv")