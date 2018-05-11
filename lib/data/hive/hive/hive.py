# coding=utf-8
from thrift.transport import TTransport
from thrift.transport import TSocket
from thrift.protocol import TBinaryProtocol

from TCLIService import TCLIService
from TCLIService.ttypes import *
import socket
import logging
import time

class HiveConnection:
    def __init__(self, conf):
        self.transport = TSocket.TSocket(conf['host'], conf['port'])
        protocol = TBinaryProtocol.TBinaryProtocol(self.transport)
        self.client = TCLIService.Client(protocol)
        self.transport.open()

    def close(self):
        self.transport.close()
    
    def createStatement(self):
        return HiveStatement(self.client)
    
class HiveStatement:
    def __init__(self, client):
        self._logger = logging.getLogger(__name__)
        self.client = client
        openSessionResp = client.OpenSession(TOpenSessionReq(configuration={"use:database":"algo"}))
        if openSessionResp.status.statusCode != 0:
            return None
        self.sessionHandle = openSessionResp.sessionHandle

    def close(self):
        if self.operationHandle:
            closeOperationResp = self.client.CloseOperation(TCloseOperationReq(self.operationHandle))
        if self.sessionHandle:
            closeSessionResp = self.client.CloseSession(TCloseSessionReq(self.sessionHandle))

    def query(self, sql):
        start_time = time.time()
        executeStatementResp = self.client.ExecuteStatement(TExecuteStatementReq(self.sessionHandle, sql))
        if executeStatementResp.status.statusCode != 0:
            return None
        self.operationHandle = executeStatementResp.operationHandle
        self.first = True
        self.row = []
        self.index = 0
        end_time = time.time()
        self._logger.debug('[HIVE QUERY %i ms]\n\033[0;32m%s\033[0m', (end_time - start_time) * 1000, sql)

    def _column_value(self, column):
        if column.boolVal is not None:
            return column.boolVal.values
        if column.byteVal is not None:
            return column.byteVal.values
        if column.i16Val is not None:
            return column.i16Val.values
        if column.i32Val is not None:
            return column.i32Val.values
        if column.i64Val is not None:
            return column.i64Val.values
        if column.doubleVal is not None:
            return column.doubleVal.values
        if column.stringVal is not None:
            return column.stringVal.values
        if column.binaryVal is not None:
            return column.binaryVal.values
        return None

    def _build(self, result):
        n = len(self._column_value(result.columns[0]))
        rows = []
        columns = []
        for column in result.columns:
            columns.append(self._column_value(column))
        for i in range(0, n):
            row = []
            for column in columns:
                row.append(column[i])
            rows.append(row)
        return rows

    def next(self):
        if len(self.row) == self.index:
            fetchType = None
            if self.first:
                fetchType = 4
                self.first = False
            else:
                fetchType = 0
            fetchResultsResp = self.client.FetchResults(TFetchResultsReq(self.operationHandle, fetchType, maxRows=1000))
            if fetchResultsResp.status.statusCode != 0:
                return None
            self.row = self._build(fetchResultsResp.results)
            self.index = 0
        if len(self.row) == self.index:
            return None
        else:
            result = self.row[self.index]
            self.index = self.index + 1
            return result
