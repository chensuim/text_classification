# -*- coding: utf-8 -*-
import sys
import logging
import time
import MySQLdb
from MySQLdb import cursors
from DBUtils.PooledDB import PooledDB
from lib.utils.singleton import *

reload(sys)
sys.setdefaultencoding('utf-8')

logger = logging.getLogger(__name__)


def execute_with_log(self, sql, data=()):
    """
    带日志输出的SQL执行。改造了Cursor类，自动输出日志，方便Debug和查问题。
    """
    start_time = time.time()
    self.execute(sql, data)
    end_time = time.time()
    logger.debug('[SQL %i ms]\n\033[0;32m%s\033[0m', (end_time - start_time) * 1000, self._last_executed)


@singleton
class MySQLClient(object):
    """
    MySQL客户端封装。
    """
    # 高内聚、低耦合。logger应该内敛，不应该传来传去
    def __init__(self, conf):
        # 增加execute_with_log方法，只需执行一次
        cursors.Cursor.execute_with_log = execute_with_log
        self._logger = logging.getLogger(__name__)
        try:
            self._pool = PooledDB(MySQLdb, 5, **conf)
        except Exception as e:
            self._logger.error('Database error: ', exc_info=True)
            exit()

    def _get_connect_from_pool(self):
        return self._pool.connection()

    def execute(self, sql, data):
        """
        执行一条SQL
        Args:
            sql: 数组，元素是SQL字符串
        Returns:
            None
        """
        try:
            conn = self._get_connect_from_pool()
            cursor = conn.cursor()
            #for sql in sqls:
            cursor.execute_with_log(sql, data)
            conn.commit()
        except Exception as e:
            self._logger.error('Database error: ', exc_info=True)
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def executemany(self, sql, datas):
        """
        Args:
            sql: SQL语句
            datas: 数据
        Returns:
            None
        """
        try:
            conn = self._get_connect_from_pool()
            cursor = conn.cursor()
            cursor.executemany(sql, datas)
            conn.commit()
        except Exception as e:
            self._logger.error('Database error: ', exc_info=True)
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def all(self, sql, data=(), show_log=True):
        """
        查询SQL，获取所有指定的列
        Args:
            sql: SQL语句
            data: 数据
        Returns:
            结果集
        """
        try:
            conn = self._get_connect_from_pool()
            cursor = conn.cursor()
            if show_log:
                cursor.execute_with_log(sql, data)
            else:
                cursor.execute(sql, data)
            rows = cursor.fetchall()
            if len(rows) > 0:
                row_size = len(rows[0])
            results = []
            for row in rows:
                if row_size == 1:
                    results.append(row[0])
                else:
                    vals = [e for e in row]
                    results.append(vals)
            return results
        except Exception as e:
            self._logger.error('Database error: ', exc_info=True)
        finally:
            cursor.close()
            conn.close()
        return []


@singleton
class MySQLTestClient(object):
    """
    MySQLTest客户端封装。
    """
    # 高内聚、低耦合。logger应该内敛，不应该传来传去
    def __init__(self, conf):
        # 增加execute_with_log方法，只需执行一次
        cursors.Cursor.execute_with_log = execute_with_log
        self._logger = logging.getLogger(__name__)
        try:
            self._pool = PooledDB(MySQLdb, 5, **conf)
        except Exception as e:
            self._logger.error('Database error: ', exc_info=True)
            exit()

    def _get_connect_from_pool(self):
        return self._pool.connection()

    def executemany(self, sql, datas):
        """
        Args:
            sql: SQL语句
            datas: 数据
        Returns:
            None
        """
        try:
            conn = self._get_connect_from_pool()
            cursor = conn.cursor()
            cursor.executemany(sql, datas)
            conn.commit()
        except Exception as e:
            self._logger.error('Database error: ', exc_info=True)
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
