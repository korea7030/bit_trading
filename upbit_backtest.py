from config.mock_upbit import MockUpbit
from trader.basic_trader import BasicTrader


def check_available_bought_price(
    price, # 매수가격
    low, # 다음시점 저가
    high # 다음시점 고가
):
    assert low <= high
    # 저가보다 매수가격이 큰 경우 거래 가능
    if low < price:
        # 고가 보다 매수 가격이 큰 경우 고가로 거래
        return True, min(high, price)
    
    return False, None


def check_available_sold_price(
    price,  # 매도가격
    low, # 다음시점 저가
    high # 다음시점 고가
):
    assert low <= high
    # 고가 보다 매도가 작은 경우 거래 가능
    if price <= high:
        # 저가 보다 매도 가격이 작은 경우 저가로 거래
        return True, max(price, low)
    return False, None

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

    # 모든 시점에 대해 for-loop을 돕니다.
    for t in range(test_data.shape[0] - 1):
        # TODO 이전봉 데이터는 어떻게 가져올까

        # t 시점의 데이터를 불러옵니다.
        data = test_data.iloc[t: t+1]

        next_data = test_data.iloc[t+1]
        low, high = next_data["low"], next_data["high"]

        # 음봉 전환
        if data['open'] - data['close'] < 0:
            tic_count += 1
            # 이전 다섯봉 평균보다 2,3배 이상 로직 추가
            if data['close'] >= data['before5_mean'] * 2.5:
                tic += 1
            tic_start = data['close'] # 직전 마감가
        
            if tic_count == 2:
                if data['open'] - data['close'] >= data['close'] * 1.5:
                    tic += 1

            # 음봉 전환 후 두번째 틱 계산
            if tic_count > 2:
                if tic_start - data['close'] >= data['close'] * 1.5: # 일정금액 보다 크면 tic count
                    tic += 1
                    tic_start = data['close'] # tic count시의 직전가
            
            if tic == 3:
                # 구매 금액 체크
                available, price = check_available_bought_price(data['close'].iloc[-1], low, high)
                if available:
                    # 구매
                    trader.buy(price)

        elif data['open'] - data['close'] >= 0: # 양봉전환
            available, price = check_available_bought_price(data['close'].iloc[-1], low, high)
            # TODO: 특정 금액보다 양봉이 크게 일어난 경우 구매 로직 추가 필요
            if available:
                trader.sell(price)

                # 구매하면 초기화
                tic_start = 0
                tic_count = 0
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
 