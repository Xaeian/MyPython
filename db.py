from abc import ABC, abstractmethod
from numpy import iterable
import psycopg2
import pymysql
from psycopg2._psycopg import connection as PostgresConn
from pymysql import Connection as MysqlConn
from datetime import datetime
import html

class _DatabaseSQL:
  def __init__(self, db:str|None, host:str="localhost", user:str="root", password:str="") -> None:
    self.host = host
    self.user = user
    self.password = password
    self.db = db

  @abstractmethod
  def Conn(self) -> PostgresConn|MysqlConn:
    pass
  
  def getArray(self, sql:str) -> list[tuple]:
    conn = self.Conn()
    cur = conn.cursor()
    cur.execute(sql)
    res = cur.fetchall()
    cur.close()
    conn.close()
    return res
  
  def getDicts(self, sql:str, names:list[str]|None=None) -> list[dict]:
    conn = self.Conn()
    cur = conn.cursor()
    cur.execute(sql)
    array = cur.fetchall()
    dicts = []
    names = [column[0] for column in cur.description] if names == None else names
    for record in array:
      dicts.append(dict(zip(names,record)))
    cur.close()
    conn.close()
    return dicts
  
  def getRow(self, sql:str) -> tuple:
    array = self.getArray(sql)
    return array[0] if array else None
  
  def getDict(self, sql:str) -> dict:
    dicts = self.getDicts(sql)
    return dicts[0] if dicts else None
  
  def getColumn(self, sql:str) -> tuple:
    array = self.getArray(sql)
    if(array):
      column = []
      for row in array:
        column.append(row[0])
      return column
    return None
  
  def getValue(self, sql:str) -> str:
    row = self.getRow(sql)
    if(row):
      return row[0]
    return None
  
  def getAutoincrement(self, table:str) -> int:
    value = self.getValue(f"""SELECT `AUTO_INCREMENT`
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = '{self.db}'
    AND TABLE_NAME = '{table}';""")
    if not value: return 1
    return int(value)
  
  @staticmethod
  def EncodeInsert(value):
    if(value is None):
      return "null"
    elif(isinstance(value, datetime)):
      return "'" + value.strftime("%Y-%m-%d %H:%M:%S") + "'"
    elif(isinstance(value, int) or isinstance(value, float)):
      return str(value)
    else:
      return "'" + html.escape(str(value)) + "'"
  
  def insertArraySQL(self, table:str, array) -> str:
    array = list(array)
    if(not array):
      return ""
    sql = f"INSERT INTO {table} VALUES("
    for row in array:
      for value in row:
        sql += self.EncodeInsert(value) + ","
      sql = sql.rstrip(",") + "),("
    return sql.rstrip("),(") + ");"
  
  def insertArray(self, table:str, array) -> bool:
    return self.Run(self.insertArraySQL(table, array))
  
  def updateRowSQL(self, table:str, id:int, array:dict) -> str:
    sql = f"UPDATE {table} SET "
    for key, value in array.items():
      sql += key + "=" + self.EncodeInsert(value) + ","
    sql = sql.rstrip(",")
    sql += f" WHERE id={id};"
    return sql
  
  def updateRow(self, table:str, id:int, array:dict) -> str:
    return self.Run(self.updateRowSQL(table, id, array))
  
  def dropTable(self, name):
    sql = f"DROP TABLE IF EXISTS {name};"
    self.Run(sql)
    
  def dropTables(self, *names):
    sqls = []
    for name in names:
      sqls.append(f"DROP TABLE IF EXISTS {name};")
    self.Transaction(sqls)

class PostgresDB(_DatabaseSQL):
  def __init__(self, db:str|None, host:str="localhost", user:str="root", password:str="") -> None:
    super().__init__(db, host, user, password)
    self.type = "postgres"
    
  def Conn(self) -> PostgresConn:
    conn = psycopg2.connect(host=self.host, user=self.user, password=self.password, dbname=self.db)
    return conn
    
class MysqlDB(_DatabaseSQL):
  def __init__(self, db:str|None, host:str="localhost", user:str="root", password:str="") -> None:
    super().__init__(db, host, user, password)
    self.type = "mysql"
    
  def Conn(self) -> MysqlConn:
    conn = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.db)
    return conn
  
  def Run(self, sql:str) -> bool:
    ok = False
    try:
      conn = self.Conn()
      cur = conn.cursor()
      cur.execute(sql)
      conn.commit()
      ok = True
    except pymysql.connect.Error as error:
      print("MYSQL Run Error: {}".format(error))
    finally:
      if conn.ping():
        cur.close()
        conn.close()
    return ok
  
  def Transaction(self, sqls:list) -> bool:
    ok = False
    try:
      conn = self.Conn()
      cur = conn.cursor()
      for sql in sqls:
        cur.execute(sql)
      conn.commit()
      ok = True
    except pymysql.connect.Error as error:
      print("MYSQL Transaction Error: {}".format(error))
      conn.rollback()
    finally:
      if conn.ping():
        cur.close()
        conn.close()
    return ok