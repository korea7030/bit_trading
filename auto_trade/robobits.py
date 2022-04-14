from dotenv import load_dotenv
import os
import pyupbit
import time
import utils
import trade


load_dotenv()

RESET_COLUMNS = { 'index': 'timestamp', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume', 'value': 'value'}

access = os.getenv('ACCESS_KEY')
secret = os.getenv('SECRET_KEY')

coin_name = 'KRW-BTC'
upbit = pyupbit.Upbit(access, secret)

revenue_rate = 0.05  # 익절비율(5%)
s5m = 0  # 5분봉 데이터

tic = 0 # 실제 tic count (거래시에 사용)
tic_count = 0 # 음봉 시 틱 발생 count
tic_start = 0 # 직전 마감가 저장용

m5_df = None  # 5분 데이터(global) - 비교할때 사용
before_5ae_df = None # 이전 5분봉의 다섯개봉 df
before5_mean_stick_size = 0  # 이전 5분봉 다섯개봉의 평균stick size

prev_data_df = None  # 이전 데이터

def get_stick_size(open, close):
    '''stick size 함수(이전 5개봉 가져오는데 사용)'''
    return abs(open - close)

utils.log_info('*********** start trading ***********')

# 미체결 주문 취소
message = trade.cancel_all_order(upbit, coin_name)
if message != 'good':
    utils.log_info("+[{}]cancel_wait_order error msg:{}".format(
                   utils.get_time_hhmmss(time.time()), message))


now = utils.get_current_time(time.time())

while True:
    check_ss = utils.get_time_ss(time.time())
    current_m5_df = None  # 현시점에서의 조회한 5분봉 데이터프레임

    # 데이터 가져오기.(5분봉, 1분봉)
    # 5분봉 : 틱 계산 및 5분봉3틱룰 적용(매수)
    # 1분봉 : 5분봉 3틱룰 적용됐을 시에 수익률 비교해서 매도하는 로직
    if check_ss in ('01', '02'):
        '''
        01, 02초 시점에는 데이터 가져오는 것만 수행.
        봉이 생긴지 초기이기 때문
        '''
        m1_df = pyupbit.get_ohlcv(coin_name, 'minute1', count=1)
        m1_reset_df = m1_df.reset_index()
        m1_reset_df.rename(columns=RESET_COLUMNS)

        # 5분봉 데이터 비교(1분마다 실행했을때 다음 5분봉을 가져왔는지 체크 필요)
        current_m5_df = pyupbit.get_ohlcv(coin_name, 'minute5', count=1)
        current_m5_reset_df = current_m5_df.reset_index()
        current_m5_reset_df.rename(columns=RESET_COLUMNS)
        print('current_m5_df ::: ', current_m5_reset_df.head())

        m5_df = current_m5_reset_df
        prev_data_df = pyupbit.get_ohlcv(coin_name, 'minute5', to=current_m5_reset_df['timestamp'], count=1)
        prev_data_reset_df = prev_data_df.reset_index()
        prev_data_reset_df.rename(columns=RESET_COLUMNS)

        stick_size = m5_df['open'] = m5_df['close']

        print('{} :::: {} '.format(check_ss, stick_size))

        # 이전 5분봉 5개봉의 평균 구하기위한 dataframe
        before_5ae_df = pyupbit.get_ohlcv(coin_name, 'minute5', to=m1_reset_df['timestamp'], count=5)
        before_5ae_reset_df = before_5ae_df.reset_index()
        before_5ae_reset_df.rename(columns=RESET_COLUMNS)

        before_5ae_df['stick_size'] = before_5ae_df.apply(lambda x: get_stick_size(x['open'], x['close']), axis=1)
        before5_mean_stick_size = before_5ae_df['stick_size'].mean()
    
    if check_ss in ('59', '00'):
        '''
        이 시점에 5분봉3틱룰 계산하도록
          - 1. 매도만 진행(5분데이터가 같은 경우)
          - 2. 5분봉3틱룰 수행
        '''
        if current_m5_df == m5_df:
            '''
            1. 수익률 비교 후 매도만 진행
              - 01, 02초때 조회한 현 시점의 5분봉데이터와 global 5분봉 데이터비교하여 같으면 5분이 안지났다는 신호로 간주
              - 단 매도 조건은 구매이력이 now 값 이후 이력이 있을 시에 수익률 체크 후 매도하도록
            '''
            pass
        else:
            '''
            2. 5분봉3틱룰 수행
            '''
            if stick_size > 0:
                print('======================= 음봉전환 stick_size :: {} ================'.format(stick_size))
                print('=============={} 음봉전환 ================'.format(m1_df['timestamp']))
                print('=============={} 이전 5분봉 크기 : {} ============'.format(m1_df['timestamp'], before5_mean_stick_size))
                tic_count += 1
                
                if abs(stick_size) >= before5_mean_stick_size * 2:
                    print('============= 이전 5봉 평균보다 크다 현재 봉 : {}, 이전5봉 : {} ========== '.format(abs(stick_size), abs(before5_mean_stick_size)))

                    if tic_count <= 1:
                        tic += 1
                    tic_start = prev_data_df['close']
                
                if tic_count == 2:
                    if m5_df['close'] <= tic_start * (1-0.0005):
                        tic += 1
                
                if tic_count > 0:
                    print('======================== 누적 tic_count 가 2초과인 경우의 tic 계산 ====================')
                    if m5_df['close'] <= tic_start * (1-0.0005):
                        tic += 1
                        tic_start = m5_df['close']
                    
                if tic >= 3:
                    print('==================== 구매 tic : {} ==============='.format(tic))
            elif stick_size < 0:
                print('======================= 양봉전환 stick_size :: {} ================'.format(stick_size))
                # 계좌 조회(message, 잔고, 평균구매금액)
                message, buy_amt, buy_price = trade.get_balances(upbit, coin_name)
                if message != "good":
                    utils.log_info("+[{}]stop loss-get_balances error msg:{}".
                                format(utils.get_time_hhmmss(time.time()), message))
                    continue
                
                # 잔고가 있는 경우
                if float(buy_amt) > 0:
                    # 현재가 조회(message, result)
                    message, result = trade.get_current_price(upbit, coin_name)
                    if message != "good":
                        utils.log_info("+[{}]stop loss-get_current_price error msg:{}".
                                    format(utils.get_time_hhmmss(time.time()), message))
                        continue
                    
                    # 수익률 : (코인현재가 - 매수평균가) / 매수평균가 * 100
                    buy_profit = ((result - buy_price) / buy_price) * 100
                    print('============== 수익률 {} ================='.format(buy_profit))

                    if tic >= 3:
                        if buy_profit >= revenue_rate:
                            print('매도')
                    else:
                        tic_count = 0
                        tic_start = 0
                        tic = 0
                    
                # 매도를 안해도 양봉전환 되면 초기화
                tic_count = 0
                tic_start = 0
                tic = 0