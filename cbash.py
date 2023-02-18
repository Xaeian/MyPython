import serial
from datetime import datetime
from colorama import Fore, Style
import serial.tools.list_ports

def serial_list():
  ports = serial.tools.list_ports.comports()
  devs = []
  for port in ports:
    devs.append(port.device)
  return devs

class cbash:
  
  colorRead = "\033[39m"
  colorRequest = "\033[90m"
  colorResponse = "\033[97m"
  
  def Preview(self, text:str|bytes, color:str):
    text = str(text)
    if self.colored:
      text = color + text + "\033[00m"
    if self.disp:
      print(text)
    if self.callback:
      self.callback(text)
  
  def ModPreview(self, text:str|bytes, color:str):
    text = str(text)
    if self.colored:
      words = text.split()
      text = "\033[33m" + words.pop(0) + "\033[39m "
      for word in words:
        text += word + " "
      text = text[:-1]
    if self.disp:
      print(text)
    if self.callback:
      self.callback(text)
  
  def __init__(
      self,
      com:str,
      bps:int=115200,
      timeout:float=0.2,
      pack_size:int=128,
      buffer_size:int=1024,
      disp:bool=True,
      callback=None,
      colored:bool=True
    ):
    self.com = com
    self.serial = serial.Serial(com, bps, timeout=timeout)
    self.pack_size = pack_size
    self.buffer_size = buffer_size
    self.disp = disp
    self.callback = callback
    self.colored = colored
    self.files = dict()
    self.Preview(f"Connect {self.com}", "\033[35m")

  def Disconnect(self):
    self.serial.close()
    self.Preview(f"Disconnect {self.com}", "\033[35m")
    self.serial.close()

  def Read(self) -> str:
    res = self.serial.read(self.buffer_size).decode("utf-8").strip()
    self.Preview(res, cbash.colorRead)
    return res

  def ReadLine(self) -> str:
    res = self.serial.readline(self.buffer_size).decode("utf-8").strip()
    self.Preview(res, cbash.colorRead)
    return res
  
  def ReadBool(self) -> bool:
    res = self.serial.read(self.buffer_size).decode("utf-8").strip().replace("\r\n", "\r\n-> ")
    if(res):
      self.Preview(res, cbash.colorRead)
      return True
    else:
      return False

  def Send(self, msg:str|bytes) -> bool:
    self.Preview(msg, cbash.colorRequest)
    if type(msg) is str:
      self.serial.write(bytes(msg, 'utf-8'))
    else:
      self.serial.write(msg)
    res = self.serial.read(self.buffer_size).decode("utf-8").strip().replace("\r\n", "\r\n>> ")
    if(res):
      self.ModPreview(res, cbash.colorResponse)
      return True
    else:
      return False

  def SendGetLine(self, msg:str|bytes) -> list:
    self.Preview(msg, cbash.colorRequest)
    if type(msg) is str:
      self.serial.write(bytes(msg, 'utf-8'))
    else:
      self.serial.write(msg)
    res = self.serial.read(self.buffer_size).decode("utf-8").strip()
    self.ModPreview(res, cbash.colorResponse)
    return res.split(" ")
  
  def SendGetValues(self, msg:str|bytes) -> dict:
    line = self.SendGetLine(msg)
    res = {}
    for kv in line:
      if ":" in kv:
        kv = kv.split(":")
        res[kv[0]] = float(kv[1])
    return res

  def SendGetMap(self, msg:str|bytes) -> list:
    self.Preview(msg, cbash.colorRequest)
    if type(msg) is str:
      self.serial.write(bytes(msg, 'utf-8'))
    else:
      self.serial.write(msg)
    res = self.serial.read(self.buffer_size).decode("utf-8").strip().replace("\r\n", "\n").split("\n")
    self.ModPreview(res[0], cbash.colorResponse)
    del res[0]
    arr = dict()
    for val in res:
      self.Preview(val, cbash.colorResponse)
      val = val.strip().split(":")
      arr[val[1]] = int(val[0])
    return arr

  def SendGetBytes(self, msg:str|bytes) -> bytes:
    self.Preview(msg, cbash.colorRequest)
    if type(msg) is str:
      self.serial.write(bytes(msg, 'utf-8'))
    else:
      self.serial.write(msg)
    return self.serial.read(self.buffer_size)

  def Ping(self) -> bool:
    res = cbash.SendGetLine(self, "PING")
    if len(res)==2 and res[0] == "PING" and res[1] == "pong":
      return True
    else:
      return False

  def Uid(self) -> bool:
    res = cbash.SendGetLine(self, "UID")
    return bytes.fromhex(res[1])

  def FileList(self) -> dict:
    self.files = cbash.SendGetMap(self, "FILE list")
    return self.files

  def FileSave(self, fileName:str, msg:str or bytes):
    if fileName in self.files:
      tmp = cbash.SendGetLine(self, "FILE cache " + str(self.files[fileName]))
      size = int(tmp[2].split("/")[1])
      if len(msg) > size:
        cbash.Error("file-size")
      pack = int((len(msg) + (self.pack_size - 1)) / self.pack_size)
      cbash.SendGetLine(self, "FILE save " + str(pack))

      for i in range(pack):
        start = i * self.pack_size
        stop = (i + 1) * self.pack_size
        if stop > len(msg):
          stop = len(msg)
        cbash.Send(self, msg[start:stop])

  def FileLoadString(self, fileName:str) -> str:
    return cbash.FileLoadBytes(self, fileName).decode("utf-8")
    
  def FileLoadBytes(self, fileName:str) -> bytes:
    res = bytes()
    if fileName in self.files:
      tmp = cbash.SendGetLine(self, "FILE cache " + str(self.files[fileName]))
      size = int(tmp[2].split("/")[0])
      pack = int((size + (self.pack_size - 1)) / self.pack_size)
      for i in range(pack):
        offset = i * self.pack_size
        res += cbash.SendGetBytes(self, "FILE load " + str(self.pack_size) + " " + str(offset))
    return res

  def SetTime(bash):
    now = datetime.utcnow()
    datetimeString = now.strftime("%Y-%m-%d %H:%M:%S")
    bash.SendGetLine("RTC " + datetimeString)
