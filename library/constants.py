# TODO 是否用枚举类型


class Position:
    """redis 查询方向"""
    LEFT = 'LEFT'
    RIGHT = 'RIGHT'


class Method:
    """request的方法"""
    GET = 'GET'
    POST = 'POST'


class TimeFMT:
    """时间格式"""
    TFM_DATE = '%Y-%m-%d'
    TFM_HOUR = '%Y-%m-%d %H'
    TFM_MINUTE = '%Y-%m-%d %H:%M'
    FTM_SECOND = '%Y-%m-%d %H:%M:%S'


class DataBase:
    """数据库"""
    SPIDER_PLATFORM = 'spider_platform'


class TableName:
    """数据表"""
    EXCHANGE_INFO = 'exchange_info'
    EXCHANGE_SYMBOL_INFO = 'exchange_symbol_info'
    BINANCE_SYMBOL_KLINE_1DAY = 'binance_symbol_kline_1day'


class SpiderName:
    pass


class Interval:
    SECOND = 'second'
    MINUTE = 'minute'
    HOUR = 'hour'
    DAY = 'day'
    WEEK = 'week'
    MONTH = 'month'
    YEAR = 'year'


class DirtySeed(Exception):
    """
    处理脏种子的自定义异常
    """
    pass
