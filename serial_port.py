import serial, time, re
from datetime import datetime

"""
It allows you to communicate with the serial port while viewing it at the same time
https://github.com/Xaeian/
2023-11-07 14:55:00
"""

class Color():
  READ = "\033[39m"
  SEND = "\033[90m"
  CONN = "\033[35;3m"
  INFO = "\033[33;3m"
  DATA = "\033[38;5;216m"
  FLUSH = "\033[100m"
  ADDR = "\033[38;5;115m"
  RESP = "\033[34m"
  TIME = "\033[36m"
  OK = "\033[32m"
  ERR = "\033[31;3m"
  END = "\033[00m"

class SerialPort():
  def __init__(
    self,
    port:str,
    band:int=115200,
    timeout:float=0.2,
    buffer_size:int=8192,
    print_console:bool=True,
    print_file:str="",
    time_disp:bool=True,
    time_utc:bool=False,
    time_format:str="%Y-%m-%d %H:%M:%S.%f",
    address:str|None = None,
    print_limit:int = 256
  ):
    self.serial:serial.Serial|None = None
    self.port:str = port
    self.band:int = band
    self.timeout:float = timeout
    self.buffer_size:int = buffer_size
    self.print_console:str = print_console
    self.print_file:bool = print_file
    self.time_disp:bool = time_disp
    self.time_utc:bool = time_utc
    self.time_format:str = time_format
    self.conected:bool = False
    self.address:str|None = address
    self.print_limit:int = print_limit

  def bytes2string(self, data:bytes, encoding:str="utf-8", exeption:bool=True) -> str:
    try:
      string:str = data.decode(encoding)
      return string.strip()
    except UnicodeDecodeError:
      if exeption:
        self.print_error("Failed conversion bytes to string")
        return None
      cleaned_bytes = bytes(filter(lambda x: x < 128, data))
      string = cleaned_bytes.decode(encoding, errors='ignore')
      return string.strip()

  def print(self, text:str, prefix:str=""):
    if(len(text) > self.print_limit):
      text = text[0:self.print_limit] + f"...{Color.END}"
    if self.time_disp:
      now = datetime.utcnow() if self.time_utc else datetime.now()
      strtime = now.strftime(self.time_format)
      text = f"{Color.TIME}{strtime}{Color.END} " + text
    if prefix:
      text = f"{prefix} {text}"
    if self.address is not None:
      str_address = "0x%0.2X" % self.address
      text = f"{Color.ADDR}{str_address}{Color.END} {text}"      
    if self.print_file:
      with open(self.print_file, 'a') as file:
        print(text, file=file)
    if self.print_console:
      print(text)

  def print_error(self, text:str):
    self.print(f"{Color.ERR}{text}{Color.END}")
    
  def print_ok(self, text:str):
    self.print(f"{Color.OK}{text}{Color.END}")
    
  def print_conv2str(self, resp:bytes, str_color=Color.READ, bytes_color=Color.DATA) -> str|None:
    try:
      text = resp.decode("utf-8")
      if text.rstrip(): self.print(f"{str_color}{text.rstrip()}{Color.END}")
      return text
    except:
      self.print(f"{bytes_color}{resp}{Color.END}")
      return None

  def connect(self) -> bool:
    if self.conected is True: return True
    try:
      self.serial = serial.Serial(self.port, self.band, timeout=self.timeout)
      self.print(f"{Color.CONN}Connect {self.port}{Color.END}")
      self.conected = True
    except serial.SerialException as e:
      self.print(f"{Color.ERR}Serial port {self.port} is used - {e}{Color.END}")
    except Exception as e:
      self.print(f"{Color.ERR}Serial port {self.port} cannot be opened - {e}{Color.END}")
    else:
      return self.conected

  def disconnect(self):
    if self.conected is False: return
    self.print(f"{Color.CONN}Disconnect {self.port}{Color.END}")
    self.serial.close()
    self.conected = False

  def check_address(self, resp:bytes):
    addr = bytes([self.address])
    if resp and resp[0] == addr[0]:
      resp = resp[1:]
      return resp
    else:
      return None

  def read(self, str_color=Color.READ, bytes_color=Color.DATA, print_conv2str=False) -> bytes|None:
    resp = self.serial.read(self.buffer_size)
    if self.address is not None:
      resp = self.check_address(resp)
    if not resp:
      return None
    if print_conv2str: self.print_conv2str(resp, str_color, bytes_color)
    else: self.print(f"{bytes_color}{resp}{Color.END}")
    return resp

  def readline(self, color=Color.READ, conv2str=True) -> str|None:
    resp = self.serial.readline(self.buffer_size)
    if self.address is not None:
      resp = self.check_address(resp)
    if not resp:
      return None
    if conv2str: return self.print_conv2str(resp, color, color)
    else: self.print(f"{color}{resp}{Color.END}")
    return resp
  
  def readlines(self, color=Color.READ, conv2str=True) -> list[str]|None:
    resp = self.serial.read(self.buffer_size)
    if self.address is not None:
      resp = self.check_address(resp)
    if not resp:
      return None
    lines = re.sub(b'[\r\n]+', b'\n', resp).strip(b'\n').split(b'\n')
    resp = []
    for line in lines:
      if conv2str:
        resp.append(self.print_conv2str(line, color, color))
      else:
        self.print(f"{color}{resp}{Color.END}")
        resp.append(line)
    return resp
  
  def clear(self, color=Color.FLUSH):
    while True:
      resp = self.readlines(color)
      if not resp: break
    self.serial.flush()
    
  def flush(self):
    self.serial.flush()
    
  def send(self, message:str|bytes, str_color=Color.SEND, bytes_color=Color.DATA):
    self.clear()
    if type(message) is str:
      self.print(f"{str_color}{message.strip()}{Color.END}")
      data = bytes(message, "utf-8")
    else:
      data = message
      self.print(f"{bytes_color}{data}{Color.END}")
    if self.address is not None:
      data = bytes([self.address]) + data
    self.serial.write(data)

class REC(SerialPort):
  def __init__(
    self,
    port:str,
    band:int=9600,
    timeout:float=0.1,
    buffer_size:int=8192,
    print_console:bool=True,
    print_file:str="rec.ansi",
    time_disp:bool=True,
    time_utc:bool=False,
    time_format:str="%Y-%m-%d %H:%M:%S.%f",
    name:str="",
    color:str=Color.READ,
    err_delay:float = 5
  ):
    self.name:str = name
    self.color:str = color
    self.err_delay:float = err_delay
    self.err_time:float = 0
    self.value:float|None = None
    super().__init__(port, band, timeout, buffer_size,
      print_console, print_file, time_disp, time_utc, time_format)
  
  def print(self, text:str):
    prefix = f"{Color.ADDR}{self.name}{Color.END}"
    super().print(text, prefix)
  
  def scan(self):
    if self.err_time and time.time() > self.err_time:
      self.disconnect()
      self.print_error(f"Serial port {self.port} not responding")
      return
    if not self.connect(): return
    try:
      self.flush(self.color)
      self.err_time = time.time() + self.err_delay
    except: pass

  def read_value(self):
    if self.err_time and time.time() > self.err_time:
      self.disconnect()
      self.print_error(f"Serial port {self.port} not responding")
      self.value = None
      return None
    if not self.connect():
      self.value = None
      return None
    try:
      strvalue = self.readline(self.color)
      self.flush()
      self.value = float(strvalue)
      self.err_time = time.time() + self.err_delay        
    except: pass
    return self.value
