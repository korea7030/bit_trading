class MockUpbit:
    def __init__(
        self,
        seed_money,
        ticker = 'KRT-BTC'
    ):
        self.balances = {
            'KRW': {
                'currency': 'KRW',
                'balance': seed_money,
                'avg_buy_price': 0
            },
            ticker: {
                'currency': ticker,
                'balance': 0,
                'avg_buy_price': 0,
            },
        }

        self.fee = 0.0005  # 수수료
    
    def get_balance(self, ticker):
        '''
        잔고 정보 조회
        '''
        return self.balances[ticker]['balance']
    
    def buy_limit_order(self, ticker, price, volume):
        """
        매수하기
        """
        if volume <= 0:
            return False
        
        total_price = price * volume * (1 + self.fee)

        # 원하는 금액보다 잔고가 많을때 체결
        if self.balances[ticker]['balance'] < total_price:
            return False
        
        # 거래 금액만큼 잔고가 줄어듦
        self.balances['KRW']['balance'] -= total_price

        # 거래한 코인의 평균구매 단가를 계산하고 추가 매수한 만큼 잔고가 증가
        self.balances[ticker]['avg_buy_price'] = (self.balances[ticker]['balance'] * self.balances[ticker]['avg_buy_price']
                                                  + volume * price)
        self.balances[ticker]['balance'] += volume
        self.balances[ticker]['avg_buy_price'] /= self.balances[ticker]['balance']
        return True
    
    def sell_limit_order(self, ticker, price, volume):
        """
        매도하기
        """
        # 수수료 만큼 손해보기 때문에 수수료만큼 부과
        total_price = price * volume * (1 - self.fee)
        
        # 판매하고자 하는 코인의 수량보다 많이 가지고 있을때 매도
        if self.balances[ticker]['balance'] < volume:
            return False
        
        # 거래한만큼 잔고를 변화
        self.balances['KRW']['balance'] += total_price
        self.balances[ticker]['balance'] -= volume
        return True
