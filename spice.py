from stdlib import *
from plot import Plot
from matplotlib import pyplot as plt
import threading
import subprocess
from datetime import datetime
import pandas as pd
import time

class Sumulation:
  def __init__(self, replaceKeys:list=[], rename:dict={}, multiplier:dict={}, load:bool=False, path:str="./", lib:str="C:/Kicad/Spice"):
        
    self.replaceKeys = toList(replaceKeys)
    self.rename = rename
    self.multiplier = multiplier
    self.path = path
    self.name = glob(f"{self.path}*.sch")[0].lstrip(".\\/").removesuffix(".sch")
    self.load = load
    self.inc = 0
    self.cir = file.Load(f"{self.path}{self.name}.cir").rstrip().removesuffix(".end")
    self.cir = self.cir.replace("{LSM}", lib).replace("{LIB}", lib)
    
    cirLines = self.cir.splitlines()
    for line in cirLines:
      if line.startswith(".include"):
        inc = file.Load(line.split()[1].strip('"')).strip()
        self.cir = self.cir.replace(line, inc)
    self.cir += file.Load(f"{self.path}{self.name}.sp")
  
  def Load(self, id:int) -> pd.DataFrame:
    csvName = f"{self.name}{id}.csv"
    if os.path.exists(csvName):
      return pd.read_csv(csvName, header=0)
    return pd.DataFrame()
    
  def Run(self, id:int, replaceValues=[]) -> pd.DataFrame:
    df = self.Load(id)
    if self.load and not df.empty:
      return df
    
    replaceValues = toList(replaceValues)
    cir = self.cir
    for key, value in zip(self.replaceKeys, replaceValues):
      cir = cir.replace(key, str(value))
    
    fileName = f"{self.path}#{id}"
    cirName = f"{fileName}.cir"
    outName = f"{fileName}.out"
    csvName = f"{self.name}{id}.csv"
    file.Delete(cirName)
    file.Delete(outName)
    cir = cir.replace("{FILE}", outName)
    file.Save(cirName, cir)
    pro = subprocess.Popen(f'ngspice "{cirName}"', stdout=subprocess.PIPE)
    while not os.path.exists(outName):
      pass
    time.sleep(0.2)
    pro.kill()
    lines = file.linesLoad(outName)
    
    head, data, state, id = [], {}, "head", 0
    for line in lines:
      if state == "head":
        if line.startswith("Title"):
          self.title = line.split(": ")[1].strip()
        if line.startswith("Date"):
          self.date = datetime.strptime(line.split(": ")[1].strip(), "%c")
        elif line.startswith("Variables"):
          state = "variable"
      elif state == "variable":
        if line.startswith("Values"):
          state = "value"
        else:
          columnName = line.strip().split()[1].upper()
          head.append(columnName)
          data[columnName] = []
      elif state == "value":
        line = line.strip()
        if(line):
          value = float(line) if id else float(line.split()[1])
          data[head[id]].append(value)
          id += 1
          if(id >= len(head)):
            id = 0
    
    df = pd.DataFrame(data)
    df.rename(columns=self.rename, inplace=True)
    for key, value in self.multiplier.items():
      df[key] *= value
    df.to_csv(csvName, index=False)
    file.Delete(cirName)
    file.Delete(outName)
    return df
  
def Chart(simulations:list, labels:str, legend:str, measurement:list=[]):
  sim = dict(zip(labels, simulations))
  ax = 0
  if measurement:
    msm = dict(zip(labels, measurement))
  plots = {}
  for name, data in simulations[0].iteritems():
    if 'lab' in locals():
      plots[name] = Plot(lab, name, legend)
    else:
      lab = name
  for key, df in sim.items():
    for name, data in df.iteritems():
      if name != lab:
        if 'msm' in locals():
          plots[name].Add(key, df[lab], data, msm[key][lab], msm[key][name])
        else:
          plots[name].Ax(ax).Add(key, df[lab], data)
    ax += 1
  for name, plot in plots.items():
    name = legend + "-" + name if legend else name
    plot.ViewSharing().SaveView(name)
  
def Analize(simulation:Sumulation, params:list, labels:list, legend:str):
  threads = list(map(lambda values, i: threading.Thread(target=simulation.Run, args=(i, values)), params, range(len(params))))
  list(map(lambda thread: thread.start(), threads))
  list(map(lambda thread: thread.join(), threads))
  simulations = list(map(lambda i: simulation.Load(i), range(len(threads))))
  Chart(simulations, labels, legend)
