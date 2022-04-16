from dotenv import load_dotenv
import os
import pyupbit
import time
from common import utils
from common import trade


load_dotenv()

RESET_COLUMNS = { 'index': 'timestamp', 'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'volume': 'volume', 'value': 'value'}

access = os.getenv('ACCESS_KEY')
secret = os.getenv('SECRET_KEY')

coin_name = 'KRW-BTC'
upbit = pyupbit.Upbit(access, secret)

revenue_rate = 0.05  # 익절비율(5%)
max_loss_rate = 0.239 #손절 비율 0.239
increace_rate = 0.248
buy_amt_unit = 4.5     #최소 오픈 수량

tic = 0 # 실제 tic count (거래시에 사용)
tic_count = 0 # 음봉 시 틱 발생 count
tic_start = 0 # 직전 마감가 저장용

# 5분 데이터(global) - 비교할때 사용
global m5_datetime
m5_datetime = None

before_5ae_df = None # 이전 5분봉의 다섯개봉 df
before5_mean_stick_size = 0  # 이전 5분봉 다섯개봉의 평균stick size
process_sleep_time = 0.2    #대시시간

order_uuid = ""        #매수 주문 아이디
# profit_uuid = ""       #이익 실현 주문 아이디
stop_uuid = ""         #손실 최소화 주문 아이디

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
        m1_reset_df = m1_reset_df.rename(columns=RESET_COLUMNS)

        # 5분봉 데이터 비교(1분마다 실행했을때 다음 5분봉을 가져왔는지 체크 필요)
        current_m5_df = pyupbit.get_ohlcv(coin_name, 'minute5', count=1)
        current_m5_reset_df = current_m5_df.reset_index()
        current_m5_reset_df = current_m5_reset_df.rename(columns=RESET_COLUMNS)

        prev_data_df = pyupbit.get_ohlcv(coin_name, 'minute5', to=current_m5_reset_df['timestamp'][0], count=1)
        prev_data_reset_df = prev_data_df.reset_index()
        prev_data_reset_df = prev_data_reset_df.rename(columns=RESET_COLUMNS)

        stick_size = current_m5_reset_df['open'][0] - current_m5_reset_df['close'][0]

        # 이전 5분봉 5개봉의 평균 구하기위한 dataframe
        before_5ae_df = pyupbit.get_ohlcv(coin_name, 'minute5', to=m1_reset_df['timestamp'][0], count=5)
        before_5ae_reset_df = before_5ae_df.reset_index()
        before_5ae_reset_df = before_5ae_reset_df.rename(columns=RESET_COLUMNS)

        before_5ae_reset_df['stick_size'] = before_5ae_reset_df.apply(lambda x: get_stick_size(x['open'], x['close']), axis=1)
        before5_mean_stick_size = before_5ae_reset_df['stick_size'].mean()

        if current_m5_reset_df['timestamp'][0] == m5_datetime:
            '''
            1. 수익률 비교 후 매도만 진행
              - 01, 02초때 조회한 현 시점의 5분봉데이터와 global 5분봉 데이터비교하여 같으면 5분이 안지났다는 신호로 간주
              - 단 매도 조건은 구매이력이 now 값 이후 이력이 있을 시에 수익률 체크 후 매도하도록
            '''
            print('====================== 5분봉이 같은 경우, 매도로직 진입 =====================')
            
            print('====================== 5분봉 수행후의 거래가 있는지 확인 ====================')
            after_5m_latest_order_datetime = trade.get_order_info(upbit, coin_name, 'done')

            if after_5m_latest_order_datetime > now:
                print('====================== 5분봉 3틱룰 수행 후 구매한 거래내역이 있다!! ============= ')
                # 잔고 조회(잔고, 평균매입금액)
                message, buy_amt, buy_price = trade.get_krw_balance(upbit)
                if message != "good":
                    utils.log_info("+[{}]stop loss-get_balances error msg:{}".
                            format(utils.get_time_hhmmss(time.time()), message))
                    continue
                time.sleep(process_sleep_time)

                if float(buy_amt) > 0:
                    #현재가 조회
                    message, result = trade.get_current_price(upbit, coin_name)
                    if message != "good":
                        utils.log_info("+[{}]stop loss-get_current_price error msg:{}".
                                    format(utils.get_time_hhmmss(time.time()), message))
                        continue
                    
                    buy_profit = ((result - buy_price) / buy_price) * 100  # 수익률

                    if buy_profit >= revenue_rate:  # 0.05 보다 수익률이 크면, 매도 실행
                        #손실최소화 주문
                        message, uuid = trade.stop_loss(upbit, coin_name, buy_amt, buy_price, result, max_loss_rate)

                        if message == "good":
                            stop_uuid = uuid
                            utils.log_info(
                                "*[{}]stop loss id:{} buy_amt:{} buy_price:{} now_price:{} msg:{}".format(
                                    utils.get_time_hhmmss(time.time()), stop_uuid, buy_amt,
                                    buy_price, result, message)
                            )
                        time.sleep(process_sleep_time)
        else:
            '''
            2. 5분봉3틱룰 수행
            '''
            if stick_size > 0:
                print('======================= 음봉전환 stick_size :: {} ================'.format(stick_size))
                print('=============={} 음봉전환 ================'.format(current_m5_reset_df['timestamp'][0]))
                print('=============={} 이전 5분봉 크기 : {} ============'.format(current_m5_reset_df['timestamp'][0], before5_mean_stick_size))
                tic_count += 1
                
                if abs(stick_size) >= before5_mean_stick_size * 2:
                    print('============= 이전 5봉 평균보다 크다 현재 봉 : {}, 이전5봉 : {} ========== '.format(abs(stick_size), abs(before5_mean_stick_size)))

                    if tic_count <= 1:
                        tic += 1
                    tic_start = prev_data_reset_df['close'][0]
                
                if tic_count == 2:
                    if current_m5_reset_df['close'][0] <= tic_start * (1-0.0005):
                        tic += 1
                
                if tic_count > 2:
                    print('======================== 누적 tic_count 가 2초과인 경우의 tic 계산 ====================')
                    if current_m5_reset_df['close'][0] <= tic_start * (1-0.0005):
                        tic += 1
                        tic_start = current_m5_reset_df['close'][0]
                    
                if tic >= 3:
                    print('==================== 구매 tic : {} ==============='.format(tic))
                    if order_uuid != "":
                        message, status, price, amt = trade.get_order_status(upbit, coin_name, order_uuid)
                        if message != "good":
                            utils.log_info("+[{}]cancel before timestep-get_order_state error msg:{} uuid:{}".
                                        format(utils.get_time_hhmmss(time.time()), message, order_uuid))
                            continue

                        if status == "done": # 주문체결
                            order_uuid = ""

                        if status == "wait": #미체결, 주문 취소
                            message, result = trade.cancel_order(upbit, order_uuid)
                            if message != "good":
                                utils.log_info("+[{}]cancel before timestep-cancel_order error msg:{} uuid:{}".
                                            format(utils.get_time_hhmmss(time.time()), message, order_uuid))
                                continue
                            time.sleep(process_sleep_time)
                    

                    #계좌조회
                    message, buy_amt, buy_price = trade.get_krw_balance(upbit)
                    if message != "good":
                        utils.log_info("+[{}]buy coin-get_balances error msg:{}".
                                    format(utils.get_time_hhmmss(time.time()), message))
                        continue
                    time.sleep(process_sleep_time)

                    #현재가 조회
                    message, result = trade.get_current_price(upbit, coin_name)
                    if message != "good":
                        utils.log_info("+[{}]take profit-get_current_price error msg:{}".
                                    format(utils.get_time_hhmmss(time.time()), message))
                        continue
                    close = float(result)

                    order_buy_amt = buy_amt_unit + float(buy_amt) * increace_rate

                    # 현재가 조회
                    message, result = trade.get_current_price(upbit, coin_name)
                    if message != "good":
                        utils.log_info("+[{}]buy coin-get_current_price error msg:{}".
                                    format(utils.get_time_hhmmss(time.time()), message))
                        continue

                    # 거래 단위 조정
                    trade_price = "{:0.0{}f}".format(float(result), 0) #정수
                    trade_amt = "{:0.0{}f}".format(order_buy_amt, 4)  #소수점 넷째자리

                    # order
                    message, order_uuid = trade.buy_limit_order(upbit, coin_name, trade_price, trade_amt)
                    if message != "good":
                        utils.log_info("+[{}]buy coin-buy_limit_order error msg:{}".
                                    format(utils.get_time_hhmmss(time.time()), message))
                        order_uuid = ""
                        continue
                    trade_flag = 1
                    trading_msg = "*[{}]buy coin uuid:{} c:{} p:{} a:{} m:{}".format(
                        utils.get_time_hhmmss(time.time()), order_uuid, close,
                        trade_price, trade_amt, message)
                    utils.log_info(trading_msg)
                    time.sleep(process_sleep_time)

            elif stick_size < 0:
                print('======================= 양봉전환 stick_size :: {} ================'.format(stick_size))
                print('====================== 5분봉 수행후의 거래가 있는지 확인 ====================')
                after_5m_latest_order_datetime = trade.get_order_info(upbit, coin_name, 'done')

                if after_5m_latest_order_datetime > now:
                    # 계좌 조회(message, 잔고, 평균구매금액)
                    message, buy_amt, buy_price = trade.get_krw_balance(upbit)
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
                                # 잔고 조회(잔고, 평균매입금액)
                                message, buy_amt, buy_price = trade.get_krw_balance(upbit)
                                if message != "good":
                                    utils.log_info("+[{}]stop loss-get_balances error msg:{}".
                                            format(utils.get_time_hhmmss(time.time()), message))
                                    continue
                                time.sleep(process_sleep_time)

                                if float(buy_amt) > 0:
                                    #현재가 조회
                                    message, result = trade.get_current_price(upbit, coin_name)
                                    if message != "good":
                                        utils.log_info("+[{}]stop loss-get_current_price error msg:{}".
                                                    format(utils.get_time_hhmmss(time.time()), message))
                                        continue
                                    
                                    buy_profit = ((result - buy_price) / buy_price) * 100  # 수익률

                                    if buy_profit >= revenue_rate:  # 0.05 보다 수익률이 크면, 매도 실행
                                        #손실최소화 주문
                                        message, uuid = trade.stop_loss(upbit, coin_name, buy_amt, buy_price, result, max_loss_rate)

                                        if message == "good":
                                            stop_uuid = uuid
                                            utils.log_info(
                                                "*[{}]stop loss id:{} buy_amt:{} buy_price:{} now_price:{} msg:{}".format(
                                                    utils.get_time_hhmmss(time.time()), stop_uuid, buy_amt,
                                                    buy_price, result, message)
                                            )
                                        time.sleep(process_sleep_time)
                    else:
                        tic_count = 0
                        tic_start = 0
                        tic = 0
                    
                # 매도를 안해도 양봉전환 되면 초기화
                tic_count = 0
                tic_start = 0
                tic = 0

            # 5분 데이터 수행 후, global 변수에 대입
            m5_datetime = current_m5_reset_df['timestamp'][0]

    time.sleep(1) #1초후 다시 시도
    # if check_ss in ('59', '00'):
    #     '''
    #     이 시점에 5분봉3틱룰 계산하도록
    #       - 1. 매도만 진행(5분데이터가 같은 경우)
    #       - 2. 5분봉3틱룰 수행
    #     '''
    #     if current_m5_reset_df == m5_df:
    #         '''
    #         1. 수익률 비교 후 매도만 진행
    #           - 01, 02초때 조회한 현 시점의 5분봉데이터와 global 5분봉 데이터비교하여 같으면 5분이 안지났다는 신호로 간주
    #           - 단 매도 조건은 구매이력이 now 값 이후 이력이 있을 시에 수익률 체크 후 매도하도록
    #         '''
    #         pass
    #     else:
    #         '''
    #         2. 5분봉3틱룰 수행
    #         '''
    #         if stick_size > 0:
    #             print('======================= 음봉전환 stick_size :: {} ================'.format(stick_size))
    #             print('=============={} 음봉전환 ================'.format(m1_df['timestamp']))
    #             print('=============={} 이전 5분봉 크기 : {} ============'.format(m1_df['timestamp'], before5_mean_stick_size))
    #             tic_count += 1
                
    #             if abs(stick_size) >= before5_mean_stick_size * 2:
    #                 print('============= 이전 5봉 평균보다 크다 현재 봉 : {}, 이전5봉 : {} ========== '.format(abs(stick_size), abs(before5_mean_stick_size)))

    #                 if tic_count <= 1:
    #                     tic += 1
    #                 tic_start = prev_data_df['close']
                
    #             if tic_count == 2:
    #                 if m5_df['close'] <= tic_start * (1-0.0005):
    #                     tic += 1
                
    #             if tic_count > 0:
    #                 print('======================== 누적 tic_count 가 2초과인 경우의 tic 계산 ====================')
    #                 if m5_df['close'] <= tic_start * (1-0.0005):
    #                     tic += 1
    #                     tic_start = m5_df['close']
                    
    #             if tic >= 3:
    #                 print('==================== 구매 tic : {} ==============='.format(tic))
    #         elif stick_size < 0:
    #             print('======================= 양봉전환 stick_size :: {} ================'.format(stick_size))
    #             # 계좌 조회(message, 잔고, 평균구매금액)
    #             message, buy_amt, buy_price = trade.get_balances(upbit, coin_name)
    #             if message != "good":
    #                 utils.log_info("+[{}]stop loss-get_balances error msg:{}".
    #                             format(utils.get_time_hhmmss(time.time()), message))
    #                 continue
                
    #             # 잔고가 있는 경우
    #             if float(buy_amt) > 0:
    #                 # 현재가 조회(message, result)
    #                 message, result = trade.get_current_price(upbit, coin_name)
    #                 if message != "good":
    #                     utils.log_info("+[{}]stop loss-get_current_price error msg:{}".
    #                                 format(utils.get_time_hhmmss(time.time()), message))
    #                     continue
                    
    #                 # 수익률 : (코인현재가 - 매수평균가) / 매수평균가 * 100
    #                 buy_profit = ((result - buy_price) / buy_price) * 100
    #                 print('============== 수익률 {} ================='.format(buy_profit))

    #                 if tic >= 3:
    #                     if buy_profit >= revenue_rate:
    #                         print('매도')
    #                 else:
    #                     tic_count = 0
    #                     tic_start = 0
    #                     tic = 0
                    
    #             # 매도를 안해도 양봉전환 되면 초기화
    #             tic_count = 0
    #             tic_start = 0
    #             tic = 0

    #         # 5분 데이터 수행 후, global 변수에 대입
    #         m5_df = current_m5_reset_df