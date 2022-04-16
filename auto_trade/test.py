import os
import pyupbit 
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

access = os.getenv('ACCESS_KEY')
secret = os.getenv('SECRET_KEY')

upbit = pyupbit.Upbit(access, secret)

# 잔고 조회
balances = upbit.get_balances()

for balance in balances:
 print(balance)

for i in range(len(balances)):
 print(i, balances[i]['currency'], balances[i]['balance'])


created_at = upbit.get_order('KRW-BTC', 'done')[0].get('created_at')
dt = datetime.fromisoformat(created_at)
print(dt)
print(type(dt))

# 원화 잔고 조회
print("보유 KRW : {}".format(upbit.get_balance(ticker="KRW")))          # 보유 KRW
print("총매수금액 : {}".format(upbit.get_amount('ALL')))                  # 총매수금액
print("비트수량 : {}".format(upbit.get_balance(ticker="KRW-BTC")))      # 비트코인 보유수량
print("리플 수량 : {}".format(upbit.get_balance(ticker="KRW-XRP")))      # 리플 보유수량
print("\n")
print(upbit.get_chance('KRW-BTC')) # 마켓별 주문 가능 정보를 확인
print("\n")
print(upbit.get_order('KRW-XRP')) # 주문 내역 조회