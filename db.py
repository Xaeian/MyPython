from abc import abstractmethod
import psycopg2, pymysql, sqlite3
from psycopg2._psycopg import connection as PostgresConnection, cursor as PostgresCursor
from pymysql import Connection as MysqlConnection
from pymysql.cursors import Cursor as MysqlCursor
from sqlite3 import Connection as SqliteConnection, Cursor as SqliteCursor
from datetime import datetime
from enum import Enum
import html, os
from my import split_sql

class DatabaseType(str, Enum):
  Postgres = "postgres"
  MySQL = "mysql"
  SQLite = "sqlite"

def tuple_to_list(data):
  if isinstance(data, (tuple, list)):
    return [tuple_to_list(item) for item in data]
  else:
    return data

# ----------------------------------------------------------------------------- Abstract

class AbstractDatabase:
  def __init__(self, utc:bool=False):
    self.utc = utc
  
  @abstractmethod
  def conn(self) -> PostgresConnection|MysqlConnection:
    pass
  
  @abstractmethod
  def exec(self, sql:str) -> bool:
    pass
  
  @abstractmethod
  def transaction(self, sql:list[str]|str) -> bool:
    pass
  
  def get_array(self, sql:str) -> list[tuple]:
    conn = self.conn()
    cur = conn.cursor()
    cur.execute(sql)
    res = tuple_to_list(cur.fetchall())
    cur.close()
    conn.close()
    return res
  
  def get_dicts(self, sql:str, names:list[str]|None=None) -> list[dict]:
    conn = self.conn()
    cur = conn.cursor()
    cur.execute(sql)
    array = tuple_to_list(cur.fetchall())
    dicts = []
    names = [column[0] for column in cur.description] if names == None else names
    for record in array:
      dicts.append(dict(zip(names,record)))
    cur.close()
    conn.close()
    return dicts
  
  def get_row(self, sql:str) -> tuple:
    array = self.get_array(sql)
    return array[0] if array else None
  
  def get_dict(self, sql:str) -> dict:
    dicts = self.get_dicts(sql)
    return dicts[0] if dicts else None
  
  def get_column(self, sql:str) -> tuple:
    array = self.get_array(sql)
    if(array):
      column = []
      for row in array:
        column.append(row[0])
      return column
    return None
  
  def get_value(self, sql:str) -> str|None:
    row = self.get_row(sql)
    if(row):
      return row[0]
    return None
  
  @abstractmethod
  def table_exist(self, name:str) -> bool:
    pass
  
  @abstractmethod
  def database_exist(self, name:str|None) -> bool:
    pass
  
  # def getAutoincrement(self, table:str) -> int:
  #   value = self.getValue(f"""SELECT `AUTO_INCREMENT`
  #   FROM INFORMATION_SCHEMA.TABLES
  #   WHERE TABLE_SCHEMA = '{self.db}'
  #   AND TABLE_NAME = '{table}';""")
  #   if not value: return 1
  #   return int(value)
  
  def encode_insert(self, value):
    suffix = " UTC" if self.utc else ""
    if(value is None):
      return "null"
    elif(isinstance(value, datetime)):
      return "'" + value.strftime("%Y-%m-%d %H:%M:%S.%f" + suffix) + "'"
    elif(isinstance(value, int) or isinstance(value, float)):
      return str(value)
    else:
      return "'" + html.escape(str(value)) + "'"
  
  def insert_row_sql(self, table: str, row:list) -> str:
    row = list(row)
    if not row:
      return ""
    sql = f"INSERT INTO {table} VALUES ("
    for value in row:
      sql += self.encode_insert(value) + ","
    return sql.rstrip(",") + ");"
  
  def insert_row(self, table: str, row:list) -> bool:
    return self.exec(self.insert_row_sql(table, row))
  
  def insert_array_sql(self, table:str, array:list[list]) -> str:
    array = list(array)
    if not array:
      return ""
    sql = f"INSERT INTO {table} VALUES("
    for row in array:
      for value in row:
        sql += self.encode_insert(value) + ","
      sql = sql.rstrip(",") + "),("
    return sql.rstrip("),(") + ");"
  
  def insert_array(self, table:str, array:list[list]) -> bool:
    return self.exec(self.insert_array_sql(table, array))
  
  def update_row_sql(self, table:str, id:int, array:dict) -> str:
    sql = f"UPDATE {table} SET "
    for key, value in array.items():
      sql += key + "=" + self.encode_insert(value) + ","
    sql = sql.rstrip(",")
    sql += f" WHERE id={id};"
    return sql
  
  def update_row(self, table:str, id:int, array:dict) -> str:
    return self.exec(self.update_row_sql(table, id, array))
  
  def drop_table(self, name):
    sql = f"DROP TABLE IF EXISTS {name};"
    self.exec(sql)
    
  def drop_tables(self, *names):
    sqls = []
    for name in names:
      sqls.append(f"DROP TABLE IF EXISTS {name};")
    self.transaction(sqls)
  
  def drop_database(self, db_name:str|None=None) -> bool:
    if db_name is None:
      db_name = self.db_name
    if db_name is None: return False
    self.backup = self.db_name
    self.db_name = None
    if not self.database_exist(db_name):
      self.db_name = self.backup
      return False
    sql = f"DROP DATABASE {db_name};"
    self.exec(sql)
    self.db_name = self.backup
    return True
    
  def create_database(self, db_name:str|None=None, set_active:bool = True) -> bool:
    if db_name is None:
      db_name = self.db_name
    if db_name is None: return False
    backup = self.db_name
    self.db_name = None
    if self.database_exist(db_name):
      self.db_name = self.backup
      return False
    sql = f"CREATE DATABASE {db_name}"
    self.exec(sql)
    self.db_name = db_name if set_active else backup
    return True

