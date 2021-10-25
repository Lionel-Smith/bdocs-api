import os
import cx_Oracle
from config import OracleDB
from src.database.SQLReader import SQLReader

class OracleDBService(SQLReader):
    def __init__(self):
        self.resultSet = []
        self.dsn = cx_Oracle.makedsn(OracleDB.host,OracleDB.port,None,OracleDB.sid)
        self.connection = cx_Oracle.connect(OracleDB.dbaUser,OracleDB.dbaPassword,self.dsn)
        self.cursor = self.connection.cursor()
    
    def getColumnNames(self):
        columnNames = [row[0] for row in self.cursor.description]
        return columnNames
    
    def createRowObject(self,columnNames,row):
        rowObj = {}
        for i in range(len(row)):
            rowObj[columnNames[i]] = row[i]
        return rowObj

    def executeQuery(self,sqlFilePath,params=None):
        self.resultSet = []
        sql = self.getSQL(sqlFilePath)

        if params is None:
            results = self.cursor.execute(sql)
        else:
            results = self.cursor.execute(sql,params)

        columnNames = self.getColumnNames()
        
        while True:
            rows = results.fetchall()
            if not rows:
                break
            for row in rows:
                self.resultSet.append(self.createRowObject(columnNames,row))

    def insertOneRecord(self,sqlFilePath,params):
        sql = self.getSQL(sqlFilePath)
        self.cursor.execute(sql,params)
        self.connection.commit()

    def insertMultipleRecords(self,sqlFilePath,params):
        sql = self.getSQL(sqlFilePath)
        self.cursor.executemany(sql,params)
        self.connection.commit()

    def updateRecord(self,sqlFilePath,params):
        sql = self.getSQL(sqlFilePath)
        self.cursor.execute(sql,params)
        self.connection.commit()

    def disposeDBConnections(self):
        self.connection.close()
        self.cursor.close()