
import requests
import pandas as pd
from copy import deepcopy
from datetime import datetime
from base_class.base_spider import BaseSpider, main
from library.initializer.mysql_client import MysqlClient
from library.constants import DataBase, TableName, Position, Interval, DirtySeed
from library.util import str_split_int, get_specify_timestamp, str_exchange_timestamp


class BinanceSymbolKline(BaseSpider):
    mysql_client = MysqlClient()

    def __init__(self):
        """
        配置该任务元数据
        """
        super().__init__(failed_count=10)       # 失败次数>=10, 就丢弃到FAILED队列

    def spider_config(self):
        """
        配置http请求信息
        :return:
        """
        if self.seed['open_timestamp'] > int(datetime.now().timestamp() * 1000):
            # 时间戳大于当前时间的种子按照脏数据处理
            raise DirtySeed(self.seed)

        symbol_type = {
            1: 'https://api.binance.com/api/v3/klines',             # 现货
            2: 'https://fapi.binance.com/fapi/v1/klines',           # U本位永续
            3: 'https://dapi.binance.com/dapi/v1/klines',           # 币本位永续
        }

        # m -> 分钟; h -> 小时; d -> 天; w -> 周; M -> 月
        interval_mapping = {
            "minute": 'm',
            "hour": 'h',
            "day": 'd',
            "week": 'w',
            "month": 'M'
        }
        interval_split = str_split_int(s=self.seed['interval'])
        interval = f'{interval_split[0]}{interval_mapping[interval_split[1]]}'

        if self.seed['symbol_type'] == 3:
            symbol_name = self.seed['symbol_name'] + '_PERP'
        else:
            symbol_name = self.seed['symbol_name']

        params = {
            'symbol': symbol_name.replace('_', '', 1),
            'interval': interval,
            'limit': self.seed['limit']
        }
        if self.seed['position'] == Position.LEFT:
            params['endTime'] = self.seed['open_timestamp']
        elif self.seed['position'] == Position.RIGHT:
            params['startTime'] = self.seed['open_timestamp']

        return {
            'method': 'GET',
            'url': symbol_type[self.seed["symbol_type"]],
            'params': params,
            'headers': None,
            'proxies': None,
            'timeout': 10
        }

    def check_response(self, spider_config):
        """
        请求并校验
        :param spider_config:
        :return:
        """
        response = requests.request(**spider_config)
        assert response.status_code == 200, f'请求异常: {response.text}'
        return response

    def parse(self, response: requests.models.Response):
        """
        解析数据，并判断是否有下一页
        :param response:
        :return:
        """
        next_seed = None
        data_list = list()
        for item in response.json():
            data_list.append(
                {
                    'exchange_id': self.seed['exchange_id'],
                    'symbol_name': self.seed['symbol_name'],
                    'symbol_type': self.seed['symbol_type'],
                    'open_timestamp': item[0],
                    # 'open_str': str_exchange_timestamp(item[0], exchange_type=0),
                    'close_timestamp': item[6],
                    'open': item[1],
                    'high': item[2],
                    'low': item[3],
                    'close': item[4],
                    'base_volume': item[5],
                    'quote_volume': item[7],
                    'version': self.seed.get('version', None)
                }
            )
        if data_list:
            interval_split = str_split_int(s=self.seed['interval'])
            if self.seed['position'] == Position.LEFT:
                open_timestamp = get_specify_timestamp(data_list[0]['open_timestamp'],
                                                       **{f"{interval_split[-1]}s": -int(interval_split[0])})
            else:
                open_timestamp = get_specify_timestamp(data_list[-1]['open_timestamp'],
                                                       **{f"{interval_split[-1]}s": int(interval_split[0])})
            if open_timestamp < int(datetime.now().timestamp() * 1000):
                next_seed = deepcopy(self.seed)
                next_seed.update({'open_timestamp': open_timestamp})
        return next_seed, data_list

    def save_data(self, data_list):
        """
        存入数据
        :param data_list:
        :return:
        """
        table_name = f'{DataBase.SPIDER_PLATFORM}.{TableName.BINANCE_SYMBOL_KLINE_1DAY}'
        self.mysql_client.insert_or_update(table_name=table_name,
                                           df=pd.DataFrame(data_list))
        return True


if __name__ == '__main__':
    # 开启两个进程处理该任务
    main(process_count=2, method=BinanceSymbolKline().execute)

    # # Debug时测试的种子
    # seed = {
    #     'exchange_id': 1,                   # 交易所ID
    #     'symbol_type': 1,                   # 交易对类型
    #     'symbol_name': 'BTC_USDT',          # 交易对
    #     'interval': f'1{Interval.DAY}',     # Kline 间隔
    #     'open_timestamp': 1651334400000,    # 开始时间戳
    #     'position': Position.LEFT,          # 向前还是向后
    #     'limit': 500,                       # 提取k线数量
    #     'version': '2022-05-13 18:00:00'    # 数据版本号
    # }
    # BinanceSymbolKline().execute(seed=seed)
