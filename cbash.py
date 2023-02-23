import serial
from datetime import datetime
from time import time
from colorama import Fore, Style
import serial.tools.list_ports
from crc import CRC

def serial_list():
  ports = serial.tools.list_ports.comports()
  devs = []
  for port in ports:
    devs.append(port.device)
  return devs

class CBash:
  color = {
    "read": "\033[39m",
    "send": "\033[90m",
    "resp": "\033[97m",
    "head": "\033[33m",
    "value": "\033[34m",
    "time": "\033[36m",
    "conn": "\033[35m",
    "ok": "\033[32m",
    "error": "\033[31m",
    "reset": "\033[00m"
  }
  
  def Preview(self, text:str|bytes, color:str, head:bool=False, values:bool=False):
    if text:
      text = str(text)
      if self.timeDisp:
        now = datetime.utcnow() if self.timeUTC else datetime.now()
        strtime = now.strftime(self.timeFormat)
      if self.colored:
        # TODO: Split \r\n
        if self.timeDisp: strtime = CBash.color["time"] + strtime + " " + color
        words = text.split(" ")
        if head: text = CBash.color["head"] + words.pop(0) + " " + color
        else: text = color
        for word in words:
          if values and ":" in word:
            keyvalue = word.split(":")
            text += keyvalue[0] + ":" + CBash.color["value"] + keyvalue[1] + " " + color
          else: text += word + " "
        text = text.split() + CBash.color["reset"]
      if self.timeDisp: text = strtime + text
      if self.disp: print(text)
      if self.callback: self.callback(text)
  
  def Error(self, text:str):
    text = "ERROR " + text if text else "ERROR"
    self.Preview(text, CBash.color["error"])
    
  def Ok(self, text:str):
    text = "OK " + text if text else "OK"
    self.Preview(text, CBash.color["ok"])
  
  def __init__(
      self,
      port:str,
      bps:int=115200,
      timeout:float=0.2,
      pack_size:int=128,
      buffer_size:int=1024,
      disp:bool=True,
      callback=None,
      colored:bool=True,
      timeDisp:bool=False,
      timeUTC:bool=False,
      timeFormat:str="%Y-%m-%d %H:%M:%S",      
      address:int|None=None, # TODO
      crc:CRC|None=None # TODO
      # TODO: display time with format
    ):
    self.port = port
    self.serial = serial.Serial(port, bps, timeout=timeout)
    self.pack_size = pack_size
    self.buffer_size = buffer_size
    self.disp = disp
    self.callback = callback
    self.colored = colored
    self.timeDisp = timeDisp
    self.timeUTC = timeUTC
    self.timeFormat = timeFormat
    self.files = dict()
    self.Preview(f"Connect {self.port}", CBash.color["conn"])

  def Disconnect(self):
    self.serial.close()
    self.Preview(f"Disconnect {self.port}", CBash.color["conn"])
    self.serial.close()
    
  def Flush(self):
    self.serial.flushInput()
    self.serial.flushOutput()

  def Read(self) -> str:
    res = self.serial.read(self.buffer_size).decode("utf-8").strip()
    self.Preview(res, CBash.color["read"])
    return res

  def ReadLine(self) -> str:
    res = self.serial.readline(self.buffer_size).decode("utf-8").strip()
    self.Preview(res, CBash.color["read"])
    return res
    
  def LoadBytes(self, msg:str|bytes) -> bytes:
    self.Preview(msg, CBash.color["send"])
    msg = bytes(msg, 'utf-8') if type(msg) is str else msg
    self.serial.write(msg)
    return self.serial.read(self.buffer_size)

  def Send(self, send:str|bytes) -> bool:
    res = self.LoadBytes(send).decode("utf-8").strip()
    self.Preview(res, CBash.color["resp"], head=True)
    return True if res else False
  
  def WaitFor(self, send:str|bytes, sec:float, expect:str) -> bool: # error
    self.Send(send)
    timeout = time() + sec
    while not self.ReadLine().startswith(expect):
      if time() > timeout: return True
    return False

  def LoadList(self, send:str|bytes, values:bool=False) -> list:
    res = self.LoadBytes(send).decode("utf-8").strip()
    self.Preview(res, CBash.color["resp"], head=True, values=values)
    return res.split(" ")
  
  def LoadDict(self, send:str|bytes) -> dict:
    values = self.LoadList(send, True)
    res = {}
    for keyvalue in values:
      if ":" in keyvalue:
        keyvalue = keyvalue.split(":")
        res[keyvalue[0]] = float(keyvalue[1])
    return res

  def LoadMap(self, send:str|bytes) -> dict:
    res = self.LoadBytes(send).decode("utf-8").strip().replace("\r\n", "\n").split("\n")
    self.Preview(res[0], CBash.color["resp"], head=True)
    del res[0]
    array = dict()
    for value in res:
      self.Preview(value, CBash.color["resp"], values=True)
      value = value.strip().split(":")
      array[value[1]] = int(value[0])
    return array

  def Ping(self) -> bool: # error
    res = CBash.LoadList(self, "PING")
    return False if len(res) == 2 and res[0] == "PING" and res[1] == "pong" else True

  def Uid(self) -> bool:
    res = CBash.LoadList(self, "UID")
    return bytes.fromhex(res[1])

  def FileList(self) -> dict:
    self.files = CBash.LoadMap(self, "FILE list")
    return self.files

  def FileSave(self, fileName:str, msg:str|bytes):
    if fileName in self.files:
      tmp = CBash.LoadList(self, "FILE cache " + str(self.files[fileName]))
      size = int(tmp[2].split("/")[1])
      if len(msg) > size:
        self.Error("file-size")
      pack = int((len(msg) + (self.pack_size - 1)) / self.pack_size)
      CBash.LoadList(self, "FILE save " + str(pack))
      for i in range(pack):
        start = i * self.pack_size
        stop = (i + 1) * self.pack_size
        if stop > len(msg):
          stop = len(msg)
        CBash.Send(self, msg[start:stop])

  def FileLoadBytes(self, fileName:str) -> bytes:
    res = bytes()
    if fileName in self.files:
      tmp = CBash.LoadList(self, "FILE cache " + str(self.files[fileName]))
      size = int(tmp[2].split("/")[0])
      pack = int((size + (self.pack_size - 1)) / self.pack_size)
      for i in range(pack):
        offset = i * self.pack_size
        res += CBash.LoadBytes(self, "FILE load " + str(self.pack_size) + " " + str(offset))
    return res

  def FileLoadString(self, fileName:str) -> str:
    return CBash.FileLoadBytes(self, fileName).decode("utf-8")

  def SetTime(self):
    now = datetime.utcnow()
    datetimeString = now.strftime("%Y-%m-%d %H:%M:%S")
    self.LoadList("RTC " + datetimeString)
    
  def GetTime(self) -> datetime:
    res = self.LoadList("RTC")
    return datetime.strptime(res[1] + " " + res[2], "%Y-%m-%d %H:%M:%S")

  def Reset(self, now:bool=False):
    text = "PWR reset now" if now else "PWR reset"
    self.Send(text)