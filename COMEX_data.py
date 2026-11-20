import yfinance as yf
import pandas as pd


start = pd.Timestamp('2026-11-06 12:21:00', tz='UTC')
end = pd.Timestamp('2026-11-11 12:21:00', tz='UTC')

# COMEX Gold Futures (GC=F) data
df_gc = yf.download('GC=F', start=start, end=end, interval='1m')

print("Number of candles:", len(df_gc))

# save the data to a CSV file
df_gc.to_csv('COMEX_GC_data.csv')