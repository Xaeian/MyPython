import os, shutil, codecs, re, json, csv, itertools, zipfile, calendar, io
from datetime import datetime, timedelta
from pathlib import Path

"""
Some code snippets are a piece of shit,
but sharing these modules allows me to put them in different projects.
I hope someday they will be better
https://github.com/Xaeian/
2023-11-08 12:50:00
"""

def nbrRange(value:float|int, minv:float|int, maxv:float|int):
  return minv if value < minv else maxv if value > maxv else value

def transpose_list(array:list):
  return list(map(list, itertools.zip_longest(*array, fillvalue=None)))

def transposeDicts(array:list):
  res = {}
  for row in array:
    for key, value in row.items():
      if key not in res:
        res[key] = []
      res[key].append(value)
  return res

def to_csv(data:list[dict], delimiter:str=",") -> str:
  output = io.StringIO()
  keys = list(data[0].keys())
  writer = csv.DictWriter(output, fieldnames=keys, delimiter=delimiter)
  writer.writeheader()
  writer.writerows(data)
  csv_string = output.getvalue()
  output.close()
  return csv_string

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
  def exec_through(scr:str, dsc:str, fnc):
    for name in os.listdir(scr):
      scrf = scr + "/" + name
      dscf = dsc + "/" + name
      if os.path.isfile(scrf):
        fnc(scrf, dscf)
      else:
        if not os.path.exists(dscf):
          os.makedirs(dscf)
        folder.exec_through(scrf, dscf, fnc)

  @staticmethod
  def copy(scr:str, dsc:str):
    folder.exec_through(scr, dsc, shutil.copy)

class file:
  @staticmethod
  def clear(name):
    file.Save(name, "")
  
  @staticmethod
  def delete(name):
    if os.path.exists(name):
      os.remove(name)

  @staticmethod
  def load(name:str) -> str:
    if name.find('.') == -1:
      name += ".txt"
    openFile = codecs.open(name, "r+", "utf-8")
    string = openFile.read()
    openFile.close()
    return string
  
  @staticmethod
  def load_lines(name:str) -> list:
    if name.find('.') == -1:
      name += ".out"
    openFile = codecs.open(name, "r+", "utf-8")
    lines = list(openFile.readlines())
    openFile.close()
    return lines

  @staticmethod
  def save(name:str, string:str):
    folder.create(os.path.dirname(name))
    openFile = codecs.open(name, "w+", "utf-8")
    openFile.write(string)
    openFile.close()

  @staticmethod
  def load_bin(name:str) -> bytes:
    name = name.removesuffix('.bin') + '.bin'
    openFile = codecs.open(name, "rb+")
    bytes = openFile.read()
    openFile.close()
    return bytes

  @staticmethod
  def save_bin(name:str, data:bytes):
    name = name.removesuffix('.bin') + '.bin'
    folder.create(os.path.dirname(name))
    openFile = open(name, "wb+")
    openFile.write(data)
    openFile.close()

  @staticmethod
  def load_json(name:str, otherwise:None|list|dict=None) -> dict|list|dict:
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
  def save_json(name:str, content:dict):
    name = name.removesuffix('.json') + '.json'
    openFile = codecs.open(name, "w+", "utf-8")
    openFile.write(json.dumps(content))
    openFile.close()

  @staticmethod
  def save_json_prettie(name:str, content:dict):
    name = name.removesuffix('.json') + '.json'
    openFile = codecs.open(name, "w+", "utf-8")
    openFile.write(json.dumps(content, indent=2))
    openFile.close()

  @staticmethod
  def load_ini(name: str) -> dict:
    name = name.removesuffix('.ini') + '.ini'
    if not os.path.exists(name):
      return {}
    try:
      with open(name, 'r+', encoding="utf-8") as file:
        string = file.read()
    except FileNotFoundError:
      raise FileNotFoundError(f"Plik '{name}' nie istnieje.")
    string = re.sub(r"(;|#).*", "", string)
    string = re.sub(r"( *\r?\n *)+", "\n", string)
    lines = string.split("\n")
    ini = {}
    section = None
    for line in lines:
      line = line.strip()
      if not line:
        continue
      if line.startswith("[") and line.endswith("]"):
        section = line[1:-1]
        ini[section] = {}
        continue
      key_value = line.split("=", 1)
      key = key_value[0].strip()
      value = key_value[1].strip() if len(key_value) > 1 else None
      isstr = False
      if value and (value[0] == value[-1]) and (value[0] in ('"', "'")):
        value = value[1:-1]
        isstr = True
      if not isstr:
        if not value: value = None
        elif value.lower() == "true": value = True
        elif value.lower() == "false": value = False
        else:
          try: value = int(value)
          except:
            try: value = float(value)
            except: value = value
      if section:
        ini[section][key] = value
      else:
        ini[key] = value
    return ini

  @staticmethod
  def save_ini(name: str, data: dict):
    name = name.removesuffix('.ini') + '.ini'
    with open(name, 'w', encoding="utf-8") as file:
      for left, right in data.items():
        if type(right) is dict:
          section = left
          section_data = right
          file.write(f"[{section}]\n")
          for key, value in section_data.items():
            if value is None:
              file.write(f"{key} =\n")
            else:
              if type(value) is str: value = '"' + value + '"'
              file.write(f"{key} = {value}\n")
        else:
          key = left
          value = right
          if value is None:
            file.write(f"{key} =\n")
          else:
            if type(value) is str: value = '"' + value + '"'
            file.write(f"{key} = {value}\n")

  @staticmethod
  def load_csv(name:str, delimiter=",") -> list:
    name = name.removesuffix('.csv') + '.csv'
    raw = csv.DictReader(codecs.open(name, "r", "utf-8"))
    file = []
    for row in raw:
      file.append(row)
    return file
  
  def add_to_csv(name:str, data_row:dict|list=[]):
    name = name.removesuffix(".csv") + ".csv"
    if not os.path.isfile(name):
      with open(name, "w", newline="") as nowy_plik_csv:
        writer = csv.writer(nowy_plik_csv)
        if type(data_row) is dict:
          writer.writerow(data_row.keys())
    with open(name, "a", newline="") as plik_csv:
      writer = csv.writer(plik_csv)
      if type(data_row) is dict:
        data_row = data_row.values()
      writer.writerow(data_row)

