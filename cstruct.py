from struct import pack, unpack_from
from enum import Enum
from typing import Callable
from numbers import Real
from crc import CRC, crc32

"""
It allows you to transfer data between embedded devices and Python
without the need to encode data in the C language
https://github.com/Xaeian/
2023-10-14 22:40:00
"""

class Type(Enum):
  uint8 = "B"
  int8 = "b"
  uint16 = "H"
  int16 = "h"
  uint32 = "I"
  int32 = "i"
  uint64 = "Q"
  int64 = "q"
  float = "f"
  double = "d"
  # 8-bit array without preamble, where \0 char is treated as the end of the message
  string = "str"
  # 8-bit array with the length specified in the uint16_t preamble
  bytes = "byte"

def type_size(ctype:Type):
  if ctype.name == "uint8" or ctype.name == "int8": return 1
  if ctype.name == "uint16" or ctype.name == "int16": return 2
  if ctype.name == "uint32" or ctype.name == "uint32" or ctype.name == "float": return 4
  if ctype.name == "uint64" or ctype.name == "uint64" or ctype.name == "double": return 8
  return 0
      
class Endian(Enum):
  little = "<"
  big = "<"
  middle = "=2x"

class Field():
  id = 0
  def __init__(
    self,
    ctype:Type,
    name:str = "",
    unit:str = "",
    length:int = 1, # for array
    scale:float = 1,
    offset:float = 0,
    encode:Callable[[Real], Real] = None,
    decode:Callable[[Real], Real] = None,
    round_point:int = 3
  ) -> None:
    self.type:Type = ctype
    if not name:
      name = "_field_" + Field.id
      Field.id += 1
    self.name:str = name
    self.unit:str = unit
    self.length:int = length
    self.scale:float = scale
    self.offset:float = offset
    self.encode:Callable[[Real], Real] = encode # TODO
    self.decode:Callable[[Real], Real] = decode # TODO
    self.round:int = round_point
    
  def __str__(self):
    return f"Field {self.name}[{self.unit}]"

