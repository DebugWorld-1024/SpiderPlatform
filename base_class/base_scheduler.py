import copy
import json
from library.constants import Position
from library.initializer.log import Log
from library.util import get_version, slack_message
from library.initializer.redis_client import RedisClient
from library.initializer.mysql_client import MysqlClient


class BaseScheduler(object):
    # TODO 批量调度、断点续传、监控

    def __init__(self, scheduler_info: dict = None, ):
        self.scheduler_info = {
            'scheduler_name': self.__class__.__name__,                  # 调度名字
            # 'start_num': 0,                                           # 提取开始位置
            'limit_num': 200000,                                        # 一次最大的提取量
            'upper_limit': float('Inf'),                                # 总提取上限
            'seed_slack': True,                                         # 调度是否发送到slack
            'redis_key_todo': f'{self.__class__.__name__}:TODO',        # 队列名称
            'delete_redis': False,                                      # 是否删除队列
            'position': Position.LEFT,                                  # 插入方向
            'sql': None,                                                # sql语句
            'version': None                                             # 数据版本号
        }
        self.scheduler_info.update(scheduler_info or dict())

        self.logger = Log().get_logger()
        self.mysql_client = MysqlClient()
        self.redis_client = RedisClient().get_client()

    def save_seeds(self, seeds: list):
        with self.redis_client.pipeline(transaction=True) as p:
            for seed in copy.deepcopy(seeds):
                seed['version'] = seed.get('version', self.scheduler_info['version'])
                if self.scheduler_info['position'] == Position.LEFT:
                    p.lpush(self.scheduler_info['redis_key_todo'], *[json.dumps(seed)])
                else:
                    p.rpush(self.scheduler_info['redis_key_todo'], *[json.dumps(seed)])
            p.execute()
        return True

    def execute(self, seeds: list = None, version: str = None):
        if not version:
            version = get_version()
        self.scheduler_info['version'] = version

        if seeds:
            self.save_seeds(seeds=seeds)
        else:
            assert self.scheduler_info['sql'], '必须配置sql语句'
            seeds = self.mysql_client.read_as_dict(sql=str(self.scheduler_info['sql']))
            self.save_seeds(seeds=seeds)

        if self.scheduler_info['seed_slack']:
            slack_message(project_name='调度任务',
                          message=f'{self.scheduler_info["scheduler_name"]} 调度完成, 种子数量: {len(seeds)}')
        self.logger.info(f'{self.scheduler_info["redis_key_todo"]} 调度成功')
        return True
