import sys


#전체 미체결 주문 취소
def cancel_all_order(up, coin_name):
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