import pyupbit 

access_key = "OS2zw6iLXxSlWSBWQ8rQ1pDm9xt4fLNJs8efHIh6"
secret_key = "ndCQxHjGXUpGhZHWL8MzwC7yYnga2pAxE19KrRfG"
upbit = pyupbit.Upbit(access_key, secret_key)

# 잔고 조회
balances = upbit.get_balances()

for balance in balances:
 print(balance)

for i in range(len(balances)):
 print(i, balances[i]['currency'], balances[i]['balance'])


# 원화 잔고 조회
print("보유 KRW : {}".format(upbit.get_balance(ticker="KRW")))          # 보유 KRW
print("총매수금액 : {}".format(upbit.get_amount('ALL')))                  # 총매수금액
print("비트수량 : {}".format(upbit.get_balance(ticker="KRW-BTC")))      # 비트코인 보유수량
print("리플 수량 : {}".format(upbit.get_balance(ticker="KRW-XRP")))      # 리플 보유수량
print("\n")
print(upbit.get_chance('KRW-BTC')) # 마켓별 주문 가능 정보를 확인
print("\n")
print(upbit.get_order('KRW-XRP')) # 주문 내역 조회