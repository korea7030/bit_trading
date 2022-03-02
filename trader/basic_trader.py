import random
import pandas as pd
import pyupbit


class BasicTrader:
    def __init__(
        self,
        upbit,
        ticker
    ):
        self.upbit = upbit
        self.ticker = ticker
    
    @property
    def krw_balance(self):
        return self.upbit.get_balance(ticker='KRW')
    
    @property
    def ticker_balance(self):
        return self.upbit.get_balance(ticker=self.ticker)
    
    def check_market_status_price(self, df):
        """
        랜덤 매매전략(다른사람거 참고용)
        """
        # 랜덤으로 살지 팔지 결정
        status = ['buy', 'sell', 'none']
        status = random.sample(status, 1)[0]
        # 거래금액은 최근의 종가
        price = df['close'].iloc[-1]
        return status, price
    
    def buy(
        self,
        price=None, 
        volume=None,
    ):
        krw_price = 10000
         
        # `price`가 입력되지 않은 경우, 
        # 현재가로 할당
        if price is None:
            price = pyupbit.get_current_price(self.ticker)

        # `volume`이 입력되지 않은 경우, 
        # 10,000원에 해당하는 만큼 할당
        if volume is None:
            volume = krw_price / price
            volume = round(volume, 5)

        krw_price = price * volume
        if self.krw_balance > krw_price:
            self.upbit.buy_limit_order(
                ticker=self.ticker,
                price=price,
                volume=volume,
            )
            print(f"Buy {self.ticker}, KRW: {krw_price}")
    
    def sell(
        self,
        price=None,
        volume=None,
    ):
        # price가 입력되지 않는 경우, 평균 구매 가격의 1%를 더함
        if price is None:
            price = round(self.avg_ticker_price * (1.01))
        
        # volume이 없으면, 전체 보유수량으로 할당
        if volume is None:
            volume = self.ticker_balance
        
        self.upbit.sell_limit_order(
            ticker=self.ticker,
            price=price,
            volume=volume
        )
        
        print(f'Sell {self.ticker}, Ticker: {self.ticker_balance}')
    
    @property
    def avg_ticker_price(self):
        balances = self.upbit.get_balances()
        for balance in balances:
            if self.ticker.split('-')[1] == balance['currency']:
                return float(balance['avg_buy_price'])
        
        return 0.0
