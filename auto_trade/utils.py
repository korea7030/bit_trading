import sys
import datetime


def get_current_time(mili_time):
    '''
    현재시간
    '''
    mili_time = float(mili_time)
    KST = datetime.timezone(datetime.timedelta(hours=9))
    dt = datetime.datetime.fromtimestamp(mili_time, tz=KST)
    return dt


def get_time_ss(mili_time):
    '''
    타임스템프에서 초 추출
    '''
    mili_time = float(mili_time)
    KST = datetime.timezone(datetime.timedelta(hours=9))
    dt = datetime.datetime.fromtimestamp(mili_time, tz=KST)
    timeline = str(dt.strftime('%S'))
    return timeline


def get_time_hhmmss(mili_time):
    '''
    타임스탬프에서 시간 추출
    '''
    mili_time = float(mili_time)
    KST = datetime.timezone(datetime.timedelta(hours=9))
    dt = datetime.datetime.fromtimestamp(mili_time, tz=KST)
    timeline = str(dt.strftime('%D %H:%M:%S'))
    return timeline


def log_info(message):
    print('{}'.format(message))
