from pybit.unified_trading import HTTP

session = HTTP(
    testnet=True,
    api_key="",
    api_secret="",
)
print(session.get_wallet_balance(
    accountType="UNIFIED",
    coin="BTC",
))