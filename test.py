import pyupbit

access = "ASNWxupj3DmBAJUrx4j7MqQS0gQgFHQj7BkF4r4e"          # 본인 값으로 변경
secret = "fobm7pIUKXMjuVCWkJbWWnjfugl9lkxctVBQlaIl"          # 본인 값으로 변경
upbit = pyupbit.Upbit(access, secret)

print(upbit.get_balance("KRW-BTC"))     # KRW-BTC 조회
print(upbit.get_balance("KRW"))         # 보유 현금 조회

upbit.buy_market_order("KRW-UXLINK", 6000)