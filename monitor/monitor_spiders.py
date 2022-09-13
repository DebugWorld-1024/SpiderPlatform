import time
from library.constants import Position
from library.initializer.log import Log
from library.util import slack_message, md5hex
from library.initializer.redis_client import RedisClient


monitor_config = {
    # 爬虫任务监控配置，5: 爬虫速度的阈值，Slack信息接收者
    'BinanceSymbolList': [5, '<@所有者1>'],
    'BinanceSymbol24H': [5, '<@所有者2>'],
    'BinanceSymbolKline': [5, '<@所有者3>'],
}


def main():
    sleep_time = 5
    data_dict = dict()
    while True:
        try:
            redis_client = RedisClient().get_client()
            for k, v in monitor_config.items():
                redis_key_todo = f'{k}:TODO'
                redis_key_doing = f'{k}:DOING'
                redis_key_failed = f'{k}:FAILED'
                redis_key_finished = f'{k}:FINISHED'

                doing_data = redis_client.lrange(name=redis_key_doing, start=0, end=-1)
                md5_data = md5hex(data=doing_data)
                if md5_data == data_dict.get(k, {}).get('md5_data', ''):
                    # for _ in range(len(doing_data)):                        # 防止陷入死循环
                    #     redis_client.blmove(first_list=doing_key,
                    #                         second_list=todo_key,
                    #                         timeout=1,
                    #                         src=Position.RIGHT,
                    #                         dest=Position.LEFT)
                    with redis_client.pipeline(transaction=True) as p:
                        for item in doing_data:
                            p.lpush(redis_key_todo, item)
                            p.lrem(name=redis_key_doing, count=0, value=item)
                        p.execute()

                todo_count = redis_client.llen(name=redis_key_todo) + redis_client.llen(name=redis_key_doing)
                failed_count = redis_client.llen(name=redis_key_failed)
                finished_count = int(redis_client.get(redis_key_finished) or 0)

                if todo_count == 0:
                    # if data_dict.get(k, {}).get('todo_count', 0) != 0:
                    if finished_count != 0:
                        slack_message(project_name='爬取任务', message=f'{k} 爬取任务完成, 失败种子数量:{failed_count} {v[1]}')
                    # 只要待爬取种子数量为0就清除 FINISHED 队列数据
                    redis_client.delete(redis_key_finished)
                else:
                    if data_dict.get(k, {}).get('todo_count', 0) != 0:
                        # 过滤待爬取的种子从0到有的情况之后，再判断爬取速度是否符合阈值
                        if (diff := (finished_count - data_dict.get(k, {}).get('finished_count', 0))) < v[0]:
                            slack_message(project_name='爬取任务',
                                          message=f'{k} 每{sleep_time}min的爬取速度({diff})低于阈值({v[0]}) 剩余种子数量({todo_count})\t{v[1]}')

                data_dict[k] = {
                    'md5_data': md5_data,
                    'todo_count': todo_count,
                    'finished_count': finished_count
                }
            Log().get_logger().info('monitor is running')
        except Exception as e:
            Log().get_logger().exception(str(e))
        finally:
            time.sleep(sleep_time * 60)


if __name__ == '__main__':
    main()
