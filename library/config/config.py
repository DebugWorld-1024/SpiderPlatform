
import os
import yaml
import logging


# 一键切换环境。0: 测试环境、1: 正式环境
# ENVIRONMENT = int(os.getenv('ENVIRONMENT', 0))

log_config = {
    # 日志配置
    'format': '%(asctime)s %(levelname)s [%(filename)s %(funcName)s line:%(lineno)d]: %(message)s',
    'level': int(os.getenv('LOG_LEVEL', logging.INFO)),
    'datefmt': None,

    # 文件输出配置
    'filename': 'app.log',
    'maxBytes': 10485760,       # 10M
    'backupCount': 3,           # 3份备份
    'encoding': 'utf-8'
}


# 使用yaml的模式
def load_config(config_name: str, file_path: str = os.getenv('CONFIG_PATH', None)):
    """
    读取yaml里的配置信息
    :param config_name:
    :param file_path:
    :return:
    """
    file_path = file_path or os.path.split(os.path.realpath(__file__))[0] + '/config.yaml'
    with open(f'{file_path}', 'r') as f:
        data = yaml.load(f.read(), Loader=yaml.FullLoader)

    for k in config_name.split('.'):
        data = data[k]

    return data

