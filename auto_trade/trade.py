import sys
import pyupbit

def get_current_price(up, coin_name):
    message = ''
    result = 'none'
    try:
        result = pyupbit.get_current_price(coin_name)
    except:
        message = "{}".format(sys.exc_info())

    try: #error message check
        message = result['error']['message']
    except: #no error message -> normal state
        if message == '':
            message = 'good'

    return message, result


def cancel_all_order(up, coin_name):
    '''
    전체 미체결 주문 취소
    '''
    message = ''
    uuid = 'none'
    result = {'uuid': ''}
    result_list = list()

    try: 
        result_list = up.get_order(coin_name, state="wait")
    except:
        message = "{}".format(sys.exc_info())

    try: #error message check
        message = result_list['error']['message']
    except: #no error message -> normal state
        message = 'good'

    if message == 'good':
        for result in result_list:
            try:  # make order
                result = up.cancel_order(result['uuid'])
            except:
                message = "{}".format(sys.exc_info())
                break

    return message


def get_balances(up, coin_name):
    '''
    코인별 잔고 조회
    '''
    message = ''
    result = 'none'
    trade_coin = 'none'
    buy_amt = 0
    buy_price = 0
    try:
        trade_coin = coin_name.split('-')[1]
        result = up.get_balances()
    except:
        message = "{}".format(sys.exc_info())

    try: #error mess
        # age check
        message = result[0]['error']['message']
    except: #no error message -> normal state
        if message == '':
            message = 'good'

    if message == 'good':
        for temp in result:
            if temp['currency'] == trade_coin:
                buy_amt = temp['balance']
                buy_price = temp['avg_buy_price']

    return message, buy_amt, buy_price


def get_order_status(up, coin_name, uuid):
    '''
    주문 상태 조회
    '''
    message = ''
    state = 'none' #wait:미체결, done:체결
    side = 'none'
    price = 'none'
    amt = 'none'
    result = {'state': 'none', 'side': 'none', 'price': '0', 'volume': '0'}

    try: 
        result = up.get_order(uuid)
    except:
        message = "{}".format(sys.exc_info())

    try: #error message check
        message = result['error']['message']
    except: #no error message -> normal state
        if message == '':
            message = "good"
            state = result['state']
            side = result['side']
            price = result['price']
            amt = result['volume']

    return message, state, price, amt




def buy_limit_order(up, coin_name, price, amt):
    '''
    지정가 매수
    '''
    message = ''
    uuid = 'none'
    result = {'uuid': ''}

    try:
        result = up.buy_limit_order(coin_name, price, amt)
    except:
        message = '{}'.format(sys.exc_info())
    
    try: #error message check
        message = result['error']['message']
    except: #no error message -> normal state
        if message == '':
            message = 'good'
            uuid = result['uuid']

    return message, uuid


def sell_limit_order(up, coin_name, price, amt):
    '''
    지정가 매도
    '''
    message = ''
    uuid = 'none'
    result = {'uuid': ''}

    try: 
        result = up.sell_limit_order(coin_name, price, amt)
    except:
        message = "{}".format(sys.exc_info())


    try: #error message check
        message = result['error']['message']
    except: #no error message -> normal state
        if message == '':
            message = 'good'
            uuid = result['uuid']

    return message, uuid


def buy_market_order(up, coin_name, price):
    '''
    시장가 매수
    '''
    message = ''
    uuid = 'none'
    result = {'uuid': ''}

    try: 
        result = up.buy_market_order(coin_name, price)
    except:
        message = "{}".format(sys.exc_info())

    try: #error message check
        message = result['error']['message']
    except: #no error message -> normal state
        if message == '':
            message = 'good'
            uuid = result['uuid']

    return message, uuid


def sell_market_order(up, coin_name, amt):
    '''
    시장가 매도
    '''
    message = ''
    uuid = 'none'
    result = {'uuid': ''}

    try: 
        result = up.sell_maket_order(coin_name, amt)
    except:
        message = "{}".format(sys.exc_info())

    try: #error message check
        message = result['error']['message']
    except: #no error message -> normal state
        if message == '':
            message = 'good'
            uuid = result['uuid']

    return message, uuid


def cancel_all_order(up, coin_name):
    '''
    전체 미체결 주문 취소
    '''
    message = ''
    uuid = 'none'
    result = {'uuid': ''}
    result_list = list()

    try: 
        result_list = up.get_order(coin_name, state="wait")
    except:
        message = "{}".format(sys.exc_info())

    try: #error message check
        message = result_list['error']['message']
    except: #no error message -> normal state
        message = 'good'

    if message == 'good':
        for result in result_list:
            try:  # make order
                result = up.cancel_order(result['uuid'])
            except:
                message = "{}".format(sys.exc_info())
                break

    return message