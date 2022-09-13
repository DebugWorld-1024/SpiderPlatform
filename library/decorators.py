
import time
import functools
from retrying import retry
from functools import wraps
from library.initializer.log import Log


def retry_if_result_false(result):
    """
    重试机制
    Return True if we should retry (in this case when result is False), False otherwise
    :param result: 被装饰的函数return的结果
    :return:
    """
    return result is False


# 利用偏函数，配置默认参数
retry_default = functools.partial(retry, stop_max_attempt_number=3, retry_on_result=retry_if_result_false)


def retry_exception(tries=3, wait_time=0):
    """
    有异常就进行重试
    :param tries: int, 最大重试次数
    :param wait_time: int, 每次重试时间间隔(秒)
    :return: result: 函数运行结果
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            failed_num = 0
            while True:
                try:
                    failed_num += 1
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    time.sleep(wait_time)
                    if failed_num >= tries:
                        raise Exception(e)
        return wrapper
    return decorator


def func_log(only_error=False):
    """
    日志打印 && 函数运行时间统计
    True/data: 打印成功日志。False/Exception: 打印失败日志。 None: 不打印日志
    :param only_error: 只打印失败日志
    :return:
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()

            message = f"success:: {str(func.__name__)}\texecuted_time:: {int((end_time-start_time)*1000)}ms"
            Log().get_logger().info(message)
            return result
        return wrapper
    return decorator

