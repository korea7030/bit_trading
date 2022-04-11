from dotenv import load_dotenv
import os
import pyupbit
import time
import utils
import trade


load_dotenv()

access = os.getenv('ACCESS_KEY')
secret = os.getenv('SECRET_KEY')

coin_name = 'KRW-BTC'
upbit = pyupbit.Upbit(access, secret)

revenue_rate = 0.05  # 익절비율(5%)
s5m = 0  # 5분봉 데이터

tic = 0 # 실제 tic count (거래시에 사용)
tic_count = 0 # 음봉 시 틱 발생 count
tic_start = 0 # 직전 마감가 저장용

m5_df = None  # 5분 데이터(global)

utils.log_info('*********** start trading ***********')

# 미체결 주문 취소
message = trade.cancel_all_order(upbit, coin_name)
if message != 'good':
    utils.log_info("+[{}]cancel_wait_order error msg:{}".format(
                   utils.get_time_hhmmss(time.time()), message))

while True:
    check_ss = utils.get_time_ss(time.time())

    # 데이터 가져오기.(5분봉, 1분봉)
    # 5분봉 : 틱 계산 및 5분봉3틱룰 적용(매수)
    # 1분봉 : 5분봉 3틱룰 적용됐을 시에 수익률 비교해서 매도하는 로직
    if check_ss in ('01', '02'):
        m1_df = pyupbit.get_ohlcv(coin_name, 'minute1', count=1)
        stick_size = m1_df['open'] = m1_df['close']

        if stick_size > 0:
            pass
        elif stick_size < 0:
            pass
        # 5분봉 데이터 비교(1분마다 실행했을때 다음 5분봉을 가져왔는지 체크 필요)
        current_m5_df = pyupbit.get_ohlcv(coin_name, 'minute5', count=1)

        m5_df = current_m5_df
        
