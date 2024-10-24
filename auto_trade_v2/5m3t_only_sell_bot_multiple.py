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
from module import upbit

global now
now = upbit.get_current_time(time.time())


# -----------------------------------------------------------------------------
# - Name : start_selltrade
# - Desc : 매도 로직
# - Input
# 1) now : 코드실행시간 용(매수일자 비교위해 필요)
# 2) target_item : 매도할 아이템
### nohup이 아닌 crontab으로 돌려도 됨(1분주기로)
# -----------------------------------------------------------------------------
def start_selltrade(now, sell_pcnt, limit_sell_pcnt):
    items = [item['market'] for item in upbit.get_items('KRW', '')]
    tickers = upbit.get_ticker(items)
    sorted_tickers = sorted(tickers, key=lambda d: d['acc_trade_price_24h'], reverse=True)
    for sorted_ticker in sorted_tickers:
        target_items = upbit.get_accounts('Y', 'KRW', sorted_ticker['market'])
        target_items_comma = upbit.chg_account_to_comma(target_items)
        # 미체결 주문 취소
        if target_items_comma != '':
            upbit.cancel_order(target_items_comma, 'SELL')
        else:
            continue

        try:
            tickers = upbit.get_ticker(target_items_comma)

            for target_item in target_items:
                for ticker in tickers:
                    if target_item['market'] == ticker['market']:
                        order_done = upbit.get_order_status(target_item['market'], 'done') + upbit.get_order_status(target_item['market'], 'cancel')
                        order_done_sorted = upbit.orderby_dict(order_done, 'created_at', True)
                        order_done_filtered = upbit.filter_dict(order_done_sorted, 'side', 'bid')

                        # -------------------------------------------------
                        # 매수 직후 나타나는 오류 체크용 마지막 매수 시간 차이 계산
                        # -------------------------------------------------
                        # 마지막 매도 시간
                        last_buy_dt = datetime.strptime(dateutil.parser.parse(order_done_filtered[0]['created_at']).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')

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

                        # # 코드 시작시간보다 크면 매도
                        # if last_buy_dt > now:
                        #     today_order_list = [x for x in order_done_filtered if x['created_at'] >= now]

                        #     # 구매한 가격 누적
                        #     today_cum_price = 0

                        #     for today_order_for in today_order_list:
                        #         today_cum_price += today_order_for['price']
                        if Decimal(str(rev_pcnt)) >= Decimal(str(sell_pcnt)):  # 1%보다 수익률이 크면 매도 실행
                                                                                                                                                                                                                                                                                                                                                          1,1           Top
                        # -------------------------------------------------
                        # 마지막 매도 시간
                        last_buy_dt = datetime.strptime(dateutil.parser.parse(order_done_filtered[0]['created_at']).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')

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

                        # # 코드 시작시간보다 크면 매도
                        # if last_buy_dt > now:
                        #     today_order_list = [x for x in order_done_filtered if x['created_at'] >= now]

                        #     # 구매한 가격 누적
                        #     today_cum_price = 0

                        #     for today_order_for in today_order_list:
                        #         today_cum_price += today_order_for['price']
                        if Decimal(str(rev_pcnt)) >= Decimal(str(sell_pcnt)):  # 1%보다 수익률이 크면 매도 실행
                            # ------------------------------------------------------------------
                            # 시장가 매도(최근 거래내역의 price)
                            # ------------------------------------------------------------------
                            logging.info('시장가 매도 시작! [' + str(target_item['market']) + ']')
                            # rtn_sellcoin_tg = upbit.sellcoin_tg(target_item['market'], today_cum_price)
                            rtn_sellcoin_mp = upbit.sellcoin_mp(target_item['market'], 'N')
                            logging.info('시장가 매도 종료! [' + str(target_item['market']) + ']')
                            logging.info(rtn_sellcoin_mp)
                            logging.info('------------------------------------------------------')
                        elif Decimal(str(rev_pcnt)) <= Decimal(str(limit_sell_pcnt)):
                            rtn_sellcoin_mp = upbit.sellcoin_mp(target_item['market'], 'N')
                        else:
                            # logging.info('- 최근 매수 일자가 코드 실행시간보다 작으므로 매도하지 않음')
                            logging.info('- 수익률이 1% 미만이라 매도하지 않음')
                            logging.info('------------------------------------------------------')
        except Exception:
            raise


if __name__ == '__main__':
    try:
        log_level = sys.argv[1]
        sell_pcnt = sys.argv[2]
        limit_sell_pcnt = sys.argv[3]

        upbit.set_loglevel(log_level)

        logging.info("*********************************************************")
        logging.info("1. 로그레벨 : " + str(log_level))
        logging.info("2. 매도 수익률 : " + str(sell_pcnt))
        logging.info("3. 매도 제한 : " + str(limit_sell_pcnt))
        start_selltrade(now, sell_pcnt, limit_sell_pcnt)
    except KeyboardInterrupt:
        logging.error("KeyboardInterrupt Exception 발생!")
        logging.error(traceback.format_exc())
        sys.exit(-100)

    except Exception:
        logging.error("Exception 발생!")
        logging.error(traceback.format_exc())
        sys.exit(-200)
