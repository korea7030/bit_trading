# -*- coding: utf-8 -*-
import time
import os
import sys
import logging
import traceback

import dateutil.parser
from decimal import Decimal
from datetime import datetime

# 공통 모듈 Import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from module import upbit

global now
now = upbit.get_current_time(time.time())

trade_flag = False  # 매수 flag(매수 시점에 True, 매도하면 False)
CANDLE_MARGIN = 0.0004

# -----------------------------------------------------------------------------
# - Name : start_buytrade
# - Desc : 매수 로직
# - Input
# 1) buy_amt : 매수금액
# -----------------------------------------------------------------------------
def start_buytrade(buy_amt, limit_sell_pcnt):
    try:
        ticker_dict = {}

        while True:
            trade_now = upbit.get_current_time(time.time())
            check_mm = upbit.get_time_mm(time.time())
            check_ss = upbit.get_time_ss(time.time())

            if trade_now.minute % 5 == 0 and trade_now.second < 10:
                logging.info('**************************** trade_now : {} *****************************'.format(trade_now.strftime('%Y-%m-%d %H:%M:%S')))
                items = [item['market'] for item in upbit.get_items('KRW', '')]
                # items = ['KRW-BTC','KRW-ETH', 'KRW-BCH', 'KRW-BSV', 'KRW-SOL', 'KRW-ETC', 'KRW-BTG']
                tickers = upbit.get_ticker(items)
                tickers = sorted(tickers, key=lambda d: d['acc_trade_price_24h'], reverse=True)[:10]

                for ticker in tickers:
                    tic = 0
                    tic_count = 0
                    tic_start = 0

                    upbit.cancel_order(ticker['market'], 'BUY')
                    m5_candle = upbit.get_candle(ticker['market'], '5', 1)
                    before_5_m5_candle = upbit.get_candle(ticker['market'], '5', 5)
                    stick_size = m5_candle[0]['opening_price'] - m5_candle[0]['trade_price']

                    before_5_m5_stick_size_cum = 0
                    for before_5_m5_candle_for in before_5_m5_candle:
                        before_5_m5_stick_size_cum += upbit.get_stick_size(before_5_m5_candle_for['opening_price'], before_5_m5_candle_for['trade_price'])

                    before_5_m5_stick_size = before_5_m5_stick_size_cum / 5
                    logging.info("*********************************************************")
                    logging.info("5분봉 : " + str(m5_candle))
                    logging.info("stick_size : " + str(stick_size))
                    logging.info("*********************************************************")

                    if stick_size > 0:
                        logging.info("*********************************************************")
                        logging.info("**************** ticker : {}, 시간 :  {} 음봉전환 ****************".format(ticker['market'], m5_candle[0]['candle_date_time_kst']))
                        logging.info("*********************************************************")

                        tic_count += 1
                        tic_start = m5_candle[0]['opening_price']

                        try:
                            ticker_dict[ticker['market']]['tic_count'] += tic_count
                            ticker_dict[ticker['market']]['tic_start'] += tic_start
                        except KeyError:
                            ticker_dict[ticker['market']] = {'tic_count': tic_count, 'tic_start': tic_start, 'tic': 0}

                        if abs(stick_size) >= before_5_m5_stick_size:
                            logging.info('이전 5분 5개봉의 크기보다 크다')
                            if ticker_dict[ticker['market']]['tic_count'] <= 1:
                                tic += 1
                                ticker_dict[ticker['market']]['tic'] += tic

                        tic_start = m5_candle[0]['opening_price']
                        ticker_dict[ticker['market']]['tic_start'] = tic_start

                        if ticker_dict[ticker['market']]['tic_count'] == 2:
                            if m5_candle[0]['trade_price'] <= ticker_dict[ticker['market']]['tic_start'] * CANDLE_MARGIN:
                                tic += 1
                                ticker_dict[ticker['market']]['tic'] += tic

                        if ticker_dict[ticker['market']]['tic_count'] > 2:
                            logging.info('***********************ticker {} 누적 tic_count 가 2초과인 경우의 tic 계산 ***********************'.format(ticker['market']))
                            if m5_candle[0]['trade_price'] <= tic_start * CANDLE_MARGIN:
                                tic += 1
                                tic_start = m5_candle[0]['opening_price']
                                ticker_dict[ticker['market']]['tic'] += tic
                                ticker_dict[ticker['market']]['tic_start'] += tic_start

                        if ticker_dict[ticker['market']]['tic'] >= 3:
                            logging.info('*********************** ticker: {},  구매 tic : {} ***********************'.format(ticker['market'], tic))
                            # # ------------------------------------------------------------------
                            # # 기매수 여부 판단
                            # # ------------------------------------------------------------------
                            # accounts = upbit.get_accounts('Y', 'KRW')
                            # account = list(filter(lambda x: x.get('market') == 'KRW-BTC', accounts))

                            # if len(account) > 0:
                            #     logging.info('기 매수 종목으로 매수하지 않음....[' + 'KRW-BTC' + ']')
                            #     continue

                            # ------------------------------------------------------------------
                            # 매수금액 설정
                            # 1. M : 수수료를 제외한 최대 가능 KRW 금액만큼 매수
                            # 2. 금액 : 입력한 금액만큼 매수
                            # ------------------------------------------------------------------
                            available_amt = upbit.get_krwbal()['available_krw']

                            if buy_amt == 'M':
                                buy_amt = available_amt

                            # ------------------------------------------------------------------
                            # 입력 금액이 주문 가능금액보다 작으면 종료
                            # ------------------------------------------------------------------
                            if Decimal(str(available_amt)) < Decimal(str(buy_amt)):
                                logging.info('주문 가능금액[' + str(available_amt) + ']이 입력한 주문금액[' + str(buy_amt) + '] 보다 작습니다.')
                                continue
                            # ------------------------------------------------------------------
                            # 최소 주문 금액(업비트 기준 5000원) 이상일 때만 매수로직 수행
                            # ------------------------------------------------------------------
                            if Decimal(str(buy_amt)) < Decimal(str(upbit.min_order_amt)):
                                logging.info('주문금액[' + str(buy_amt) + ']이 최소 주문금액[' + str(upbit.min_order_amt) + '] 보다 작습니다.')
                                continue

                            # ------------------------------------------------------------------
                            # 시장가 매수
                            # 실제 매수 로직은 안전을 위해 주석처리 하였습니다.
                            # 실제 매매를 원하시면 테스트를 충분히 거친 후 주석을 해제하시면 됩니다.
                            # ------------------------------------------------------------------
                            logging.info('시장가 매수 시작! [' + ticker['market'] + ']')
                            order_list = upbit.get_order_status(ticker['market'], 'done')

                            if len(order_list) > 0:
                                    buy_amt = buy_amt * len(order_list)

                            rtn_buycoin_mp = upbit.buycoin_mp(ticker['market'], buy_amt)
                            logging.info('시장가 매수 종료! [' + ticker['market'] + ']')
                            logging.info(rtn_buycoin_mp)

                            if rtn_buycoin_mp == '':
                                continue

                            tic_count = 0
                            tic_start = 0
                            tic = 0
                            # trade_flag = True  # 매수 시 trade_flag 변경
                            ticker_dict[ticker['market']] = {
                                'tic_count': tic_count,
                                'tic_start': tic_start,
                                'tic': tic,
                                'trade_flag': True
                            }


                            continue
                    elif stick_size == 0:
                            if ticker_dict.get(ticker['market']):
                                if ticker_dict[ticker['market']]['tic_count'] > 0: # 이전 시가 값을 넣음
                                    ticker_dict[ticker['market']]['tic_start'] = m5_candle[0]['opening_price']
                            else:
                                logging.info("************** ticker: {} ***** tic 묶음 ****************".format(ticker['market']))
                                ticker_dict[ticker['market']] = {'tic_start': 0,
                                                                 'tic_count': 0, 
                                                                 'tic': 0, 'trade_flag': False}
                    else:
                        logging.info("\n\n*********************************************************")
                        logging.info("**************** ticker: {}, {} 양봉전환 ****************".format(ticker['market'], m5_candle[0]['candle_date_time_kst']))
                        logging.info("*********************************************************")
                        target_items = upbit.get_accounts('Y', 'KRW', ticker['market'])
                        target_items_comma = upbit.chg_account_to_comma(target_items)
                        logging.info("************************ target_items_comma : {} ****************\n\n".format(target_items_comma))
                        # 미체결 주문 취소
                        if target_items_comma != '':
                            upbit.cancel_order(target_items_comma, 'SELL')
                            # tickers = upbit.get_ticker(target_items_comma)

                            for target_item in target_items:
                                if target_item['market'] == ticker['market']:
                                    order_done = upbit.get_order_status(target_item['market'], 'done') + upbit.get_order_status(target_item['market'], 'cancel')
                                    order_done_sorted = upbit.orderby_dict(order_done, 'created_at', True)
                                    order_done_filtered = upbit.filter_dict(order_done_sorted, 'side', 'bid')
                                    # -------------------------------------------------
                                    # 매수 직후 나타나는 오류 체크용 마지막 매수 시간 차이 계산
                                    # -------------------------------------------------
                                    # 마지막 매수 시간
                                    last_buy_dt = datetime.strptime(dateutil.parser.parse(order_done_filtered[0]['created_at']).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')

                                    if last_buy_dt > now:
                                        today_order_list = [x for x in order_done_filtered if x['created_at'] >= datetime.now().strftime('%Y-%m-%d')]

                                        # 현재날짜의 구매시점의 평균매수가 누적
                                        today_cum_trade_price = 0
                                        # 현재날짜에 구매한 가격 누적
                                        today_cum_price = 0
                                        # 오늘 몇번 구매했는지 체크
                                        today_trade_cnt = 0

                                        for today_order_for in today_order_list:
                                            order_uuid = upbit.get_order_uuid(today_order_for['uuid'])
                                            today_cum_trade_price += Decimal(order_uuid['trades'][0]['price']) # 누적 거래단가
                                            today_cum_price += Decimal(order_uuid['price']) # 누적 거래금액
                                            today_trade_cnt += 1 # 누적 거래 count

                                        if today_cum_trade_price > 0:
                                            today_avg_buy_price = today_cum_trade_price / today_trade_cnt
                                            logging.info('-------------------ticker: {}, 오늘 매수한 금액의 평균매수가 : {} ----------------'.format(ticker['market'], today_avg_buy_price))
                                        # -----------------------------------------------------
                                        # 수익률 계산
                                        # ((현재가 - 평균매수가) / 평균매수가) * 100
                                        # -----------------------------------------------------
                                        # 현재가 다시 구하기
                                        current_trade_price = upbit.get_ticker(ticker['market'])
                                        rev_pcnt = round(
                                            (
                                                (Decimal(str(ticker['trade_price'])) - Decimal(str(target_item['avg_buy_price'])))
                                                / Decimal(str(target_item['avg_buy_price']))
                                            ) * 100, 2)
                                        # if today_cum_trade_price > 0:
                                            # today_avg_buy_price = today_cum_trade_price / today_trade_cnt
                                            # rev_pcnt = round(((Decimal(str(ticker['trade_price'])) - today_avg_buy_price) / today_avg_buy_price) * 100, 2)

                                        logging.info('------------------------------------------------------')
                                        logging.info('- 종목:' + str(target_item['market']))
                                        logging.info('- 평균매수가:' + str(target_item['avg_buy_price']))
                                        logging.info('- 현재가:' + str(ticker['trade_price']))
                                        logging.info('- 수익률:' + str(rev_pcnt))

                                        # tic 값으로 비교했다가 매수 후에 tic 값이 0 으로 바뀌기 때문에,
                                        # 매수 시점에 flag로 5분봉3틱룰에 기반하여 매수했다 판단하고 매도하도록 변경
                                        if ticker_dict[ticker['market']]['trade_flag']:
                                            if Decimal(str(rev_pcnt)) >= Decimal(str(2)) or Decimal(str(rev_pcnt)) <= Decimal(str(limit_sell_pcnt)):
                                                # ------------------------------------------------------------------
                                                # 시장가 매도(최근 거래내역의 price)
                                                # ------------------------------------------------------------------
                                                logging.info('ticker: {}, 시장가 매도 시작! [' + str(target_item['market']) + ']'.format(ticker['market']))
                                                logging.info('ticker: {}, 최근 거래내역의 price :: {}'.format(ticker['market'], order_done_filtered[0]['price']))
                                                # rtn_sellcoin_tg = upbit.sellcoin_tg(target_item['market'], order_done_filtered[0]['price'])
                                                # rtn_sellcoin_tg = upbit.sellcoin_tg(target_item['market'], str(today_cum_price))
                                                rtn_sellcoin_mp = upbit.sellcoin_mp(target_item['market'], 'N')
                                                logging.info('ticker: {}, 시장가 매도 종료! [' + str(target_item['market']) + ']'.format(ticker['market']))
                                                logging.info(rtn_sellcoin_mp)
                                                logging.info('------------------------------------------------------')

                                                tic_start = 0
                                                tic_count = 0
                                                tic = 0

                                                # 등록되어 있던 dict값 제거
                                                del ticker_dict[ticker['market']]
                                                continue
                                            else:
                                                logging.info('- 현재 수익률이 ' + str(1) + '% 보다 크지 않아 매도하지 않음')
                                                logging.info('------------------------------------------------------')
                                                ticker_dict[ticker['market']] = {
                                                    'tic_start': 0,
                                                    'tic_count': 0,
                                                    'tic': 0,
                                                    'trade_flag': False
                                                }
                                    else:
                                        logging.info('- 최근 매수 일자가 코드 실행시간보다 작으므로 매도하지 않음')
                                        logging.info('------------------------------------------------------')
                                        tic_count = 0
                                        tic_start = 0
                                        tic = 0

                                        ticker_dict[ticker['market']] = {
                                                    'tic_start': 0,
                                                    'tic_count': 0,
                                                    'tic': 0,
                                                    'trade_flag': False
                                                }

                            # 매도를 안해도 양봉전환시 reset
                            tic_count = 0
                            tic_start = 0
                            tic = 0

                            ticker_dict[ticker['market']] = {
                                                    'tic_start': tic_start,
                                                    'tic_count': tic_count,
                                                    'tic': tic,
                                                    'trade_flag': False
                                                }

                        tic_count = 0
                        tic_start = 0
                        tic = 0

                        ticker_dict[ticker['market']] = {
                                                    'tic_start': tic_start,
                                                    'tic_count': tic_count,
                                                    'tic': tic,
                                                    'trade_flag': False
                                                }
                logging.info('*************** loop 수행 후 ticker 값 : {} ***************'.format(ticker_dict))
                logging.info('*************************************************************************\n\n\n')
            time.sleep(1)
    except Exception:
        raise
# -----------------------------------------------------------------------------
# - Name : main
# - Desc : 메인
# -----------------------------------------------------------------------------
if __name__ == '__main__':

    # noinspection PyBroadException
    try:

        # ---------------------------------------------------------------------
        # 입력 받을 변수
        #
        # 1. 로그레벨
        #   1) 레벨 값 : D:DEBUG, E:ERROR, 그 외:INFO
        #
        # 2. 매수금액
        #   1) M : 수수료를 제외한 최대 가능 금액으로 매수
        #   2) 금액 : 입력한 금액만 매수(수수료 포함)
        #
        # 3. 매수 제외종목
        #   1) 종목코드(콤마구분자) : BTC,ETH
        # ---------------------------------------------------------------------

        # 1. 로그레벨
        # log_level = input("로그레벨(D:DEBUG, E:ERROR, 그 외:INFO) : ").upper()
        # buy_amt = input("매수금액(M:최대, 10000:1만원) : ").upper()
        log_level = sys.argv[1]
        buy_amt = sys.argv[2]
        limit_sell_pcnt = sys.argv[3]

        upbit.set_loglevel(log_level)

        logging.info("*********************************************************")
        logging.info("1. 로그레벨 : " + str(log_level))
        logging.info("2. 매수금액 " +  str(buy_amt))
        logging.info("3. 매도제한 : " +str(limit_sell_pcnt))
        logging.info("*********************************************************")

        # 매수 로직 시작
        start_buytrade(buy_amt, limit_sell_pcnt)

    except KeyboardInterrupt:
        logging.error("KeyboardInterrupt Exception 발생!")
        logging.error(traceback.format_exc())
        sys.exit(-100)

    except Exception:
        logging.error("Exception 발생!")
        logging.error(traceback.format_exc())
        upbit.send_teleram_message(traceback.format_exc()[:100], error_flag=True)
        sys.exit(-200)