
import os
import logging
from logging.handlers import RotatingFileHandler
from library.config.config import log_config as default_log_config


class Log(object):
    """
    Usage:
        >>> from library.initializer.log import Log
        >>> logger = Log().get_logger(log_name='test')
        >>> logger.warning('This is warning')
        >>> logger.info('This is info')
    """
    def __init__(self, log_config: dict = default_log_config):
        # 屏幕输出
        base_config = {
            'format': log_config['format'],
            'level': log_config['level'],
            'datefmt': log_config['datefmt']
        }
        logging.basicConfig(**base_config)

        # # Mac、Linux、Windows都兼容
        # log_dir = os.path.abspath(os.path.join(os.path.realpath(__file__), '../../..', 'log'))
        # if not os.path.exists(log_dir):
        #     os.makedirs(log_dir)
        #
        # # 文件输出
        # file_config = {
        #     'filename': os.path.join(log_dir, log_config['filename']),
        #     'maxBytes': log_config['maxBytes'],
        #     'backupCount': log_config['backupCount'],
        #     'encoding': log_config['encoding']
        # }
        #
        # self.logger_handler = RotatingFileHandler(**file_config)
        # self.logger_handler.setFormatter(fmt=logging.Formatter(log_config['format']))

    @classmethod
    def get_logger(cls, log_name=None):
        """
        Log() 实例化
        :param log_name: 如果是log_name相同，则id(logger)相同。
        :return:
        """
        logger = logging.getLogger(log_name)
        # logger.addHandler(self.logger_handler)
        return logger
