import pyupbit
import time

from config.mock_upbit import MockUpbit
from trader.basic_trader import BasicTrader


import pandas as pd

from trader import BasicTrader
from config.mock_upbit import MockUpbit


def check_available_bought_price(
    price,  # 매수 가격
    low,    # 다음 시점 저가
    high,   # 다음 시점 고가
):
    assert low <= high
    # 저가 보다 매수 가격이 큰 경우 거래 가능
    if low < price:
        # 고가 보다 매수 가격이 큰 경우 고가로 거래
        return True, min(high, price)
    return False, None


def check_available_sold_price(
    price,  # 매도 가격
    low,    # 다음 시점 저가
    high,   # 다음 시점 고가
):
    assert low <= high
    # 고가 보다 매도 가격이 작은 경우 거래 가능
    if price < high:
        # 저가 보다 매도 가격이 작은 경우 저가로 거래
        return True, max(price, low)
    return False, None

def get_stick_size(open, close):
    '''stick size 함수(이전 5개봉 가져오는데 사용)'''
    return abs(open - close)

def backtesting(
    test_data,
    seed_money = 1000000,
    ticker = 'KRW-BTC'
):
    upbit = MockUpbit(seed_money, ticker)
    trader = BasicTrader(upbit=upbit, ticker=ticker)

    tic = 0 # 실제 tic count (거래시에 사용)
    tic_count = 0 # 음봉 시 틱 발생 count
    tic_start = 0 # 직전 마감가 저장용
    prev_data = None

    # 모든 시점에 대해 for-loop을 돕니다.
    for t in range(test_data.shape[0] - 1):

        # t 시점의 데이터를 불러옵니다.
        data = test_data.iloc[t]
        # low, high = test_data["low"].iloc[-1], test_data["high"].iloc[-1]

        next_data = test_data.iloc[t+1]
        low, high = next_data["low"], next_data["high"]

        # 이전봉 데이터        
        prev_data = test_data.iloc[t-1]
        if prev_data.empty:
            print('=========== prev_data empty ================')
            time.sleep(0.1)
            prev_data = pyupbit.get_ohlcv(ticker, 'minute', to=data['timestamp'], count=1)
        
        time.sleep(0.1)
        before5_df = pyupbit.get_ohlcv(ticker, 'minute5', to=data['timestamp'], count=5)
        before5_df['stick_size'] = before5_df.apply(lambda x: get_stick_size(x['open'], x['close']), axis=1)
        before5_mean_stick_size = before5_df['stick_size'].mean()

        stick_size = data['open'] - data['close']

        # 음봉 전환
        if stick_size > 0:
            print('======================= 음봉전환 stick_size :: {} ================'.format(stick_size))
            print('=============={} 음봉전환 ================'.format(data['timestamp']))
            print('=============={} 이전 5분봉 크기 : {} ============'.format(data['timestamp'], before5_mean_stick_size))
            tic_count += 1
        
            # 이전 다섯봉 평균보다 2,3배 이상 로직 추가
            if abs(stick_size) >= before5_mean_stick_size * 2:
                print('============= 이전 5봉 평균보다 크다 현재 봉 : {}, 이전5봉 : {} ========== '.format(abs(stick_size), abs(before5_mean_stick_size)))

                if tic_count <= 1:
                    tic += 1
            tic_start = prev_data['close'] # 직전 마감가
    
            if tic_count == 2:
                # 전종가 * 0.0005 >= 현종가
                if data['close'] <= tic_start * (1-0.0005):
                    tic += 1

            # 음봉 전환 후 두번째 틱 계산
            if tic_count > 2:
                print('======================== 누적 tic_count 가 2초과인 경우의 tic 계산 ====================')
                if data['close'] <= tic_start * (1-0.0005) : # 일정금액 보다 크면 tic count
                    tic += 1
                    tic_start = data['close'] # tic count시의 직전가
                
            if tic >= 3:
                print('==================== 구매 tic : {} ==============='.format(tic))
                # 구매 금액 체크
                available, price = check_available_bought_price(data['close'], low, high)
                if available:
                    # 구매
                    trader.buy(price)
                    print('======================== {} 시간 매수 완료 : {} =============== '.format(data['timestamp'], price))
                    print('============================= {} 시간 가격 : {}, 매수평균 금액 : {} ==============='.format(data['timestamp'], price, upbit.balances[ticker]['avg_buy_price']))
                    tic_count = 0
                    tic_start = 0
                    tic = 0
            print('###################################################### tic_count : {}, tic : {}, tic_start: {} ######################################################'.format(tic_count, tic, tic_start))
        elif stick_size < 0: # 양봉전환
            print('======================= 양봉전환 stick_size :: {} ================'.format(stick_size))
            if upbit.balances[ticker]['avg_buy_price'] > 0:
                # (코인현재가(data['close']) - 매수평균가('avg_buy_price')) / 매수평균가(avg_buy_price) * 100
                # 실시간으로 할 경우 현재가를 가져오기 떄문에 더 정확함. 백테스팅은 정확하기 힘듦
                buy_profit = ((upbit.balances[ticker]['balance'] * data['close']) - (upbit.balances[ticker]['balance'] * upbit.balances[ticker]['avg_buy_price'])) * 100 / upbit.balances[ticker]['avg_buy_price']
                # (float(nowPrice)- float(value['avg_buy_price'])) * 100.0 / float(value['avg_buy_price'])
                print('============== 수익률 {} ================='.format(buy_profit))
                if tic >= 3:
                    if buy_profit >= 0.05:
                        available, price = check_available_sold_price(data['close'], low, high)
                        # TODO: 특정 금액보다 양봉이 크게 일어난 경우 구매 로직 추가 필요
                        if available:
                            trader.sell(price)

                            # 구매하면 초기화
                            tic_start = 0
                            tic_count = 0
                            tic = 0

                            print('======================== {} 시간 매도 완료 : {} =============== '.format(data['timestamp'], price))
                            print('======================== {} 시점 balance : {} ================ '.format(data['timestamp'], trader.krw_balance))
                else:
                    # 양봉전환인데 매도 못한경우
                    tic_count = 0
                    tic_start = 0
                    tic = 0

            # 매도를 안해도 양봉전환 되면 초기화
            tic_count = 0
            tic_start = 0
            tic = 0

        # 입력된 t 시점의 데이터를 바탕으로
        # 살지, 팔지, 그대로 있을지와 거래 금액을 결정합니다.
        # status, price = trader.check_market_status_price(data)

        # # t + 1 시점의 데이터 중 저가와 고가를 추출합니다.
        

        # if status == "buy":
        #     # 거래 금액 제약을 확인합니다.
        #     available, price = check_available_bought_price(price, low, high)
        #     if available:
        #         trader.buy(price)

        # elif status == "sell":
        #     # 거래 금액 제약을 확인합니다.
        #     available, price = check_available_sold_price(price, low, high)
        #     if available:
        #         trader.sell(price)

    # 최근 코인 가격으로 총 자산을 계산합니다.
    recent_ticker_price = test_data["close"].iloc[-1]
    total_balance = (
        trader.krw_balance
        + trader.ticker_balance * recent_ticker_price
    )

    # 초기 자본금 대비 수익률을 계산합니다.
    ROI = ((total_balance - seed_money) / seed_money) * 100
    print(ROI, "% !!!!!")

    return ROI
 