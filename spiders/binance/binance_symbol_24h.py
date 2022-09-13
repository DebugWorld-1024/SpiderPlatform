
import requests
import pandas as pd
from library.constants import DataBase, TableName
from base_class.base_spider import BaseSpider, main
from library.initializer.mysql_client import MysqlClient


class BinanceSymbol24H(BaseSpider):
    mysql_client = MysqlClient()

    def __init__(self):
        """
        配置该任务元数据
        """
        super().__init__()

    def spider_config(self):
        """
        配置请求信息
        :return:
        """
        symbol_name = self.seed["symbol_name"].replace("_", "", 1)
        if self.seed['symbol_type'] == 3 and '_' not in symbol_name:
            symbol_name = symbol_name + '_PERP'
        symbol_type = {
            1: f'https://api.binance.com/api/v3/ticker/24hr?symbol={symbol_name}',        # 现货
            2: f'https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={symbol_name}',      # U本位
            3: f'https://dapi.binance.com/dapi/v1/ticker/24hr?symbol={symbol_name}',      # 币本位
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
        assert response.status_code == 200, f'status_cod异常: {response.status_code}'
        return response

    def parse(self, response: requests.models.Response):
        """
        解析数据，并判断是否有下一页
        :param response:
        :return:
        """
        json_data = response.json()
        if self.seed['symbol_type'] == 3:
            json_data = response.json()[0]

        data_list = [
            {
                'exchange_id': self.seed['exchange_id'],
                'symbol_name': self.seed['symbol_name'],
                'symbol_type': self.seed['symbol_type'],
                'price_change_24h': json_data['priceChange'],
                'base_volume_24h': json_data['volume'],
                'version': self.seed.get('version', None)
            }
        ]
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


if __name__ == '__main__':
    # 开启两个进程处理该任务
    main(process_count=2, method=BinanceSymbol24H().execute)

    # # Debug时测试的种子
    # seed = {
    #     'exchange_id': 1,                   # 交易所ID
    #     'symbol_name': '1INCHUP_USDT',      # 交易对名字
    #     'symbol_type': 1,                   # 交易对类型
    #     'version': '2022-05-12 18:00:00'
    # }
    # BinanceSymbol24H().execute(seed=seed)
