
import pandas as pd
from pymysql import cursors, connect
from library.decorators import retry_default
from library.config.config import load_config


class MysqlClient(object):
    """
    Usage:
        >>> from library.initializer.mysql_client import MysqlClient
        >>> mysql_client = MysqlClient()
        >>> mysql_client.read_as_tuple(sql="SELECT VERSION()")
    """

    def __init__(self, mysql_config: dict = load_config('db.mysql_config')):
        self.mysql_config = mysql_config
        self.connection = self._connect_mysql()

    def _connect_mysql(self):
        """
        连接mysql服务端
        :return:
        """
        self.connection = None
        self.connection = connect(**self.mysql_config)
        return self.connection

    @retry_default()
    def check_ping(self):
        """
        检查数据库是否连接，否则重新连接
        :return:
        """
        try:
            self.connection.ping()
            return True
        except:
            self._connect_mysql()
            return False

    # @retry_exception(wait_time=1)
    def read_as_tuple(self, sql, params=None):
        self.check_ping()
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            data = cursor.fetchall()
        return list(data)

    # @retry_exception(wait_time=1)
    def read_as_dict(self, sql, params=None):
        """

        :param sql: 要用 %s 占位符，防止sql注入
        :param params: 元组/列表
        :return:
        """
        self.check_ping()
        with self.connection.cursor(cursor=cursors.DictCursor) as cursor:
            cursor.execute(sql, params)
            data = cursor.fetchall()
        return list(data)

    # @retry_exception(wait_time=1)
    def read_as_df(self, sql, params=None):
        self.check_ping()
        with self.connection.cursor(cursor=cursors.DictCursor) as cursor:
            cursor.execute(sql, params)
            data = cursor.fetchall()
        df = pd.DataFrame(list(data), dtype=object)
        df = df.where(df.notnull(), None)               # 处理Nan
        return df

    # @retry_exception(wait_time=1)
    def write(self, sql, params=None):
        self.check_ping()
        with self.connection.cursor() as cursor:
            row = cursor.execute(sql, params)
            self.connection.commit()
            return row

    # @retry_exception(wait_time=1)
    def write_many(self, sql, params=None):
        self.check_ping()
        with self.connection.cursor() as cursor:
            row = cursor.executemany(sql, params)
            self.connection.commit()
            return row

    def update_many(self, table_name: str, df: pd.DataFrame, where_columns: list):
        """
        批量更新
        :param table_name:
        :param df:
        :param where_columns:
        :return:
        """
        if df.empty:
            return None

        df = df.astype(object)
        df = df.where(df.notnull(), None)                   # 处理Nan
        column_str = ','.join(map(lambda x: f' `{x}`=%s', df.keys()))
        where_column_str = ' AND'.join(map(lambda x: f' `{x}`=%s', where_columns))

        sql = f"""
            UPDATE {table_name}
            SET    {column_str}
            WHERE  {where_column_str}
        """

        for column in where_columns:
            df[f'{table_name.split(".")[-1]}{column}'] = df[column]

        result = self.write_many(sql, df.to_records(index=False).tolist())
        return result

    def insert_or_update(self, table_name: str, df: pd.DataFrame, update_columns: list = None):
        """
        有该条记录就更新，无该条记录就插入
        :param table_name: 表名字
        :param df: 插入的数据
        :param update_columns: 需要更新的字段，默认是全部
        :return: 写入数据是否成功
        """
        if df.empty:
            return None

        df = df.astype(object)
        df = df.where(df.notnull(), None)                               # 处理Nan
        column_str = ','.join([f'`{x}`' for x in list(df.keys())])
        value_str = ','.join(['%s'] * df.shape[1])
        update_columns = update_columns or list(df.keys())
        update_str = ','.join(map(lambda x: f'`{x}`=VALUES(`{x}`)', update_columns))

        sql = f"""INSERT INTO {table_name}
            ({column_str}) VALUES ({value_str})
            ON DUPLICATE KEY UPDATE {update_str}
        """

        result = self.write_many(sql, df.to_records(index=False).tolist())
        return result

    def insert_ignore(self, table_name: str, df: pd.DataFrame):
        """
        批量插入，如果存在就忽略
        :param table_name:
        :param df:
        :return:
        """
        if df.empty:
            return None

        df = df.astype(object)
        df = df.where(df.notnull(), None)                               # 处理Nan
        value_str = ','.join(['%s'] * df.shape[1])
        column_str = ','.join([f'`{x}`' for x in list(df.keys())])

        sql = f"""
            INSERT IGNORE INTO {table_name}
            ({column_str}) VALUES ({value_str})
        """
        result = self.write_many(sql, df.to_records(index=False).tolist())
        return result

    def close_mysql(self):
        """
        断开连接
        :return:
        """
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                return True
            else:
                return self.connection
        except:
            return False

    def __del__(self):
        """
        程序运行结束，关闭连接
        :return:
        """
        self.close_mysql()