# ----------------------------------------------------------------------------- Postgres

class PostgresDatabase(AbstractDatabase):
  def __init__(self, db_name:str|None, host:str="localhost", user:str="root", password:str="") -> None:
    self.host:str = host
    self.user:str = user
    self.password:str = password
    self.db_name:str|None = db_name
    self.type:DatabaseType = "postgres"
    super().__init__()
    
  def conn(self) -> PostgresConnection:
    conn = psycopg2.connect(host=self.host, user=self.user, password=self.password, dbname=self.db_name)
    return conn

# ----------------------------------------------------------------------------- MySQL
   
class MysqlDatabase(AbstractDatabase):
  def __init__(self, db_name:str|None, host:str="localhost", user:str="root", password:str="") -> None:
    self.host:str = host
    self.user:str = user
    self.password:str = password
    self.db_name:str|None = db_name
    self.type:DatabaseType = "mysql"
    super().__init__()
    
  def conn(self) -> MysqlConnection:
    conn = pymysql.connect(host=self.host, user=self.user, password=self.password, database=self.db_name)
    return conn
  
  def exec(self, sql:str) -> bool:
    ok = False
    try:
      conn = self.conn()
      cur:MysqlCursor = conn.cursor()
      cur.execute(sql)
      conn.commit()
      ok = True
    except pymysql.connect.Error as error:
      print("MYSQL exec: {}".format(error))
    finally:
      if conn.ping():
        cur.close()
        conn.close()
    return ok
  
  def transaction(self, sqls:list[str]|str) -> bool:
    if type(sqls) is str:
      sqls = split_sql(sqls)
    ok = False
    try:
      conn = self.conn()
      cur:MysqlCursor = conn.cursor()
      for sql in sqls:
        cur.execute(sql)
      conn.commit()
      ok = True
    except pymysql.connect.Error as error:
      print("MYSQL transaction: {}".format(error))
      conn.rollback()
    finally:
      if conn.ping():
        cur.close()
        conn.close()
    return ok
  
  def table_exist(self, name:str) -> bool:
    sql  = f"SELECT 1 FROM information_schema.tables "
    sql += f"WHERE table_name='{name}' AND table_schema='{self.db_name}'"
    if self.get_value(sql): return True
    else: return False
    
  def database_exist(self, db_name:str|None=None) -> bool:
    if db_name is None:
      db_name = self.db_name
    if db_name is None: return False
    dbs = self.get_column("SHOW DATABASES;")
    if db_name in dbs: return True
    else: return False
    
  def create_database_ifnotexist(self, db_name:str|None=None, set_active:bool = True):
    if db_name is None:
      db_name = self.db_name
    if db_name is None: return
    backup = self.db_name
    self.db_name = None
    sql = f"CREATE DATABASE IF NOT EXIST {db_name}"
    self.exec(sql)
    self.db_name = db_name if set_active else backup
    return True

