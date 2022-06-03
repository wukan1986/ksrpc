from ksrpc import RpcClient
from ksrpc.connections.http import HttpxConnection

conn = HttpxConnection('http://127.0.0.1:8000/api/file')
conn.timeout = None
client = RpcClient('eikon', conn, async_local=False)
client.cache_get = True
client.cache_expire = 86400

# 这两处按情况按换
ek = client
# import eikon as ek

ek.set_app_key('8e9bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx1b035d')
df, err = ek.get_data(
    instruments=['GOOG.O', 'MSFT.O', 'FB.O'],
    fields=['BID', 'ASK']
)
print(df)

# streaming_prices = ek.StreamingPrices(
#     instruments=['EUR=', 'GBP=', 'JPY=', 'CAD='],
#     fields=['DSPLY_NAME', 'BID', 'ASK'],
#     on_update=lambda streaming_price, instrument_name, fields:
#     print("Update received for {}: {}".format(instrument_name, fields))
# )
#
# streaming_prices.open()

df, err = ek.get_data(
    instruments=['GOOG.O', 'MSFT.O', 'FB.O'],
    fields=['TR.LegalAddressCity', 'TR.LegalAddressLine1', 'TR.Employees']
)
print(df)

ek.get_timeseries('AAPL.O', interval='minute')
ek.get_news_headlines('IBM.N', count=100)
