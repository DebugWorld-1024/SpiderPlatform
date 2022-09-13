
import json
import requests
import pandas as pd
from base_class.base_spider import BaseSpider, main
from library.initializer.mysql_client import MysqlClient
from spiders.binance.binance_symbol_24h import BinanceSymbol24H
from library.constants import DataBase, TableName, Interval, Position


class BinanceSymbolList(BaseSpider):
    mysql_client = MysqlClient()

    def __init__(self):
        """
        配置该任务的元数据
        """
        super().__init__()

    def spider_config(self):
        """
        配置http请求信息
        :return:
        """
        symbol_type = {
            1: 'https://api.binance.com/api/v3/exchangeInfo',       # 现货
            2: 'https://fapi.binance.com/fapi/v1/exchangeInfo',     # U本位
            3: 'https://dapi.binance.com/dapi/v1/exchangeInfo',     # 币本位
        }

        url = symbol_type[self.seed["symbol_type"]]
        return {
            'method': 'GET',
            'url': url,
            'params': None,
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
        state = 'status'
        json_data = response.json()
        if self.seed['symbol_type'] == 3:
            state = 'contractStatus'

        data_list = list()
        for item in json_data['symbols']:
            if item.get('contractType', 'PERPETUAL') == 'PERPETUAL':                # 只获取现货、U本位永续合约、币本位永续合约
                data_list.append(
                    {
                        'exchange_id': self.seed['exchange_id'],
                        'symbol_name': f"{item['baseAsset']}_{item['quoteAsset']}",
                        'symbol_type': self.seed['symbol_type'],
                        'state':  1 if item[state] == 'TRADING' else 0,
                        'version': self.seed.get('version', None)
                    }
                )
        return None, data_list

    def save_data(self, data_list):
        """
        存储数据
        :param data_list:
        :return:
        """
        self.mysql_client.insert_or_update(table_name=f'{DataBase.SPIDER_PLATFORM}.{TableName.EXCHANGE_SYMBOL_INFO}',
                                           df=pd.DataFrame(data_list))
        return True

    def next_stream(self, data_list: list):
        """
        生成下游的种子
        :param data_list:
        :return:
        """
        seeds = [json.dumps({
            'exchange_id': x['exchange_id'],                                    # 交易所ID
            'symbol_type': x['symbol_type'],                                    # 交易对类型
            'symbol_name': x['symbol_name'],                                    # 交易对
            'version': x['version']                                             # 数据版本号
        }) for x in data_list if x['state'] == 1]                               # 有效的交易对
        if seeds:
            self.redis_client.lpush(BinanceSymbol24H().redis_key_todo, *seeds)
        return True


if __name__ == '__main__':
    # 开启一个进程处理该任务
    main(process_count=1, method=BinanceSymbolList().execute)

    # Debug时测试的种子
    # seed = {
    #     'exchange_id': 1,               # 交易所ID
    #     'symbol_type': 1,               # 交易对类型
    #     'version': '2022-05-12 18:00:00'
    # }
    # BinanceSymbolList().execute(seed=seed)
