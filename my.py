import os, shutil
import json, csv
from matplotlib import pyplot as plt
from glob import glob
import itertools
from IPython import get_ipython
from pathlib import Path
import codecs
import re
import zipfile
import csv
from PIL import Image

#------------------------------------------------------------------------------ List

def nbrRange(value:float|int, minv:float|int, maxv:float|int):
  return minv if value < minv else maxv if value > maxv else value

def inIpynb():
  cfg = get_ipython()
  return True if cfg else False

def transposeList(array:list):
  return list(map(list, itertools.zip_longest(*array, fillvalue=None)))

# only list od dicts to dict od lists
def transposeDicts(array:list):
  res = {}
  for row in array:
    for key, value in row.items():
      if key not in res:
        res[key] = []
      res[key].append(value)
  return res

def setList(vect:list, index:int, value:any):
  try:
    vect[index] = value
  except IndexError:
    for _ in range(index - len(vect) + 1):
      vect.append(None)
    vect[index] = value
    
def setList2D(vect:list, x:int, y:int, value:any):
  try:
    vect[x][y] = value
  except IndexError:
    try:
      setList(vect[x], y, value)
    except IndexError:
      for _ in range(x - len(vect) + 1):
        setList(vect, x, [])
      setList(vect[x], y, value)

def toList(content:any):
  if(isinstance(content, list)):
    return content
  else:
    return [content]

#------------------------------------------------------------------------------ files

# for e.g.
# my.imageCompress(src="./image.jpg", prefix="compress-", scale=0.5, quality=30)
def imageCompress(
    src:str,
    dsc:str="",
    prefix:str="",
    suffix:str="",
    quality:int=100, # [%]
    optimize:bool=True,
    scale:int=0,
    width:int=0,
    height:int=0,
    format:str=""
  ):
  img = Image.open(src)
  resize = True
  if scale:
    width, height = img.size[0] * scale, img.size[1] * scale
  elif width:
    height = int(width * img.size[1] / img.size[0])
  elif height:
    width = int(height * img.size[0] / img.size[1])
  else:
    resize = False
  if resize:
    img = img.resize((width, height),Image.Resampling.LANCZOS)
  if prefix or suffix:
    dir = os.path.dirname(src)
    name, ext = os.path.splitext(os.path.basename(src))
    dsc = dir + "/" + prefix + name + suffix + ext
  if not format:
    name, ext = os.path.splitext(os.path.basename(dsc))
    format = ext.lstrip(".")
  
    
  format = format.upper()
  format = "JPEG" if format == "JPG" else format
  # print(format)
  # exit()
  img.save(dsc, format, optimize=optimize, quality=quality)

class folder:
  @staticmethod
  def create(path:str):
    Path(path).mkdir(parents=True, exist_ok=True)
  
  @staticmethod
  def clear(path:str):
    if not os.path.exists(path):
      return
    for filename in os.listdir(path):
      file = os.path.join(path, filename)
      try:
        if os.path.isfile(file) or os.path.islink(file):
          os.unlink(file)
        elif os.path.isdir(file):
          shutil.rmtree(file)
      except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file, e)) # todo log
  
  @staticmethod
  def delete(path:str):
    if not os.path.exists(path):
      return
    folder.clear(path)
    shutil.rmtree(path)
    
  @staticmethod
  def toZip(path:str, name:str, withFolder=False):
    if not os.path.exists(path):
      return
    name = name.removesuffix(".zip") + ".zip"
    with zipfile.ZipFile(name, "w", zipfile.ZIP_DEFLATED) as zipf: 
      for root, dirs, files in os.walk(path):
        for file in files:
          zipf.write(
            os.path.join(root, file),
            os.path.relpath(os.path.join(root, file), 
            os.path.join(path, ".." if withFolder else "."))
          )
  
  @staticmethod
  def through(scr:str, dsc:str, fnc):
    for name in os.listdir(scr):
      scrf = scr + "/" + name
      dscf = dsc + "/" + name
      if os.path.isfile(scrf):
        fnc(scrf, dscf)
      else:
        if not os.path.exists(dscf):
          os.makedirs(dscf)
        folder.through(scrf, dscf, fnc)

  @staticmethod
  def copy(scr:str, dsc:str):
    folder.through(scr, dsc, shutil.copy)

  def imageCompress(
    scr:str,
    dsc:str,
    exts:list[str],
    quality:int=100,
    optimize:bool=True,
    scale:int=0,
    width:int=0,
    height:int=0
  ):
    def fnc(fsrc:str, fdsc:str):
      if(exts):
        go = False
        for ext in exts:
          if fsrc.lower().endswith("." + ext):
            go = True
      else:
        go = True
      if go:
        imageCompress(
          src=fsrc,
          dsc=fdsc,
          quality=quality,
          optimize=optimize,
          scale=scale,
          width=width,
          height=height
        )
    folder.through(scr, dsc, fnc)

