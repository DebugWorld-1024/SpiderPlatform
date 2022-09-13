import json
import time
from library.initializer.log import Log
from library.decorators import retry_default
from library.constants import Position, DirtySeed
from library.initializer.redis_client import RedisClient
from concurrent.futures import ProcessPoolExecutor, wait


class BaseSpider(object):
    # TODO 处理多进程问题
    logger = Log().get_logger()
    redis_client = RedisClient().get_client()

    def __init__(self, spider_name: str = None, failed_count: int = float('inf')):
        self.seed = None
        self.seed_str = None
        self.failed_count = failed_count                                          # 失败的次数
        self.spider_name = spider_name or self.__class__.__name__                 # TODO 命名规范
        self.redis_key_todo = f'{self.spider_name}:TODO'

        # self.logger = Log().get_logger()
        # self.redis_client = RedisClient().get_client()

    def get_seed(self, seed: dict = None, redis_key_todo: str = None, position: str = Position.RIGHT):
        """
        TODO：是否支持批量, redis方向可选
        从redis队列中原子性提取数据, 异常已经捕获
        :param seed: 自定义种子
        :param redis_key_todo: 队列名字
        :param position: 提取方向
        :return:
        """

        redis_key_todo = redis_key_todo or self.redis_key_todo
        redis_key_doing = redis_key_todo.replace('TODO', 'DOING')

        if seed:
            self.seed_str = json.dumps(seed)                                # TODO ensure_ascii=False
            self.redis_client.lpush(redis_key_doing, self.seed_str)
            return seed

        while not seed:
            try:
                if not (seed := self.redis_client.blmove(first_list=redis_key_todo,
                                                         second_list=redis_key_doing,
                                                         timeout=10,
                                                         src=Position.RIGHT,
                                                         dest=Position.LEFT)):
                    # # 在 to do 队列获取不到种子就去doing队列获取
                    # if not (seed := self.redis_client.blmove(first_list=redis_key_doing,
                    #                                          second_list=redis_key_doing,
                    #                                          timeout=1,
                    #                                          src=Position.RIGHT,
                    #                                          dest=Position.LEFT)):
                    self.logger.info(f'{self.spider_name}:: {redis_key_todo}:: seed is null')
            except Exception as e:
                self.logger.exception(f'{self.spider_name}:: {redis_key_todo}:: {str(e)}')
                time.sleep(60)                                      # 限制redis连接频率
                self.redis_client = RedisClient().get_client()      # 重新连接redis
        self.seed_str = seed
        return json.loads(seed)

    @retry_default()
    def set_seed(self, state: bool, redis_key_todo: str = None, position: str = Position.RIGHT):
        """
        处理种子
        :param state: True: 成功、False: 失败、其他: pass
        :param redis_key_todo:
        :param position: redis队列方向
        :return:
        """
        redis_key_todo = redis_key_todo or self.redis_key_todo
        redis_key_doing = redis_key_todo.replace('TODO', 'DOING')
        redis_key_failed = redis_key_todo.replace('TODO', 'FAILED')
        redis_key_finished = redis_key_todo.replace('TODO', 'FINISHED')

        try:
            if state is True:
                # 爬取成功，剔除DOING队列的种子, 用seed_str流转种子，是要保证种子的值是一样的
                with self.redis_client.pipeline(transaction=True) as p:
                    p.lrem(name=redis_key_doing, count=0, value=self.seed_str)
                    p.incr(name=redis_key_finished, amount=1)
                    p.execute()
            elif state is False:
                # 爬取失败的操作是一个事务操作，保证原子性。
                # 1. 失败次数超过上限放回FAILED队列尾部, 否则种子重新塞回TODO队列尾部，
                # 2. DOING队列剔除该种子。
                self.seed['failed_count'] = int(self.seed.get('failed_count', 0)) + 1
                with self.redis_client.pipeline(transaction=True) as p:
                    if self.seed['failed_count'] >= self.failed_count:
                        p.lpush(redis_key_failed, *[json.dumps(self.seed)])
                    else:
                        p.lpush(redis_key_todo, *[json.dumps(self.seed)])
                    p.lrem(name=redis_key_doing, count=0, value=self.seed_str)
                    p.execute()
            else:
                pass
            return True
        except Exception as e:
            self.logger.exception(f'{self.spider_name}:: {str(e)}')
            time.sleep(60)                                              # 限制redis连接频率
            self.redis_client = RedisClient().get_client()              # 重新连接redis
            return False

    def spider_config(self, *args, **kwargs):
        pass

    def check_response(self, *args, **kwargs):
        pass

    def parse(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return: 第一个None: 表示下一页的种子, 第二个None: 爬取的数据
        """
        return None, None

    def save_data(self, *args, **kwargs):
        pass

    def next_seed(self, next_seed):
        """
        下一页的种子
        :param next_seed:
        :return:
        """
        if next_seed:
            self.redis_client.rpush(self.redis_key_todo, *[json.dumps(next_seed)])
        return True

    def next_stream(self, *args, **kwargs):
        """
        向下游队列塞种子
        :return:
        """
        pass

    def execute(self, seed: dict = None):
        while True:
            self.seed = self.get_seed(seed=seed)                                            # 获取种子，内部已经捕获异常了
            try:
                spider_config = self.spider_config()                                        # 配置请求信息
                response = self.check_response(spider_config=spider_config)                 # 发起请求、校验数据
                next_seed, data_list = self.parse(response=response)                        # 解析数据、下一页的种子
                self.save_data(data_list=data_list)                                         # 保存数据
                self.next_seed(next_seed=next_seed)                                         # 处理下一页的种子
                self.next_stream(data_list=data_list)                                       # 处理下游的种子
                self.set_seed(state=True)                                                   # 处理种子
                self.logger.info(f'{self.spider_name}:: {self.seed}\t{len(data_list)}')     # spider_name和seed都要有
            except DirtySeed as e:
                self.logger.info(f'{self.spider_name}:: {self.seed}\t异常种子')
                self.set_seed(state=True)                                                   # 脏数据按照成功处理
            except Exception as e:
                self.logger.exception(f'{self.spider_name}:: {self.seed}\t{str(e)}')
                self.set_seed(state=False)                                                  # 无论成功、失败都需要处理种子
                time.sleep(10)
            seed = None                                                                     # 删除自定义种子


def main(process_count: int, method):
    """

    :param process_count: 进程数
    :param method: 方法
    :return:
    """
    fs = []
    process_count = process_count
    executor = ProcessPoolExecutor(process_count)

    for _ in range(process_count):
        fs.append(executor.submit(method))

    wait(fs)                        # 等待计算结束
    executor.shutdown()             # 销毁进程池
