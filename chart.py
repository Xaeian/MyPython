from stdlib import *
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.dates as mdates
from copy import copy

class ChartSettings:
  saveWidth:float=5.8
  saveHeight:float=4.15
  pdfPath:str="./pdf/"
  pngPath:str="./png/"
  dispStyle:str="bmh"
  saveStyle:str="seaborn-whitegrid"
  pointSize:int=15
  
  def Scale(self, width:float, height:float=0):
    if height == 0:
      height = width
    self.saveWidth *= width
    self.saveHeight *= height

class ChartLineLog(ChartSettings):
  dispWidth:float=16
  dispHeight:float=4
  def __init__(self, xlab:str="", ylab:str="", xunit:str="", yunit:str="", llab:str="", lunit:str="", title:str="",  min:float=10**-3):
    self.min = min
    self.legend = llab + " [" +  lunit + "]" if lunit else llab
    with plt.style.context(self.dispStyle):
      self.dispFig, (self.dispAx1, self.dispAx2) = plt.subplots(1, 2)
    with plt.style.context(self.saveStyle):
      self.saveFig1, self.saveAx1 = plt.subplots()
      self.saveFig2, self.saveAx2 = plt.subplots()
    if title:
      self.dispFig.suptitle(title)
    if(xlab):
      lab = xlab + " [" +  xunit + "]" if xunit else xlab
      self.dispAx1.set_xlabel(lab)
      self.dispAx2.set_xlabel(lab)
      self.saveAx1.set_xlabel(lab)
      self.saveAx2.set_xlabel(lab)      
    if(ylab):
      lab = ylab + " [" +  yunit + "]" if yunit else ylab
      self.dispAx1.set_ylabel(lab)
      self.dispAx2.set_ylabel(lab)
      self.saveAx1.set_ylabel(lab)
      self.saveAx2.set_ylabel(lab)
    self.dispFig.set_size_inches(self.dispWidth, self.dispHeight, forward=True)
    self.dispAx2.set_yscale("log")
    self.saveAx2.set_yscale("log")
  
  def Add(self, label, xline, yline, xpoint=[], ypoint=[]):
    if self.min:
      yline[yline < self.min] = None
    if len(xpoint):
      self.dispAx1.scatter(xpoint, ypoint, s=self.pointSize, label=label)
      self.dispAx1.plot(xline, yline)
      self.dispAx2.scatter(xpoint, ypoint, s=self.pointSize, label=label)
      self.dispAx2.plot(xline, yline)
      self.saveAx1.scatter(xpoint, ypoint, s=self.pointSize, label=label)
      self.saveAx1.plot(xline, yline)
      self.saveAx2.scatter(xpoint, ypoint, s=self.pointSize, label=label)
      self.saveAx2.plot(xline, yline)
    else:
      self.dispAx1.plot(xline, yline, label=label)
      self.dispAx2.plot(xline, yline, label=label)
      self.saveAx1.plot(xline, yline, label=label)
      self.saveAx2.plot(xline, yline, label=label)
    
  def Run(self, name:str="fig", format:str=""):
    self.dispAx1.legend(loc="best", title = self.legend)
    self.dispAx2.legend(loc="best", title = self.legend)
    self.saveAx1.legend(loc="best", title = self.legend)
    self.saveAx2.legend(loc="best", title = self.legend)
    self.saveFig1.set_dpi(600)
    self.saveFig2.set_dpi(600)
    self.saveFig1.set_size_inches(self.saveWidth, self.saveHeight, forward=True)
    self.saveFig2.set_size_inches(self.saveWidth, self.saveHeight, forward=True)
    if format == "png" or format == "all":
      folder.MakeSure(self.pngPath)
      self.saveFig1.savefig(self.pngPath + name + ".png", bbox_inches = "tight")
      self.saveFig2.savefig(self.pngPath + name + ".ylog.png", bbox_inches = "tight")
    if format == "pdf" or format == "all":
      folder.MakeSure(self.pdfPath)
      self.saveFig1.savefig(self.pdfPath + name + ".pdf", bbox_inches = "tight")
      self.saveFig2.savefig(self.pdfPath + name + ".ylog.pdf", bbox_inches = "tight")
    plt.close(self.saveFig1)
    plt.close(self.saveFig2)
    plt.show()

class Chart(ChartSettings):
  dispWidth:float=8
  dispHeight:float=4
  def __init__(self, xlab:str="", ylab:str="", xunit:str="", yunit:str="", llab:str="", lunit:str="", title:str="", min:float=0):
    self.min = min
    self.legend = llab + " [" +  lunit + "]" if lunit else llab
    with plt.style.context(self.dispStyle):
      self.dispFig, self.dispAx = plt.subplots()
    with plt.style.context(self.saveStyle):
      self.saveFig, self.saveAx = plt.subplots()
    if title:
      self.dispFig.suptitle(title)
      self.saveFig.suptitle(title)
    if(xlab):
      lab = xlab + " [" +  xunit + "]" if xunit else xlab
      self.dispAx.set_xlabel(lab)
      self.saveAx.set_xlabel(lab)      
    if(ylab):
      lab = ylab + " [" +  yunit + "]" if yunit else ylab
      self.dispAx.set_ylabel(lab)
      self.saveAx.set_ylabel(lab)
    self.dispFig.set_size_inches(self.dispWidth, self.dispHeight, forward=True)
    
  def Add(self, label, xline=[], yline=[], xpoint=[], ypoint=[]):
    if self.min:
      yline[yline < self.min] = None
      
    if len(xline):
      if len(xpoint):
        self.dispAx.plot(xline, yline)
        self.saveAx.plot(xline, yline)
      else:
        self.dispAx.plot(xline, yline, label=label)
        self.saveAx.plot(xline, yline, label=label)
    if len(xpoint):
      self.dispAx.scatter(xpoint, ypoint, s=self.pointSize, label=label)
      self.saveAx.scatter(xpoint, ypoint, s=self.pointSize, label=label)
    
  def AddNorm(self, label, xline, yline, xpoint=[], ypoint=[]): 
    std = np.std(yline)
    mean = np.mean(yline)
    yline = (yline - mean) / std
    ypoint = (ypoint - mean) / std
    self.Add(label, xline, yline, xpoint, ypoint)
    
  def Run(self, name:str="fig", format:str=""):
    self.dispAx.legend(loc="best", title = self.legend)
    self.saveAx.legend(loc="best", title = self.legend)
    self.saveFig.set_dpi(600)
    self.saveFig.set_size_inches(self.saveWidth, self.saveHeight, forward=True)
    if format == "png" or format == "all":
      folder.MakeSure(self.pngPath)
      self.saveFig.savefig(self.pngPath + name + ".png", bbox_inches = "tight")
    if format == "pdf" or format == "all":
      folder.MakeSure(self.pdfPath)
      self.saveFig.savefig(self.pdfPath + name + ".pdf", bbox_inches = "tight")
    plt.close(self.saveFig)
    plt.show()
