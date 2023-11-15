from serial_port import SerialPort
from datetime import datetime

def convert_value(value:str|None):
  if not value or value.lower() == "null": return None
  elif value.lower() == "true": return True
  elif value.lower() == "false": return False
  else:
    try: return int(value)
    except:
      try: return float(value)
      except: return value

class CBash(SerialPort):
  def __init__(
    self,
    port:str,
    band:int=115200,
    timeout:float=0.2,
    buffer_size:int=8192,
    print_console:bool=True,
    print_file:str="cbash.ansi",
    time_disp:bool=True,
    time_utc:bool=False,
    time_format:str="%Y-%m-%d %H:%M:%S.%f",
    address:str|None = None,
    print_limit:int = 96,
    pack_size:int=1024
  ):
    self.pack_size:int = pack_size
    self.files:dict = {}
    super().__init__(port, band, timeout, buffer_size,
      print_console, print_file, time_disp, time_utc, time_format,
      address, print_limit)

  def exec(self, command:str|bytes) -> bytes:
    self.send(command)
    return self.read(print_conv2str=True)

  def load_list(self, command:str|bytes) -> list|None:
    resp = self.exec(command)
    if not resp: return None
    resp = self.bytes2string(resp)
    if not resp: return None
    return resp.split(" ")
  
  def load_dict(self, command:str|bytes) -> dict|None:
    values = self.load_list(command)
    if not values: return None
    resp = {}
    for keyvalue in values:
      if ":" in keyvalue:
        keyvalue:str
        keyvalue = keyvalue.split(":", 2)
        resp[keyvalue[0]] = convert_value(keyvalue[1])
    return resp
  
  def load_map(self, command:str|bytes) -> list|None:
    self.send(command)
    lines = self.readlines()
    if not lines: return None
    del lines[0]
    cmap = dict()
    for line in lines:
      if ":" in line:
        keyvalue = line.strip().split(":")
        cmap[keyvalue[1]] = int(keyvalue[0])
    return cmap

  def ping(self) -> bool:
    resp = self.load_list("PING")
    if not resp: return False
    if len(resp) == 2 and resp[0] == "PING" and resp[1] == "pong": return True
    else: return False

  def uid(self) -> str|None:
    res = self.load_list("UID")
    if not res: return None
    return bytes.fromhex(res[1])

  def file_list(self) -> dict:
    self.files = self.load_map("FILE list")
    return self.files

  def file_size(self, file_name:str):
    if file_name in self.files:
      resp = self.load_list("FILE cache " + str(self.files[file_name]))
      if not resp: return None
      resp = resp[2].split("/")
      return (int(resp[0]), int(resp[1]))

  def file_save(self, file_name:str, data:str|bytes, append=False):
    if file_name in self.files:
      _, size = self.file_size(file_name)
      if len(data) > size:
        self.print_error(f"No space in {file_name} file")
      pack = int((len(data) + (self.pack_size - 1)) / self.pack_size)
      action = "append" if append else "save"
      self.load_list(f"FILE {action} {str(pack)}")
      for i in range(pack):
        start = i * self.pack_size
        stop = (i + 1) * self.pack_size
        if stop > len(data):
          stop = len(data)
        self.exec(data[start:stop])

  def file_load_bytes(self, file_name:str) -> bytes:
    resp = bytes()
    if file_name in self.files:
      size, _ = self.file_size(file_name)
      pack = int((size + (self.pack_size - 1)) / self.pack_size)
      for i in range(pack):
        offset = i * self.pack_size
        resp += self.exec("FILE load " + str(self.pack_size) + " " + str(offset))
    return resp

  def file_load_str(self, file_name:str, exeption=False) -> str|None:
    resp_bytes = self.file_load_bytes(file_name)
    resp = self.bytes2string(resp_bytes, exeption=exeption)
    if not resp: return None
    return resp

  def set_time(self):
    now = datetime.utcnow()
    str_datetime = now.strftime("%Y-%m-%d %H:%M:%S")
    self.load_list("RTC " + str_datetime)
    
  def get_time(self) -> None|datetime:
    resp = self.load_list("RTC")
    if not resp: return None
    return datetime.strptime(resp[1] + " " + resp[2], "%Y-%m-%d %H:%M:%S")

  def reset(self, now:bool=False):
    command = "PWR reset now" if now else "PWR reset"
    self.send(command)
