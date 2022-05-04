import time
import os
import sys
import logging
import traceback
import pandas as pd
import numpy
 
from decimal import Decimal
 
# 공통 모듈 Import
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from module import upbit
 
 
# -----------------------------------------------------------------------------
# - Name : start_selltrade
# - Desc : 매도 로직
# - Input
# 1) sell_pcnt : 매도 수익률
# -----------------------------------------------------------------------------
def start_selltrade(sell_pcnt):
    try:
 
        # ----------------------------------------------------------------------
        # 반복 수행
        # ----------------------------------------------------------------------
        while True:
 
            logging.info("*********************************************************")
            logging.info("1. 로그레벨 : " + str(log_level))
            logging.info("2. 매도 수익률 : " + str(sell_pcnt))
            logging.info("*********************************************************")
 
            # ------------------------------------------------------------------
            # 보유 종목조회
            # ------------------------------------------------------------------
            target_items = upbit.get_accounts('Y', 'KRW')
 
            # ------------------------------------------------------------------
            # 보유 종목이 있는 경우에만 수행
            # ------------------------------------------------------------------
            if len(target_items) < 1:
                logging.info('------------------------------------------------------')
                logging.info('-  매도 가능 보유 종목 없음!')
                logging.info('------------------------------------------------------')
                time.sleep(1)
                continue
 
            logging.info(target_items)
 
            # ------------------------------------------------------------------
            # 보유 종목 현재가 조회
            # ------------------------------------------------------------------
            target_items_comma = upbit.chg_account_to_comma(target_items)
            tickers = upbit.get_ticker(target_items_comma)
            logging.info(tickers)
 
            # -----------------------------------------------------------------
            # 보유 종목별 진행
            # -----------------------------------------------------------------
            for target_item in target_items:
                for ticker in tickers:
                    if target_item['market'] == ticker['market']:
 
                        rsi_val = False
                        mfi_val = False
                        ocl_val = False
 
                        # -----------------------------------------------------
                        # 수익률 계산
                        # ((현재가 - 평균매수가) / 평균매수가) * 100
                        # -----------------------------------------------------
                        rev_pcnt = round(((Decimal(str(ticker['trade_price'])) - Decimal(
                            str(target_item['avg_buy_price']))) / Decimal(str(target_item['avg_buy_price']))) * 100, 2)
 
                        logging.info('')
                        logging.info('------------------------------------------------------')
                        logging.info('- 종목:' + str(target_item['market']))
                        logging.info('- 평균매수가:' + str(target_item['avg_buy_price']))
                        logging.info('- 현재가:' + str(ticker['trade_price']))
                        logging.info('- 수익률:' + str(rev_pcnt))
 
                        # -----------------------------------------------------
                        # 현재 수익률이 매도 수익률 이상인 경우에만 진행
                        # -----------------------------------------------------
                        if Decimal(str(rev_pcnt)) < Decimal(str(sell_pcnt)):
                            logging.info('- 현재 수익률이 매도 수익률 보다 낮아 진행하지 않음!!!')
                            logging.info('------------------------------------------------------')
                            continue
 
                        # --------------------------------------------------------------
                        # 종목별 보조지표를 조회
                        # 1. 조회 기준 : 일캔들, 최근 5개 지표 조회
                        # --------------------------------------------------------------
                        indicators_data = upbit.get_indicators(target_item['market'], 'D', 200, 5)
 
                        # --------------------------------------------------------------
                        # 최근 30일 이내에 신규 상장하여 보조 지표를 구하기 어려운 건은 제외
                        # --------------------------------------------------------------
                        if len(indicators_data) < 5:
                            logging.info('- 캔들 데이터 부족으로 매수 대상에서 제외....[' + str(target_item['market']) + ']')
                            continue
 
                        # --------------------------------------------------------------
                        # 매도 로직
                        # 1. RSI : 2일전 > 70초과, 3일전 < 2일전, 1일전 < 2일전, 현재 < 1일전
                        # 2. MFI : 2일전 > 80초과, 3일전 < 2일전, 1일전 < 2일전, 현재 < 1일전
                        # 3. MACD(OCL) : 3일전 > 0, 2일전 > 0, 1일전 > 0, 3일전 < 2일전, 1일전 < 2일전, 현재 < 1일전
                        # --------------------------------------------------------------
 
                        # --------------------------------------------------------------
                        # RSI : 2일전 > 70초과, 3일전 < 2일전, 1일전 < 2일전, 현재 < 1일전
                        # indicators_data[0][0]['RSI'] : 현재
                        # indicators_data[0][1]['RSI'] : 1일전
                        # indicators_data[0][2]['RSI'] : 2일전
                        # indicators_data[0][3]['RSI'] : 3일전
                        # --------------------------------------------------------------
                        if (Decimal(str(indicators_data[0][0]['RSI'])) < Decimal(str(indicators_data[0][1]['RSI']))
                                and Decimal(str(indicators_data[0][1]['RSI'])) < Decimal(str(indicators_data[0][2]['RSI']))
                                and Decimal(str(indicators_data[0][3]['RSI'])) < Decimal(str(indicators_data[0][2]['RSI']))
                                and Decimal(str(indicators_data[0][2]['RSI'])) > Decimal(str(70))):
                            rsi_val = True
 
                        # --------------------------------------------------------------
                        # MFI : 2일전 > 80초과, 3일전 < 2일전, 1일전 < 2일전, 현재 < 1일전
                        # indicators_data[1][0]['MFI'] : 현재
                        # indicators_data[1][1]['MFI'] : 1일전
                        # indicators_data[1][2]['MFI'] : 2일전
                        # indicators_data[1][3]['MFI'] : 3일전
                        # --------------------------------------------------------------
                        if (Decimal(str(indicators_data[1][0]['MFI'])) < Decimal(str(indicators_data[1][1]['MFI']))
                                and Decimal(str(indicators_data[1][1]['MFI'])) < Decimal(str(indicators_data[1][2]['MFI']))
                                and Decimal(str(indicators_data[1][3]['MFI'])) < Decimal(str(indicators_data[1][2]['MFI']))
                                and Decimal(str(indicators_data[1][2]['MFI'])) > Decimal(str(80))):
                            mfi_val = True
 
                        # --------------------------------------------------------------
                        # MACD(OCL) : 3일전 > 0, 2일전 > 0, 1일전 > 0, 3일전 < 2일전, 1일전 < 2일전, 현재 < 1일전
                        # indicators_data[2][0]['OCL'] : 현재
                        # indicators_data[2][1]['OCL'] : 1일전
                        # indicators_data[2][2]['OCL'] : 2일전
                        # indicators_data[2][3]['OCL'] : 3일전
                        # --------------------------------------------------------------
                        if (Decimal(str(indicators_data[2][0]['OCL'])) < Decimal(str(indicators_data[2][1]['OCL']))
                                and Decimal(str(indicators_data[2][1]['OCL'])) < Decimal(str(indicators_data[2][2]['OCL']))
                                and Decimal(str(indicators_data[2][3]['OCL'])) < Decimal(str(indicators_data[2][2]['OCL']))
                                and Decimal(str(indicators_data[2][1]['OCL'])) > Decimal(str(0))
                                and Decimal(str(indicators_data[2][2]['OCL'])) > Decimal(str(0))
                                and Decimal(str(indicators_data[2][3]['OCL'])) > Decimal(str(0))):
                            ocl_val = True
 
                        # --------------------------------------------------------------
                        # 매도 조건 만족
                        # --------------------------------------------------------------
                        if rsi_val and mfi_val and ocl_val:
                            logging.info('- 매도 조건 만족....[' + str(target_item['market']) + ']')
                            logging.info(indicators_data[0])
                            logging.info(indicators_data[1])
                            logging.info(indicators_data[2])
 
                            # ------------------------------------------------------------------
                            # 시장가 매도
                            # 실제 매도 로직은 안전을 위해 주석처리 하였습니다.
                            # 실제 매매를 원하시면 테스트를 충분히 거친 후 주석을 해제하시면 됩니다.
                            # ------------------------------------------------------------------
                            logging.info('- 시장가 매도 시작! [' + str(target_item['market']) + ']')
                            # rtn_sellcoin_mp = upbit.sellcoin_mp(target_item['market'], 'Y')
                            logging.info('- 시장가 매도 종료! [' + str(target_item['market']) + ']')
                            # logging.info(rtn_sellcoin_mp)
                            logging.info('------------------------------------------------------')
 
                        else:
                            logging.info('- 조건에 맞지 않아 매도하지 않음!!!')
                            logging.info(indicators_data[0])
                            logging.info(indicators_data[1])
                            logging.info(indicators_data[2])
                            logging.info('------------------------------------------------------')
 
 
    # ---------------------------------------
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
 
        # ---------------------------------------------------------------------
        # 입력 받을 변수
        #
        # 1. 로그레벨
        #   1) 레벨 값 : D:DEBUG, E:ERROR, 그 외:INFO
        #
        # 2. 매도 수익률
        #   1)
        # ---------------------------------------------------------------------
 
        # 1. 로그레벨
        log_level = input("로그레벨(D:DEBUG, E:ERROR, 그 외:INFO) : ").upper()
        sell_pcnt = input("매도 수익률(ex:1%=1) : ")
 
        upbit.set_loglevel(log_level)
 
        # 매수 로직 시작
        start_selltrade(sell_pcnt)
 
 
    except KeyboardInterrupt:
        logging.error("KeyboardInterrupt Exception 발생!")
        logging.error(traceback.format_exc())
        sys.exit(-100)
 
    except Exception:
        logging.error("Exception 발생!")
        logging.error(traceback.format_exc())
        sys.exit(-200)