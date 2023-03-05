import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.dates as mdates
from collections.abc import Iterable
from IPython import get_ipython
import my



# 

def inIpynb():
  cfg = get_ipython()
  return True if cfg else False

import itertools



only list od dicts to dict od lists


#----------------------------------------------------------------------------------------------------------------------

class Plotcoll:

  def __init__(self, mode:str="plot", **option:dict):
    self.mode = mode
    self.option = option

class Plotsize:
  
  def __init__(self, width:float=16, height:float=8, dpi:int=100):
    self.width = width
    self.height = height
    self.dpi = dpi
    
  def Scale(self, width:float, height:float=0):
    if height == 0:
      height = width
    self.width *= width
    self.height *= height

#----------------------------------------------------------------------------------------------------------------------

class Plot():
  
  def __init__(self, x:str|list="", y:str|list="", legend:str|list="", **args:dict):
    self.label_x = x if type(x) == str else x[0] + " [" + x[1] + "]"
    self.label_y = y if type(y) == str else y[0] + " [" + y[1] + "]"
    self.label_legend = legend if type(legend) == str else legend[0] + " [" + legend[1] + "]"
    self.label_legend = self.label_legend + ":" if self.label_legend else ""
    if "time" not in args:
      args["time"] = "%y-%m-%d\n%H:%M:%S" if "A5" not in args else "%m-%d\n%H:%M"
    if "format" not in args:
      args["format"] = "web"
    self.args = args
    self.series = []
    self.collection = []
    self.ax = 0
    self.fnc = None
    self.sizeView = Plotsize(6, 3, 72) if inIpynb() else Plotsize(14.5, 6.5, 100)
    self.sizeSave = Plotsize(5.8, 4.15, 600) if args["format"] == "A5" else Plotsize()
    self.styleDisp = "bmh"
    self.styleSave = "seaborn-whitegrid"
    self.phantom = [""]
    self.colorNext = True
    self.Subplots()
    self.ymin, self.ymax, self.xmin, self.xmax = None, None, None, None

  def ScaleView(self, width:float, height:float=0):
    if height == 0:
      height = width
    self.sizeView.width *= width
    self.sizeView.height *= height
    return self
  
  def ScaleSave(self, width:float, height:float=0):
    if height == 0:
      height = width
    self.sizeSave.width *= width
    self.sizeSave.height *= height
    return self
  
  def Scale(self, width:float, height:float=0):
    self.ScaleView(width, height)
    self.ScaleSave(width, height)
    return self
    
  def Ax(self, nbr:int):
    self.ax = nbr
    return self
  
  def AxesCount(self) -> int:
    count = 0
    for serie in self.series:
      count = serie["ax"] if serie["ax"] > count else count
    return count + 1
    
  def SetCollection(self, *collection:list[Plotcoll]):
    self.collection = collection
    return self
  
  def SetPhantom(self, mode:str):
    self.phantom.append(mode.lower())
    self.colorNext = False
    return self
  
  def SetRange(self, ymin:float=None, ymax:float=None, xmin:float=None, xmax:float=None):
    self.ymin = ymin if ymin != None else self.ymin
    self.ymax = ymax if ymax != None else self.ymax
    self.xmin = xmin if xmin != None else self.xmin
    self.xmax = xmax if xmax != None else self.xmax
  
  def Add(self, label:str|list, *series:list[list]):
    for iax, mode in enumerate(self.phantom):
      serie = { "x":[], "y":[], "ax": self.ax + iax, "xmin": self.xmin, "xmax": self.xmax }
      serie["name"] = label if type(label) == str else label[0]
      serie["unit"] = "" if type(label) == str else label[1]
      serie["logx"] = True if "x" in mode else False
      serie["logy"] = True if "y" in mode else False
      for i in range(0, len(series), 2):
        serie["x"].append(series[i])
        y = np.asarray(series[i+1])
        if self.ymin != None:
          y[y < self.ymin] = None
        if self.ymax != None:
          y[y > self.ymax] = None
        serie["y"].append(y)
      self.series.append(serie)
    return self

  def AddStd(self, label:str|list, *series:list[list]):
    if not self.collection:
      self.collection.append(Plotcoll())
    std = np.std(series[1])
    mean = np.mean(series[1])
    seriesStd = []
    x = True
    for serie in series:
      if x:
        seriesStd.append(serie)
      else:
        seriesStd.append((np.asarray(serie) - mean) / std)
      x = not x
    self.Add(label, *seriesStd)
    return self
  
  def __AxesAppend(self, ax:Axes, x, y, mode:str="plot", option:dict={}):
    if mode == "plot":
      ax.plot(x, y, **option)
    elif mode == "scatter":
      ax.scatter(x, y, **option)
  
  def Draw(self, fig:Figure, *axes:list[Axes]) -> Figure:
    if("title" in self.args):
      fig.suptitle(self.args["title"])
    for i, serie in zip(range(len(self.series)), self.series):
      ax = axes[serie["ax"]]
      if not ax:
        continue
      lebel = True
      if not self.collection:
        for _ in serie["x"]:
          self.collection.append(Plotcoll())
      for coll, x, y in zip(self.collection, serie["x"], serie["y"]):
        option = coll.option.copy()
        if(self.colorNext):
          option["color"] = "C" + str(i)
        if lebel:
          option["label"] = serie["name"]
          lebel = False
        self.__AxesAppend(ax, x, y, coll.mode, option)
      pdx = pd.DataFrame(x)
      if(is_datetime64_any_dtype(pdx)):
        ax.xaxis.set_major_formatter(mdates.DateFormatter(self.args["timeFormat"]))
      if(len(self.series) > 1):
        ax.legend(loc="best", title=self.label_legend)
      ax.set_xlabel(self.label_x)
      label_y = self.label_y if self.label_y or len(self.series) > 1 else serie["name"] + " [" + serie["unit"] + "]" if serie["unit"] else serie["name"]
      if label_y:
        ax.set_ylabel(label_y)
      if serie["logx"]:
        ax.set_xscale("log")
      if serie["logy"]:
        ax.set_yscale("log")
      if serie["xmin"] and serie["xmax"]:
        ax.set_xlim(left=serie["xmin"], right=serie["xmax"])
      elif serie["xmin"]:
        ax.set_xlim(left=serie["xmin"])
      elif serie["xmax"]:
        ax.set_xlim(right=serie["xmax"])
    return fig
  
  def Subplots(self, rows:int=1, cols:int=1):
    self.rows = rows
    self.cols = cols
    return self
  
  def __Show(self, fig:Figure, size:Plotsize|None=None):
    if(not size):
      size = self.sizeView
    fig.set_dpi(size.dpi)
    fig.set_size_inches(size.width, size.height, forward=True)
    plt.show()
    plt.close(fig)
  
  def __View(self, style:str) -> Figure:
    with plt.style.context(style):
      fig, axes = plt.subplots(self.rows, self.cols)
    self.fnc = self.__View
    if isinstance(axes, Iterable):
      return self.Draw(fig, *axes)
    else:
      return self.Draw(fig, axes)
  
  def View(self, size:Plotsize|None=None):
    fig = self.__View(self.styleDisp)
    self.__Show(fig, size)
    return self
  
  def __ViewSharing(self, style:str) -> Figure:
    with plt.style.context(style):
      fig = plt.figure()
      gs = fig.add_gridspec(self.AxesCount(), hspace=0.02)
      axes = gs.subplots(sharex=True, sharey=False)
    self.fnc = self.__ViewSharing
    for ax in axes:
      ax.label_outer()
    return self.Draw(fig, *axes)
    
  def ViewSharing(self, size:Plotsize|None=None):
    fig = self.__ViewSharing(self.styleDisp)
    self.__Show(fig, size)
    return self
  
  def __Save(self, fig:Figure, path:str, size:Plotsize|None=None):
    if(not size):
      size = self.sizeSave
    fig.set_dpi(size.dpi)
    fig.set_size_inches(size.width, size.height, forward=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
  
  def Save(self, name:str, format:str="png", dir:str="./{format}", display:Plotsize|None=None):
    dir = dir.replace("{format}", format)
    my.folder.create(dir)
    count = self.AxesCount()
    for i in range(count):
      with plt.style.context(self.styleSave):
        fig, ax = plt.subplots()
      axes = [None] * len(self.series)
      axes[i] = ax
      self.Draw(fig, *axes)
      postfix = str(i + 1) if count > 1 else ""
      self.__Save(fig, f"{dir}/{name}{postfix}.{format}", display)
    return self
  
  def SaveView(self, name:str, format:str="png", dir:str="./{format}", display:Plotsize|None=None):
    dir = dir.replace("{format}", format)
    my.folder.create(dir)
    if not self.fnc:
      return self
    fig = self.fnc(self.styleSave)
    self.__Save(fig, f"{dir}/{name}.{format}", display)
    return self
