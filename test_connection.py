import MetaTrader5 as mt5

MT5_PATH = r"C:\JEV01-Automate\MT5\terminal64.exe"

print("=" * 60)
print("JEV01-Automate MT5 CONNECTION TEST")
print("=" * 60)

if not mt5.initialize(path=MT5_PATH):
    print("MT5 INITIALIZATION FAILED")
    print("Error:", mt5.last_error())
    raise SystemExit(1)

terminal = mt5.terminal_info()
account = mt5.account_info()

print("\nTERMINAL")
print("Path:", terminal.path)
print("Data:", terminal.data_path)
print("Connected:", terminal.connected)
print("Trade allowed:", terminal.trade_allowed)

print("\nACCOUNT")
print("Login:", account.login)
print("Server:", account.server)
print("Company:", account.company)
print("Balance:", account.balance)
print("Equity:", account.equity)
print("Trade allowed:", account.trade_allowed)

symbol = "XAUUSD"

info = mt5.symbol_info(symbol)

print("\nSYMBOL")
print("Symbol:", symbol)
print("Exists:", info is not None)

if info:
    print("Visible:", info.visible)
    print("Trade mode:", info.trade_mode)
    print("Point:", info.point)
    print("Digits:", info.digits)

print("\n" + "=" * 60)
print("JEV01 CONNECTION TEST COMPLETE")
print("=" * 60)

mt5.shutdown()