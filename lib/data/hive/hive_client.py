# coding=utf-8
import hive
import gc
import yaml
import logging
import time
import sys
import md5

# python GC内存过程导致大array操作性能极低
# 用gc.disable()去禁止

class HiveClient(object):
    def __init__(self, conf):
        self._logger = logging.getLogger(__name__)
        self.connection = hive.HiveConnection(conf)
        self.statement = self.connection.createStatement()

    def __del__(self):
        self.statement.close()
        self.connection.close()

    def query(self, sql):
        gc.disable()
        result = []
        try:
            self.statement.query(sql)
            start_time = time.time()
            while True:
                # 性能问题，10万行记录10秒
                row = self.statement.next()
                if row is None:
                    break
                result.append(row)
            end_time = time.time()
            size = sys.getsizeof(result)
            self._logger.debug('\033[0;32m[HIVE ITERATE FINISHED: %i ROWS, %i bytes, %i ms]\033[0m', len(result), size, (end_time - start_time) * 1000)
        except Exception as e:
            self._logger.error('Hive error: ', exc_info=True)
        gc.enable()
        return result

    def all(self, sql):
        """执行SQL，获取所有行"""
        return self.query(sql)
