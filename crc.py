CRC_MASK = { 8:0xFF, 16:0xFFFF, 32:0xFFFFFFFF }

def ReflectBit(data:int, width:int) -> int:
  reflection = 0
  for bit in range(width):
    if data & 0x01:
      reflection |= (1 << ((width - 1) - bit))
    data = (data >> 1)
  return reflection

class CRC:
  def __init__(
    self,
    width:int,
    polynomial:int,
    initial:int,
    reflectIn:bool,
    reflectOut:bool,
    xor:int,
    invertOut:bool
  ):
    self.width = width
    self.polynomial = polynomial
    self.initial = initial
    self.reflectIn = reflectIn # reflect_data_in
    self.reflectOut = reflectOut # reflect_data_out
    self.xor = xor
    self.invertOut = invertOut
    self.topbit = (1 << (width - 1))
    self.array = list()
    self.__init()
    
  def __init(self):
    for i in range(256):
      remainder = i << (self.width - 8)
      for bit in range(8, 0, -1):
        if remainder & self.topbit: remainder = (remainder << 1) ^ self.polynomial
        else: remainder = (remainder << 1)
      remainder &= CRC_MASK[self.width]
      self.array.append(remainder)
  
  def Run(self, msg:bytes):
    msg = [x for x in msg]
    remainder = self.initial
    for byte in range(len(msg)):
      if self.reflectIn: msg[byte] = ReflectBit(msg[byte], 8)
      data = msg[byte] ^ (remainder >> (self.width - 8))
      tmp = data & CRC_MASK[8]
      remainder = self.array[tmp] ^ (remainder << 8)
    remainder &= CRC_MASK[self.width]
    if self.reflectOut: remainder = ReflectBit(remainder, self.width)
    remainder = remainder ^ self.xor
    if self.invertOut: self.toInt(bytes(reversed(self.toBytes(remainder))));
  
  def toBytes(self, crc:int) -> bytes:
    return crc.to_bytes(int(self.width / 8), byteorder="big")
  
  def toInt(self, crc:bytes) -> int:
    crc = [x for x in crc]
    if self.width == 32: return int((crc[0] << 24) + (crc[1] << 16) + (crc[2] << 8) + crc[3])
    if self.width == 16: return int((crc[0] << 8) + crc[1])
    if self.width == 8: return int(crc[0])
    
  def Decode(self, frame:bytes) -> bytes or None:
    n = int(self.width / 8)
    if(len(frame) < n):
      return None
    msg = frame[:-n]
    crc = frame[-n:]
    if self.toInt(crc) == self.Run(msg):
      return msg
    return None
  
  def Encode(self, msg:bytes) -> bytes:
    crc = self.Run(msg)
    return msg + self.toBytes(crc)
  
crc32 = CRC(32, 0x04C11DB7, 0xFFFFFFFF, True, True, 0xFFFFFFFF, False)
crc16_kermit = CRC(16, 0x1021, 0x0000, True, True, 0x0000, False)
crc16_modbus = CRC(16, 0x8005, 0xFFFF, True, True, 0x0000, True)
crc8 = CRC(8, 0x07, 0x00, False, False, 0x00, False)
