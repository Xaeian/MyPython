from stdlib import *
from datetime import datetime
import serial

class cbash:
  def __init__(self, com:str, bps:int=115200, timeout:float=0.2, pack_size:int=128, buffer_size:int=1024):
    self.serial = serial.Serial(com, bps, timeout=timeout)
    self.pack_size = pack_size
    self.buffer_size = buffer_size
    self.files = dict()

  def Read(self) -> str:
    res = self.serial.read(self.buffer_size).decode("utf-8").strip()
    print("-> " + res)
    return res

  def ReadLine(self) -> str:
    res = self.serial.readline(self.buffer_size).decode("utf-8").strip()
    print("-> " + res)
    return res
  
  def ReadBool(self) -> bool:
    res = self.serial.read(self.buffer_size).decode("utf-8").strip().replace("\r\n", "\r\n-> ")
    if(res):
      print("-> " + res)
      return True
    else:
      return False

  def Send(self, msg:str or bytes) -> bool:
    print(msg)
    if type(msg) is str:
      self.serial.write(bytes(msg, 'utf-8'))
    else:
      self.serial.write(msg)
    res = self.serial.read(self.buffer_size).decode("utf-8").strip().replace("\r\n", "\r\n>> ")
    if(res):
      print(">> " + res)
      return True
    else:
      return False

  def SendGetLine(self, msg:str or bytes) -> list:
    print(msg)
    if type(msg) is str:
      self.serial.write(bytes(msg, 'utf-8'))
    else:
      self.serial.write(msg)
    res = self.serial.read(self.buffer_size).decode("utf-8").strip()
    print(">> " + res)
    return res.split(" ")
  
  def SendGetValues(self, msg:str or bytes) -> dict:
    line = self.SendGetLine(msg)
    res = {}
    for kv in line:
      if ":" in kv:
        kv = kv.split(":")
        res[kv[0]] = float(kv[1])
    return res

  def SendGetMap(self, msg:str or bytes) -> list:
    print(msg)
    if type(msg) is str:
      self.serial.write(bytes(msg, 'utf-8'))
    else:
      self.serial.write(msg)
    res = self.serial.read(self.buffer_size).decode("utf-8").strip().replace("\r\n", "\n").split("\n")
    print(">> " + res[0])
    del res[0]
    arr = dict()
    for val in res:
      print(">> " + val)
      val = val.strip().split(":")
      arr[val[1]] = int(val[0])
    return arr

  def SendGetBytes(self, msg:str or bytes) -> bytes:
    print(msg)
    if type(msg) is str:
      self.serial.write(bytes(msg, 'utf-8'))
    else:
      self.serial.write(msg)
    return self.serial.read(self.buffer_size)

  def Ping(self) -> bool: #error
    res = cbash.SendGetLine(self, "PING")
    if len(res)==2 and res[0] == "PING" and res[1] == "pong":
      return False
    else:
      return True

  def Uid(self) -> bool:
    res = cbash.SendGetLine(self, "UID")
    return bytes.fromhex(res[1])

  def FileList(self, show:bool=False) -> dict:
    self.files = cbash.SendGetMap(self, "FILE list")
    if show:
      print(self.files)
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
    
  def End(self):
    print(">>>> OK")
    self.serial.close()

  def Error(self, msg:str):
    msg = (">>>> ERROR " + msg).strip()
    cbash.End(self)
    exit(msg)