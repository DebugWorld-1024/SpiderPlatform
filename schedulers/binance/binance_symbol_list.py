
from library.constants import DataBase, TableName
from base_class.base_scheduler import BaseScheduler
from apscheduler.schedulers.background import BlockingScheduler


class BinanceSymbolList(BaseScheduler):

    def __init__(self):
        super().__init__()


def main():
    seeds = list()
    data_list = BinanceSymbolList().mysql_client.read_as_dict(f"""
        SELECT  id, exchange_name
        FROM    {DataBase.SPIDER_PLATFORM}.{TableName.EXCHANGE_INFO}
        WHERE   exchange_name = 'Binance'
        AND     state = 1
    """)

    for item in data_list:
        for symbol_type in [1, 2, 3]:
            seeds.append(
                {
                    'exchange_id': item['id'],
                    # 'exchange_name': item['exchange_name'],
                    'symbol_type': symbol_type
                }
            )
    BinanceSymbolList().execute(seeds=seeds)


if __name__ == '__main__':
    # 手动调度
    # main()

    # 定时调度
    scheduler = BlockingScheduler(timezone='Asia/Shanghai')
    scheduler.add_job(
        func=main,
        # kwargs={'seeds': seeds},
        trigger='cron',
        hour='08',
        minute='00',
        name='BinanceSymbolList'
    )
    scheduler.start()