class file:
  @staticmethod
  def Clear(name):
    file.Save(name, "")
  
  @staticmethod
  def Delete(name):
    if os.path.exists(name):
      os.remove(name)

  @staticmethod
  def Load(name:str) -> str:
    if name.find('.') == -1:
      name += ".txt"
    openFile = codecs.open(name, "r+", "utf-8")
    string = openFile.read()
    openFile.close()
    return string
  
  @staticmethod
  def linesLoad(name:str) -> list:
    if name.find('.') == -1:
      name += ".out"
    openFile = codecs.open(name, "r+", "utf-8")
    lines = list(openFile.readlines())
    openFile.close()
    return lines

  @staticmethod
  def Save(name:str, string:str):
    folder.create(os.path.dirname(name))
    openFile = codecs.open(name, "w+", "utf-8")
    openFile.write(string)
    openFile.close()

  @staticmethod
  def binLoad(name:str) -> bytes:
    name = name.removesuffix('.bin') + '.bin'
    openFile = codecs.open(name, "rb+", "utf-8")
    bytes = openFile.read()
    openFile.close()
    return bytes

  @staticmethod
  def binSave(name:str, data:bytes):
    name = name.removesuffix('.bin') + '.bin'
    folder.create(os.path.dirname(name))
    openFile = codecs.open(name, "wb+", "utf-8")
    openFile.write(data)
    openFile.close()

  @staticmethod
  def jsonLoad(name:str, otherwise:None|list|dict=None) -> dict|list|dict:
    name = name.removesuffix('.json') + '.json'
    if not os.path.isfile(name):
      return otherwise
    openFile = codecs.open(name, "r+", "utf-8")
    content = openFile.read()
    if content:
      content = json.loads(content)
    else:
      return otherwise
    openFile.close()
    return content

  @staticmethod
  def jsonSave(name:str, content:dict):
    name = name.removesuffix('.json') + '.json'
    openFile = codecs.open(name, "w+", "utf-8")
    openFile.write(json.dumps(content))
    openFile.close()

  @staticmethod
  def jsonSavePrettie(name:str, content:dict):
    name = name.removesuffix('.json') + '.json'
    openFile = codecs.open(name, "w+", "utf-8")
    openFile.write(json.dumps(content, indent=2))
    openFile.close()
    
  @staticmethod
  def iniLoad(name:str) -> dict:
    name = name.removesuffix('.ini') + '.ini'
    string = file.Load(name)
    string = re.sub("( *\r?\n *)+", "\n", string)
    lines = string.split("\n")
    ini = {}
    section = None
    for line in lines:
      line = line.strip()
      if not line or line[0] == ";" or line[0] == "#":
        continue
      x = line.split("=", 1)
      key = x[0].strip()
      if key[0] == "[" and key[-1] == "]":
        section = key[1:-1]
        ini[section] = {}
        continue
      value = None if len(x) == 1 else x[1].strip()
      if (value[0] == "'" and value[-1] == "'") or (value[0] == '"' and value[-1] == '"'):
        value = value[1:-1]
      if section:
        ini[section][key] = value
      else:
        ini[key] = value
    return ini     
    
  @staticmethod
  def csvLoad(name, delimiter=",") -> list:
    name = name.removesuffix('.csv') + '.csv'
    raw = csv.DictReader(codecs.open(name, "r", "utf-8"))
    file = []
    for row in raw:
      file.append(row)
    return file
    
#---------------------------------------------------------------------------------------------------------------------- buffer

class buffer:
  def __init__(self, limit:int=64) -> None:
    self.limit = limit
    self.list = []

  def Push(self, value:any) -> None:
    if isinstance(value, list):
      self.list += value
    self.list.append(value)
    while len(self.list) > self.limit:
      self.list.pop(0)

  def Clear(self):
    self.list.clear

  def String(self, separator="\n") -> str:
    string = ""
    for value in self.list:
      string += str(value) + separator
    return string.strip()

  def __str__(self) -> str:
    return str(self.list)
  