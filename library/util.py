import re
import time
import socket
import random
import string
import decimal
import hashlib
import requests
import tempfile
import pandas as pd
from datetime import datetime
from io import BytesIO, StringIO
from library.constants import TimeFMT
from library.decorators import retry_default
from library.config.config import load_config
from dateutil.relativedelta import relativedelta


def get_version():
    """
    以当前时间戳字符串，作为数据版本号
    :return:
    """
    return datetime.now().strftime('%Y%m%d %H:%M:%S')


def str_exchange_date(time_data, fmt: str = TimeFMT.FTM_SECOND, exchange_type: int = 1):
    """
    字符串和日期相互转换
    :param time_data:
    :param fmt: 格式
    :param exchange_type: 1: 字符串 to 日期、0: 日期 to 字符串
    :return:
    """
    return datetime.strptime(time_data, fmt) if exchange_type else time_data.strftime(fmt)


def timestamp_exchange_date(time_data, exchange_type: int = 1):
    """
    时间戳和日期互换，单位是毫秒
    :param time_data:
    :param exchange_type: 1: 时间戳 to 日期、0: 日期 to 时间戳
    """
    return datetime.fromtimestamp(time_data / 1000) if exchange_type else int(time_data.timestamp() * 1000)


def str_exchange_timestamp(time_data, fmt: str = TimeFMT.FTM_SECOND, exchange_type: int = 1):
    """
    字符串和时间戳互换，单位毫秒
    :param time_data:
    :param fmt:
    :param exchange_type:
    :return:
    """
    return int(time.mktime(time.strptime(time_data, fmt)) * 1000) if exchange_type \
        else datetime.fromtimestamp(time_data / 1000).strftime(fmt)


def get_specify_time(time_data: str = None, fmt: str = TimeFMT.FTM_SECOND, **time_type):
    """
    字符串时间之间加减
    :param time_data: 时间格式
    :param fmt: 时间格式
    :param time_type: 时间加减 {"days": 1}: 日期加一天
    :return: 特定格式的时间字符串
    """
    time_data = str_exchange_date(time_data, fmt=fmt, exchange_type=1) if time_data else datetime.now()
    time_str = (time_data + relativedelta(**time_type)).strftime(fmt)
    return time_str


def get_specify_timestamp(timestamp, **time_type):
    """
    时间戳之间加减时间
    :param timestamp: 时间戳，单位毫秒
    :param time_type: {'seconds': 1}, seconds、minutes、hours、days、weeks、months、years
    :return: 时间戳，单位毫秒
    """
    time_data = timestamp_exchange_date(timestamp) + relativedelta(**time_type)
    return timestamp_exchange_date(time_data, exchange_type=0)


def random_date(start_date, end_date):
    """
    两个日期之间的随机一天[start_date, end_date)
    :param start_date: 开始时间, datetime
    :param end_date: 结束时间, datetime
    :return: datetime
    """
    start_stamp = timestamp_exchange_date(time_data=start_date, exchange_type=0)
    end_stamp = timestamp_exchange_date(time_data=end_date, exchange_type=0)-1000
    random_stamp = random.randint(start_stamp, end_stamp)
    return timestamp_exchange_date(time_data=random_stamp)


def md5hex(data):
    """
    MD5加密算法，返回32位小写16进制符号
    :param data:
    :return:
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    elif not isinstance(data, str):
        data = str(data).encode("utf-8")
    m = hashlib.md5()
    m.update(data)
    return m.hexdigest()


def format_headers(headers_str):
    """
    str to dict
    :param headers_str: headers的字符串形式
    :return: headers的dict形式
    """
    headers = dict()
    headers_list = headers_str.split('\n')
    for header in headers_list:
        header = header.strip()
        if header == '':
            continue
        header_list = header.split(': ')
        if len(header_list) == 1:
            headers[header_list[0].replace(':', '')] = ''
        elif len(header_list) == 2:
            headers[header_list[0]] = header_list[1]
        else:
            raise Exception('headers 解析出错')
    return headers


def cut(_list: list, num: int):
    """
    把一个list按照指定长度切割
    :param _list:
    :param num:
    :return:
    """
    return [_list[i:i+num] for i in range(0, len(_list), num)]


def random_string(n):
    """
    获取指定长度的字符串(字母和数字)
    :param n:
    :return:
    """
    ran_str = "".join(random.choice(string.printable[0:62]) for _ in range(n))
    return ran_str


def string_to_file(s):
    """
    字符串数据转成文件对象
    :param s:
    :return:
    """
    file_obj = tempfile.NamedTemporaryFile()
    file_obj.write(s.encode())
    file_obj.flush()                    # 确保string立即写入文件
    file_obj.seek(0)                    # 将文件读取指针返回到文件开头位置
    return file_obj


def df_to_buffer(df: pd.DataFrame, text_type: str):
    """
    df数据 转 IO数据
    :param df:
    :param text_type: 目前仅支持csv、xlsx格式
    :return:
    """
    if text_type == 'csv':
        buffer = StringIO()
        df.to_csv(buffer, index=False)
    elif text_type == 'xlsx':
        buffer = BytesIO()
        df.to_excel(buffer, engine='xlsxwriter', index=False)      # xlsxwriter 比 openpyxl快，但是xlsxwriter以后不维护了
    else:
        raise Exception('参数 text_type 不正确')
    return buffer


def get_local_ip():
    """
    获取ip信息
    :return:
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        return {
            "LAN": s.getsockname()[0],                                                  # 内网ip信息
            "WAN": requests.get('https://ifconfig.me/ip', timeout=5).text.strip()       # 外网ip信息
        }
    except:
        return None


@retry_default()
def slack_message(project_name: str, message: str):
    """
    向slack发送信息
    :param project_name: 业务名字
    :param message: 信息内容
    :return:
    """
    try:
        url = ''
        utc_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        text = f'通知 *_* 通知({load_config("environment")}):\n【业务名字】: {project_name}\n【通知时间】: {utc_time}\n【信息内容】: {message}'
        post_data = {'text': text}
        return requests.post(url=url, json=post_data, timeout=5).text
    except Exception as e:
        from library.initializer.log import Log
        Log().get_logger().error(str(e))
        return False


def float_to_str(f: float, prce: int = 38):
    """
    Convert the given float to a string,
    without resorting to scientific notation
    :param f:
    :param prce:
    :return:
    """
    context = decimal.getcontext()
    context.prec = prce
    return format(context.create_decimal(repr(f)), 'f')


def split_int(s: str):
    """
    拆分字符串里的整数
    :param s:
    :return:
    """
    return re.findall('\\d+|[A-Za-z]+', s)