#-------------------------------------------------------------------------------------------------- datetime  

class idt(datetime):

  def interval(interval:str="", dt:None|datetime=None):
    dt = idt.now() if dt is None else dt
    value = re.findall(r"\-?[0-9]*\.?[0-9]+", interval)
    if not value: return dt
    value = float(value[0])
    factor = re.sub("[^a-z]", "", interval.lower())
    if factor == "y" or factor == "mo":
      if factor == "y": value *= 12
      month = dt.month - 1 + int(value)
      year = dt.year + month // 12
      month = month % 12 + 1
      day = min(dt.day, calendar.monthrange(year, month)[1])
      return dt.replace(year, month, day)
    match factor:
      case "w": dt += timedelta(weeks=value)
      case "d": dt += timedelta(days=value)
      case "h": dt += timedelta(hours=value)
      case "m": dt += timedelta(minutes=value)
      case "s": dt += timedelta(seconds=value)
      case "ms": dt += timedelta(milliseconds=value)
      case "us": dt += timedelta(microseconds=value)
    return dt

  def intervals(intervals:str=""):
    dt = idt.now()
    for interval in intervals.split():
      dt = idt.interval(interval, dt)
    return dt

  def is_interval(text:str):
    if re.search(r"^(\-|\+)?[0-9]*\.?[0-9]+(y|mo|w|d|h|m|s|ms|µs|us)$", text.strip()): return True
    else: return False

  def is_intervals(text:str):
    if re.search(r"^((\-|\+)?[0-9]*\.?[0-9]+(y|mo|w|d|h|m|s|ms|µs|us) ?)*$", text.strip()): return True
    else: return False

  def create(some:str|int|float|datetime|None="now"):
    if some is None: return None
    if type(some) is datetime: return some
    some = str(some).strip()
    if some.lower() == "now": return idt.now()
    if some.replace(".", "", 1).isdigit(): return idt.fromtimestamp(float(some))
    if idt.is_interval(some): return idt.interval(some)
    if idt.is_intervals(some): return idt.intervals(some)
    some = some.replace("T", "")
    if re.search(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})$", some): return idt.strptime(some, '%Y-%m-%d %H:%M:%S')
    if re.search(r"^(\d{2}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})$", some): return idt.strptime(some, '%m/%d/%y %H:%M:%S')
    if re.search(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.(\d{3}|\d{6}))$", some): return idt.strptime(some, '%Y-%m-%d %H:%M:%S.%f')
    if re.search(r"^(\d{2}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}.(\d{3}|\d{6}))$", some): return idt.strptime(some, '%m/%d/%y %H:%M:%S.%f')
    else: return None

  def __str__(self):
    return self.strftime("%Y-%m-%d %H:%M:%S.%f")

# ----------------------------------------------------------------------------- String

def split_str(string:str, split:str= " ", string_char:str='"', escape_char:str = "\\") -> list:
  def trim(value:str) -> str:
    if value[0] == string_char and value[-1] == string_char: return value[1:-1]
    else: return value
  array:list = []
  k:int = 0
  mute:bool = False
  mute_start:bool = False
  mute_end:bool = False
  escape:bool = False
  inc:int = 0
  count:int = len(split)
  val:str = ""
  i:int = 0
  while i < len(string):
    if string[i] == string_char:
      if not mute:
        mute_start = True
        mute = True
        if mute_end == True:
          array.append(trim(val))
          val = ""
    mute_end = False
    if not mute:
      j = 0
      go_continue = False
      while j < count:
        if string[i + j] == split[j]:
          if j + 1 == count:
            if not inc: val = trim(val)
            inc = 0
            k += 1
            array.append(val)
            val = ""
            i += j
            go_continue = True
            break # continue 2
        else:
          break
        j += 1
      if go_continue:
        i += 1
        continue
      inc += 1      
    if mute and not mute_start:
      if string[i] == escape_char: escape = True
      elif not escape and string[i] == string_char:
        mute = False
        mute_end = True
      else: escape = False
    if not escape:
      val += string[i]
    mute_start = False
    if i + 1 == len(string) and not inc:
      val = trim(val)
    i += 1
  array.append(val)
  return array

# test = 'Hello "world" this "\\"" is """ a" "test string" with "escape\\"s: " char'
# result = split_str(test)
# print(result)

def split_sql(sqls):
  sqls = split_str(sqls, ";", "'")
  for i, sql in enumerate(sqls):
    sql = re.sub(r"[\n\r]+", "", sql)
    sql = re.sub(r"[\ ]+", " ", sql)
    sql = re.sub(r"\ ?\(\ ?", "(", sql)
    sql = re.sub(r"\ ?\)\ ?", ")", sql)
    sql = re.sub(r"\ ?\,\ ?", ",", sql)
    sql = re.sub(r"\ ?\=\ ?", "=", sql)
    sqls[i] = sql
  output = []
  i = 0
  for sql in sqls:
    if sql and sql != " ":
      output.append(sql + ";")
      i += 1
  return output