
from base_class.base_scheduler import BaseScheduler
from apscheduler.schedulers.background import BlockingScheduler
from library.constants import DataBase, TableName, Interval, Position


class BinanceSymbolKline(BaseScheduler):

    def __init__(self):
        scheduler_info = {
            'seed_slack': False,
            'sql': f"""
                    SELECT  exchange_id
                            ,symbol_name
                            ,symbol_type
                            ,'1{Interval.DAY}' AS `interval`
                            ,unix_timestamp(now()) * 1000 as open_timestamp
                            ,'{Position.LEFT}' AS `position`
                            ,1500 AS `limit`
                    FROM    {DataBase.SPIDER_PLATFORM}.{TableName.EXCHANGE_SYMBOL_INFO}
                    WHERE   exchange_id in (
                        SELECT  id AS exchange_id
                        FROM    {DataBase.SPIDER_PLATFORM}.{TableName.EXCHANGE_INFO}
                        WHERE   exchange_name = 'Binance'
                    )
                    AND     state = 1
                """
        }
        super().__init__(scheduler_info=scheduler_info)


if __name__ == '__main__':
    # 手动调度
    # BinanceSymbolKline().execute()

    # 定时调度
    scheduler = BlockingScheduler(timezone='Asia/Shanghai')
    scheduler.add_job(
        func=BinanceSymbolKline().execute,
        # kwargs={'seeds': seeds},
        trigger='cron',
        hour='08',
        minute='30',
        name='BinanceSymbolKline'
    )
    scheduler.start()