class Struct():
  id = 0
  codes = {}
  def __init__(self, code:int|None=None, name:str|None=None, endian:Endian|None=None, crc:CRC|None=None, crc_frame:CRC|None=None, crc_auth:CRC|None=None) -> None:
    if code and name:
      if code in Struct.codes:
        raise Exception(f"Code {code} has been used on struct {self.structs[code]} and cannot be assigned to struct {name}")
      Struct.codes[code] = name
      if not name:
        name = "_struct_" + Struct.id
        Struct.id += 1
    self.code:int = code
    self.name:str = name
    self.endian:Endian|None = endian
    self.crc:CRC|None = crc
    self.crc_frame:CRC|None = crc_frame
    self.crc_auth:CRC|None = crc_auth # is responsible for authorizations, it should be non-standard
    self.size = 0
    self.fields:list[Field] = []
    self.fields_by_name:dict[Field] = {}

  def Add(self, *fields:list[Field]):
    for field in fields:
      self.fields.append(field)
      self.fields_by_name[field.name] = field # not use

  def _Encode(self, data:dict, endian:Endian|None=None):
    if endian is None: endian = self.endian
    if endian is None: endian = Endian.little
    message = b""
    for field in self.fields:
      if field.name not in data:
        raise Exception(f"Field {field.name} not found in struct {self.name}")
      if field.type.name == "string":
        message += bytes(data[field.name], "utf-8") + b"\0"
      elif field.type.name == "bytes":
        message += pack(endian.value + Type.uint16.value, len(data[field.name]))
        message += data[field.name]
      elif field.length > 1: # is array
        if not isinstance(data[field.name], list):
          raise Exception(f"The value of {field.name} must be a list")
        for value in data[field.name]:
          value = value * field.scale + field.offset
          if field.encode: value = field.encode(value)
          if field.type.name != "float" and field.type.name != "double":
            value = int(value)         
          message += pack(endian.value + field.type.value, value)
      else: # is number
        value = data[field.name]
        if isinstance(value, list):
          raise Exception(f"The value of {field.name} must be a number")
        value = value * field.scale + field.offset
        if field.type.name != "float" and field.type.name != "double":
          value = int(value)
        if field.encode: value = field.encode(value)
        message += pack(endian.value + field.type.value, value)
    if self.crc_frame:
      message = self.crc_frame.Encode(message)   
    return message
  
  def _Decode(self, msg:bytes, endian:Endian|None=None):
    if endian is None: endian = self.endian
    if endian is None: endian = Endian.little
    if self.crc_frame:
      frame = self.crc_frame.Decode(frame)
      if frame is None:
        raise Exception("Checksum CRC is not correct 'Frame->Struct._Decode()'")
    data = {}
    offset = 0
    for field in self.fields:
      if field.type.name == "string":
        string = ""
        while msg[offset]:
          string += chr(msg[offset])
          offset += 1
        data[field.name] = string
        offset += 1
      elif field.type.name == "bytes":
        size = unpack_from(endian.value +  Type.uint16.value, msg, offset)[0]
        offset += 2
        data[field.name] = msg[offset:offset + size]
        offset += size
      elif field.length > 1: # is array
        data[field.name] = []
        n = field.length
        while n:
          value = unpack_from(endian.value + field.type.value, msg, offset)[0]
          value = (value - field.offset) / field.scale
          if field.decode: value = field.decode(value)
          if field.type.name == "float": value = round(value, field.round)
          data[field.name].append(value)
          offset += type_size(field.type)
          n -= 1
      else: # is number
        value = unpack_from(endian.value + field.type.value, msg, offset)[0]
        value = (value - field.offset) / field.scale
        if field.decode: value = field.decode(value)
        if field.type.name == "float": value = round(value, field.round)
        data[field.name] = value
        offset += type_size(field.type)
    return [data, offset]
  
  def Encode(self, data_list:list[dict]|dict, endian:Endian|None=None):
    if isinstance(data_list, dict): data_list = [data_list]
    message = b""
    for data in data_list:
      message += self._Encode(data, endian)
    if self.crc_auth:
      message = self.crc_auth.Encode(message) 
    if self.crc:
      message = self.crc.Encode(message)
    return message   
  
  def Decode(self, message:bytes, endian:Endian|None=None) -> list[dict]|dict:
    if self.crc:
      message = self.crc.Decode(message)
      if message is None:
        raise Exception("Checksum CRC is not correct 'Struct.Decode()'")
    if self.crc_auth:
      message = self.crc_auth.Decode(message)
      if message is None:
        raise Exception("Invalid CRC authorization 'Struct.Decode()'") 
    data_list = []
    while message:
      [data, offset] = self._Decode(message, endian)
      data_list.append(data)
      message = message[offset:]
    if len(data_list) == 1: return data_list[0]
    return data_list
  
  def __iter__(self):
    self.i = 0
    return self

  def __next__(self) -> Field:
    if self.i < len(self.fields):
      field = self.fields[self.i]
      self.i += 1
      return field
    else:
      raise StopIteration
    
  def __str__(self):
    return f"Struct {self.code}:{self.name}"

"""
|size-uint16|type-uint16|
|        message        |
|          ...          |
"""

class Frame():
  def __init__(self, *structs:list[Struct], endian:Endian|None=Endian.little, crc:CRC|None=crc32, crc_auth:CRC|None=None) -> None:
    self.structs:list[Struct] = structs
    self.structs_by_code:dict[Struct] = {}
    self.structs_by_name:dict[Struct] = {}
    for struct in self.structs:
      self.structs_by_code[struct.code] = struct
      self.structs_by_name[struct.name] = struct
    self.endian:Endian|None = endian
    self.crc:CRC|None = crc
    self.crc_auth:CRC|None = crc_auth # is responsible for authorizations, it should be non-standard
    
  def Encode(self, data_dict:dict) -> bytes:
    message = b""
    for struct_name, data_list in data_dict.items():
      if not isinstance(data_list, list): data_list = [data_list]
      struct:Struct = self.structs_by_name[struct_name]
      msg =  b"".join([struct._Encode(data, self.endian) for data in data_list])
      message += pack(self.endian.value + Type.uint16.value, len(msg))
      message += pack(self.endian.value + Type.uint16.value, struct.code)
      message += msg
    if self.crc_auth:
      message = self.crc_auth.Encode(message)  
    if self.crc:
      message = self.crc.Encode(message)
    return message
  
  def Decode(self, frame:bytes) -> dict:
    if self.crc:
      frame = self.crc.Decode(frame)
      if frame is None:
        raise Exception("Checksum CRC is not correct 'Frame.Decode()'")
    if self.crc_auth:
      frame = self.crc_auth.Decode(frame)
      if frame is None:
        raise Exception("Invalid CRC authorization 'Frame.Decode()'")   
    size = 0
    n = len(self.structs)
    data_dict = {}
    while(n):
      if not size:
        size = unpack_from(self.endian.value + Type.uint16.value, frame, 0)[0]
        struct_code = unpack_from(self.endian.value + Type.uint16.value, frame, 2)[0]
        frame = frame[4:]
        if struct_code not in self.structs_by_code:
          raise Exception(f"Struct with code {struct_code} not found")
        struct = self.structs_by_code[struct_code]
      while(size):
        struct:Struct
        [data, offset] = struct._Decode(frame, self.endian)
        if struct.name in data_dict:
          if not isinstance(data_dict[struct.name], list): data_dict[struct.name] = [data_dict[struct.name]]
          data_dict[struct.name].append(data)
        else:
          data_dict[struct.name] = data
        frame = frame[offset:]
        size -= offset
      n -= 1
    return data_dict
  
  def get_struct(self, tag:int|str) -> dict:
    if type(tag) is int:
      return self.structs_by_code[tag]
    else:
      return self.structs_by_name[tag]

  def __iter__(self):
    self.i = 0
    return self

  def __next__(self) -> Field:
    if self.i < len(self.structs):
      field = self.structs[self.i]
      self.i += 1
      return field
    else:
      raise StopIteration

