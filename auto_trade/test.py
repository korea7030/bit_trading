import os
import pyupbit 
from datetime import datetime
from dotenv import load_dotenv
from common import trade

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

buy_amt_unit = 4.5     #최소 오픈 수량
increace_rate = 0.248
# message, result = trade.get_current_price(upbit, 'KRW-BTC')
message, buy_amt, buy_price = trade.get_balances(upbit, 'KRW-BTC')
print(pyupbit.get_ohlcv('KRW-BTC', 'minute5', count=1))
order_buy_amt = buy_amt_unit + float(buy_amt) * increace_rate
message, result = trade.get_current_price(upbit, 'KRW-BTC')
# 거래 단위 조정
trade_price = "{:0.0{}f}".format(float(result), 0) #정수
trade_amt = "{:0.0{}f}".format(order_buy_amt, 4)  #소수점 넷째자리
print('result ::: ', result)
buy_profit = ((result - buy_price) / buy_price) * 100  # 수익률
max_loss_rate = 0.239 #손절 비율 0.239
trade.stop_loss(upbit, 'KRW-BTC', buy_amt, buy_price, trade_price, max_loss_rate)
print('================= 거래 단위 :::: {}, {} =================='.format(trade_price, trade_amt))
print('수익률 ::: {}'.format(buy_profit))
# 원화 잔고 조회
# print("보유 KRW : {}".format(upbit.get_balance(ticker="KRW")))          # 보유 KRW
# print("총매수금액 : {}".format(upbit.get_amount('ALL')))                  # 총매수금액
# print("비트수량 : {}".format(upbit.get_balance(ticker="KRW-BTC")))      # 비트코인 보유수량
# print("리플 수량 : {}".format(upbit.get_balance(ticker="KRW-XRP")))      # 리플 보유수량
# print("\n")
# print(upbit.get_chance('KRW-BTC')) # 마켓별 주문 가능 정보를 확인
# print("\n")
# print(upbit.get_order('KRW-XRP')) # 주문 내역 조회