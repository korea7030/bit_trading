import sys
import logging
import traceback
import time
 
from module import upbit
from datetime import datetime
from decimal import Decimal
 
# -----------------------------------------------------------------------------
# - Name : start_mon
# - Desc : 모니터링 로직
# - Input
# - Output
# -----------------------------------------------------------------------------
def start_monitoring():
    try:
 
        # 프로그램 시작 메세지 발송
        message = '\n\n[프로그램 시작 안내]'
        message = message + '\n\n잔고 모니터링 프로그램이 시작 되었습니다!'
        message = message + '\n\n- 현재시간:' + str(datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
 
        # 프로그램 시작 메세지 발송
        upbit.send_teleram_message(message)
 
        # ---------------------------------------------------------------------
        # 알림 발송 용 변수
        # ---------------------------------------------------------------------
        sent_list = []
        # ---------------------------------------------------------------------
 
        # 반복 조회
        while True:
 
            # -----------------------------------------------------------------
            # 잔고 계산용 변수
            # -----------------------------------------------------------------
            cur_price_sum = 0  # 현재 가격(전체 합계용)
            avg_buy_price_sum = 0  # 매수 금액(전체 합계용)
            # -----------------------------------------------------------------
 
            # 보유 종목 잔고 조회
            accounts = upbit.get_accounts('Y', 'KRW')
 
            # 보유 종목이 없으면 진행하지 않음
            if len(accounts) <= 0:
                logging.info('보유잔고 없음!')
                time.sleep(1)
                continue
 
            # 보유 종목 현재 가격 조회
            accounts_comma = upbit.chg_account_to_comma(accounts)
            tickers = upbit.get_ticker(accounts_comma)
 
            # 종목별 진행
            for account in accounts:
                for ticker in tickers:
                    if account['market'] == ticker['market']:
 
                        # -------------------------------------------------------------
                        # 개별 변동률 계산
                        # -------------------------------------------------------------
                        chg_rate = round(((Decimal(str(ticker['trade_price'])) - Decimal(str(account['avg_buy_price']))) / Decimal(str(account['avg_buy_price']))) * Decimal(str(100)), 2)
 
                        # 개별 종목 10% 이상 상승 시 메세지 발송(1시간 간격)
                        if Decimal(str(chg_rate)) >= Decimal(str(10)):
                            logging.info("PCNT-UP 조건 만족![" + str(account['market']) + "]")
                            logging.info("변동률:[" + str(chg_rate) + "]")
 
                            # 알림 Key 조립
                            msg_key = {'TYPE': 'PCNT-UP', 'ITEM': account['market']}
 
                            # 메세지 조립
                            message = '\n\n[보유종목 상승안내!]'
                            message = message + '\n\n- 대상종목:' + str(account['market'])
                            message = message + '\n- 현재가:' + str(ticker['trade_price'])
                            message = message + '\n- 변동률:' + str(chg_rate)
 
                            # 메세지 발송(1시간:3600초 간격)
                            sent_list = upbit.send_msg(sent_list, msg_key, message, '3600')
 
                        # 개별 종목 10% 이상 하락 시 메세지 발송(1시간 간격)
                        if Decimal(str(chg_rate)) <= Decimal(str(-10)):
                            logging.info("PCNT-DOWN 조건 만족![" + str(account['market']) + "]")
                            logging.info("변동률:[" + str(chg_rate) + "]")
 
                            # 알림 Key 조립
                            msg_key = {'TYPE': 'PCNT-DOWN', 'ITEM': account['market']}
 
                            # 메세지 조립
                            message = '\n\n[보유종목 하락안내!]'
                            message = message + '\n\n- 대상종목:' + str(account['market'])
                            message = message + '\n- 현재가:' + str(ticker['trade_price'])
                            message = message + '\n- 변동률:' + str(chg_rate)
 
                            # 메세지 발송(1시간:3600초 간격)
                            sent_list = upbit.send_msg(sent_list, msg_key, message, '3600')
 
                        # -------------------------------------------------------------
                        # 전체 수익률 계산
                        # -------------------------------------------------------------
                        # 현재가격 합계(평가금액)
                        cur_price_sum = Decimal(str(cur_price_sum)) + (Decimal(str(ticker['trade_price'])) * Decimal(str(account['balance'])))
 
                        # 매수금액 합계
                        avg_buy_price_sum = Decimal(str(avg_buy_price_sum)) + (Decimal(str(account['avg_buy_price'])) * Decimal(str(account['balance'])))
 
            # 전체 수익률
            overall_amt = cur_price_sum - avg_buy_price_sum
            overall_revenue = round(((cur_price_sum - avg_buy_price_sum) / avg_buy_price_sum) * Decimal(str(100)), 2)
 
            logging.info('')
            logging.info('전체 매수금액:' + '{:0,.0f}'.format(round(avg_buy_price_sum, 0)) + '원')
            logging.info('전체 평가금액:' + '{:0,.0f}'.format(round(cur_price_sum, 0)) + '원')
            logging.info('전체 변동금액:' + '{:0,.0f}'.format(round(overall_amt, 0)) + '원')
            logging.info('전체 수익률:' + str(overall_revenue) + '%')
            logging.info('')
 
            # 전체 자산 5%이상 상승 시 메세지 발송
            if Decimal(str(overall_revenue)) >= Decimal(str(5)):
                logging.info("OVERALL-PCNT-UP 조건 만족!")
 
                # 알림 Key 조립
                msg_key = {'TYPE': 'OVERALL-PCNT-UP', 'ITEM': 'OVERALL'}
 
                # 메세지 조립
                message = '\n\n[전체 자산 상승안내]'
                message = message + '\n\n- 전체 매수금액:' + '{:0,.0f}'.format(round(avg_buy_price_sum, 0)) + '원'
                message = message + '\n- 전체 평가금액:' + '{:0,.0f}'.format(round(cur_price_sum, 0)) + '원'
                message = message + '\n- 전체 변동금액:' + '{:0,.0f}'.format(round(overall_amt, 0)) + '원'
                message = message + '\n- 전체 수익률:' + str(overall_revenue) + '%'
 
                # 메세지 발송(1시간:3600초 간격)
                sent_list = upbit.send_msg(sent_list, msg_key, message, '3600')
 
            # 전체 자산 5%이상 하락 시 메세지 발송
            if Decimal(str(overall_revenue)) <= Decimal(str(-5)):
                logging.info("OVERALL-PCNT-DOWN 조건 만족!")
 
                # 알림 Key 조립
                msg_key = {'TYPE': 'OVERALL-PCNT-DOWN', 'ITEM': 'OVERALL'}
 
                # 메세지 조립
                message = '\n\n[전체 자산하락안내]'
                message = message + '\n\n- 전체 매수금액:' + '{:0,.0f}'.format(round(avg_buy_price_sum, 0)) + '원'
                message = message + '\n- 전체 평가금액:' + '{:0,.0f}'.format(round(cur_price_sum, 0)) + '원'
                message = message + '\n- 전체 변동금액:' + '{:0,.0f}'.format(round(overall_amt, 0)) + '원'
                message = message + '\n- 전체 수익률:' + str(overall_revenue) + '%'
 
                # 메세지 발송(1시간:3600초 간격)
                sent_list = upbit.send_msg(sent_list, msg_key, message, '3600')
 
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception:
        raise
 
 
# -----------------------------------------------------------------------------
# - Name : main
# - Desc : 메인
# -----------------------------------------------------------------------------
if __name__ == '__main__':
 
    # noinspection PyBroadException
    try:
        # 로그레벨 설정(DEBUG)
        upbit.set_loglevel('I')
 
        # 모니터링 프로그램 시작
        start_monitoring()
 
    except KeyboardInterrupt:
        logging.error("KeyboardInterrupt Exception 발생!")
        logging.error(traceback.format_exc())
        sys.exit(-100)
 
    except Exception:
        logging.error("Exception 발생!")
        logging.error(traceback.format_exc())
        sys.exit(-200)