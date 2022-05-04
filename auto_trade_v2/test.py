import time
import os
import sys
import logging
import traceback

import dateutil.parser 
from decimal import Decimal
from datetime import datetime


# 공통 모듈 Import
from module import upbit

global now
now = upbit.get_current_time(time.time())


# -----------------------------------------------------------------------------
# - Name : start_selltrade
# - Desc : 매도 로직
# - Input
# 1) now : 코드실행시간 용(매수일자 비교위해 필요)
# 2) target_item : 매도할 아이템
# -----------------------------------------------------------------------------
def start_selltrade(now, sell_pcnt, sell_price):
    target_items = upbit.get_accounts('Y', 'KRW', 'KRW-BTC')
    target_items_comma = upbit.chg_account_to_comma(target_items)
    # 미체결 주문 취소
    upbit.cancel_order(target_items_comma, 'SELL')

    try:
        while True:
            check_ss = upbit.get_time_ss(time.time())
            if check_ss in ('01', '02'):
                # 1분봉 조회
                tickers = upbit.get_ticker(target_items_comma)

                for target_item in target_items:
                    for ticker in tickers:
                        if target_item['market'] == ticker['market']:
                            order_done = upbit.get_order_status(target_item['market'], 'done') + upbit.get_order_status(target_item['market'], 'cancel')
                            order_done_sorted = upbit.orderby_dict(order_done, 'created_at', True)
                            order_done_filtered = upbit.filter_dict(order_done_sorted, 'side', 'bid')
                            print('============= order_done_filtered : {} =============='.format(order_done_filtered))
                            # -------------------------------------------------
                            # 매수 직후 나타나는 오류 체크용 마지막 매수 시간 차이 계산
                            # -------------------------------------------------
                            # 마지막 매수 시간
                            last_buy_dt = datetime.strptime(dateutil.parser.parse(order_done_filtered[0]['created_at']).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')

                            # 현재 시간 추출
                            current_dt = datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')

                            # 시간 차이 추출
                            diff = current_dt - last_buy_dt

                            # 매수 후 1분간은 진행하지 않음(업비트 오류 방지 용)
                            if diff.seconds < 60:
                                logging.info('- 매수 직후 발생하는 오류를 방지하기 위해 진행하지 않음!!!')
                                logging.info('------------------------------------------------------')
                                continue
                            
                            # -----------------------------------------------------
                            # 수익률 계산
                            # ((현재가 - 평균매수가) / 평균매수가) * 100
                            # -----------------------------------------------------
                            rev_pcnt = round(((Decimal(str(ticker['trade_price'])) - Decimal(str(target_item['avg_buy_price']))) / Decimal(str(target_item['avg_buy_price']))) * 100, 2)

                            logging.info('')
                            logging.info('------------------------------------------------------')
                            logging.info('- 종목:' + str(target_item['market']))
                            logging.info('- 평균매수가:' + str(target_item['avg_buy_price']))
                            logging.info('- 현재가:' + str(ticker['trade_price']))
                            logging.info('- 수익률:' + str(rev_pcnt))

                            candle = upbit.get_candle(target_item['market'], '1', 1)

                            # 코드 시작시간보다 크면 매도
                            if last_buy_dt > now:
                                if Decimal(str(rev_pcnt)) >= Decimal(str(sell_pcnt)):  # 1%보다 수익률이 크면 매도 실행
                                    # ------------------------------------------------------------------
                                    # 시장가 매도
                                    # 실제 매도 로직은 안전을 위해 주석처리 하였습니다.
                                    # 실제 매매를 원하시면 테스트를 충분히 거친 후 주석을 해제하시면 됩니다.
                                    # ------------------------------------------------------------------
                                    logging.info('시장가 매도 시작! [' + str(target_item['market']) + ']')
                                    #rtn_sellcoin_mp = upbit.sellcoin_tg(target_item['market'], sell_price)
                                    logging.info('시장가 매도 종료! [' + str(target_item['market']) + ']')
                                    #logging.info(rtn_sellcoin_mp)
                                    logging.info('------------------------------------------------------')
                            else:
                                logging.info('- 최근 매수 일자가 코드 실행시간보다 작으므로 매도하지 않음')
                                logging.info('------------------------------------------------------')
                            
    except Exception:
        raise


if __name__ == '__main__':
    try:
        log_level = input("로그레벨(D:DEBUG, E:ERROR, 그 외:INFO) : ").upper()
        sell_pcnt = input("매도 수익률(ex:2%=2) : ")
        sell_price = input("매도 가격(ex: 5000) : ")

        upbit.set_loglevel(log_level)
 
        logging.info("*********************************************************")
        logging.info("1. 로그레벨 : " + str(log_level))
        logging.info("2. 매도 수익률 : " + str(sell_pcnt))
        logging.info("3. 매도 가격 : " + str(sell_price))
        start_selltrade(now, sell_pcnt, sell_price)
    except KeyboardInterrupt:
        logging.error("KeyboardInterrupt Exception 발생!")
        logging.error(traceback.format_exc())
        sys.exit(-100)
 
    except Exception:
        logging.error("Exception 발생!")
        logging.error(traceback.format_exc())
        sys.exit(-200)