if __name__ == "__main__":

  class Modem(Struct):
    def __init__(self, code:int) -> None:
      super().__init__(code, "modem")
      self.Add(
        Field(Type.uint8, "uid", length=12),
        Field(Type.string, "str"),
        Field(Type.float, "sigPower", "dbm"),
        Field(Type.float, "gpsLatitude", "°", scale=100000),
        Field(Type.float, "gpsLongitude", "°", scale=100000)
      )
      
  class SDM230(Struct):
    def __init__(self, code:int) -> None:
      super().__init__(code, "sdm230")
      self.Add(
        Field(Type.uint32, "time", "s"),
        Field(Type.bytes, "bytes"),
        Field(Type.float, "voltage", "V"),
        Field(Type.float, "current", "A"),
        Field(Type.float, "activePower", "W"),
        Field(Type.float, "apparentPower", "VA"),
        Field(Type.float, "reactivePower", "VAr"),
        Field(Type.float, "powerFactor"),
        Field(Type.float, "phaseAngle", "°"),
        Field(Type.float, "frequency", "Hz"),
        Field(Type.float, "importActiveEnergy", "kWh"),
        Field(Type.float, "exportActiveEnergy", "kWh"),
        Field(Type.float, "importReactiveEnergy", "kVArh"),
        Field(Type.float, "exportReactiveEnergy", "kVArh")
      )
    
  # global struct list
  class StructList(Enum):
    modem = 1
    sdm230 = 2
  
  # inserting structs into the structure for Encode & Decode
  fr = Frame(
    Modem(StructList.modem.value),
    SDM230(StructList.sdm230.value)
  )

  # example data
  data = {
    "modem": {
      "uid": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
      "str": "Test",
      "sigPower": -67,
      "gpsLatitude": 23.2,
      "gpsLongitude": 15.6,
    },
    "sdm230": [
      {
        "time": 0,
        "bytes": b"xy\12\13\14\15",
        "voltage": 1,
        "current": 2,
        "activePower": 3,
        "apparentPower": 4,
        "reactivePower": 5,
        "powerFactor": 6,
        "phaseAngle": 7,
        "frequency": 8,
        "importActiveEnergy": 9,
        "exportActiveEnergy": 10,
        "importReactiveEnergy": 11,
        "exportReactiveEnergy": 12,
      },
      {
        "time": 0,
        "bytes": b"ab\62\63\64\65",
        "voltage": 1,
        "current": 2,
        "activePower": 3,
        "apparentPower": 4,
        "reactivePower": 5,
        "powerFactor": 6,
        "phaseAngle": 7,
        "frequency": 8,
        "importActiveEnergy": 9,
        "exportActiveEnergy": 10,
        "importReactiveEnergy": 11,
        "exportReactiveEnergy": 12,
      },
    ],
  }

  # convert data to message
  message = fr.Encode(data)
  print(message)
  # convert message to data
  data = fr.Decode(message)
  print(data)
  
  xyz = Struct(endian=Endian.little, crc=crc32)
  xyz.Add(
    Field(Type.uint16, "x"),
    Field(Type.uint16, "y"),
    Field(Type.uint16, "z"),
  )
  
  message = xyz.Encode([
    { "x": 1, "y": 2, "z": 3 },
    { "x": 4, "y": 5, "z": 6 }
  ])
  print(message)
  data = xyz.Decode(message)
  print(data)