# ----------------------------------------------------------------------------- SQLite

class SqliteDatabase(AbstractDatabase):
  def __init__(self, db_name:str|None) -> None:
    self.db_name:str = db_name
    self.type:DatabaseType = "sqlite"
    super().__init__()

  def conn(self) -> SqliteConnection:
    conn = sqlite3.connect(self.db_name)
    return conn
  
  def exec(self, sql:str) -> bool:
    ok = False
    cur = None
    try:
      conn = self.conn()
      cur:SqliteCursor = conn.cursor()
      cur.execute(sql)
      conn.commit()
      ok = True
    except sqlite3.Error as error:
      print("SQLite exec: {}".format(error))
    finally:
      if cur: cur.close()
      conn.close()
    return ok

  def transaction(self, sqls:list[str]|str) -> bool:
    if type(sqls) is str:
      sqls = split_sql(sqls)
    ok = False
    cur = None
    try:
      conn = self.conn()
      cur:SqliteCursor = conn.cursor()
      for sql in sqls:
        cur.execute(sql)
      conn.commit()
      ok = True
    except sqlite3.Error as error:
      print("SQLite transaction: {}".format(error))
      conn.rollback()
    finally:
      if cur: cur.close()
      conn.close()
    return ok

  def table_exist(self, name:str) -> bool:
    sql = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{name}'"
    if self.get_value(sql): return True
    else: return False
  
  def database_exist(self, db_name:str|None=None) -> bool:
    if db_name is None:
      db_name = self.db_name
    if os.path.isfile(db_name): return True
    else: return False

  def drop_database(self, db_name:str|None=None) -> bool:
    if db_name is None:
      db_name = self.db_name
    if db_name is None: return False
    if not self.database_exist(db_name): return False
    try:
      os.remove(db_name)
      return True
    except OSError as e:
      print(f"SQLite drop_database: {e}")
      return False
    
  def create_database(self, db_name:str|None=None, set_active:bool = True) -> bool:
    if db_name is None:
      db_name = self.db_name
    if db_name is None: return False
    if self.database_exist(db_name): return False
    backup = self.db_name
    self.db_name = db_name
    conn = self.conn()
    conn.close()
    self.db_name = db_name if set_active else backup
    return True

  def create_database_ifnotexist(self, db_name:str|None=None, set_active:bool = True):
    self.create_database(db_name, set_active)

# ----------------------------------------------------------------------------- Any

def Database(type:DatabaseType, db_name:str|None, host:str="localhost", user:str="root", password:str="") -> MysqlConnection|PostgresConnection|SqliteDatabase|None:
  if type == "postgres":
    from db import PostgresDatabase
    return PostgresDatabase(db_name, host, user, password)
  elif type == "mysql":
    from db import MysqlDatabase
    return MysqlDatabase(db_name, host, user, password)
  elif type == "sqlite":
    from db import SqliteDatabase
    return SqliteDatabase(db_name)
  else:
    return None