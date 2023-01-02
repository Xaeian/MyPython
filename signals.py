from re import X
import numpy as np
import pandas as pd
import math
from pandas.core.base import PandasObject
from pandas.api.types import is_string_dtype

from scipy import integrate
from scipy.signal import butter, lfilter, freqz
from scipy.optimize import curve_fit
import pandas as pd
from datetime import datetime, timezone
import glob
import os

# ---------------------------------------------------------------------------------------

def df_rollo_median(df:pd.DataFrame, window:int, step:int):
  return df.rolling(window).median()[window - 1::step].reset_index(drop=True)

def df_rollo_mean(df:pd.DataFrame, window:int, step:int):
  return df.rolling(window).mean()[window - 1::step].reset_index(drop=True)

def df_rollo_max(df:pd.DataFrame, window:int, step:int):
  return df.rolling(window).max()[window - 1::step].reset_index(drop=True)

def df_rollo_min(df:pd.DataFrame, window:int, step:int):
  return df.rolling(window).min()[window - 1::step].reset_index(drop=True)

def df_rollo(df:pd.DataFrame, window:int, step:int, modes:dict):
  rollo = pd.DataFrame()
  for key, serie in df.iteritems():
    if modes[key] == "min":
      rollo[key] = serie.rollo_min(window, step)
    elif modes[key] == "mean":
      rollo[key] = serie.rollo_mean(window, step)
    elif modes[key] == "max":
      rollo[key] = serie.rollo_max(window, step)
    else:
      rollo[key] = serie.rollo_median(window, step)
  return rollo

def to_stamp(dt:str|datetime|pd.DataFrame, format="%Y-%m-%d %H:%M:%S"):
  if type(dt) == str or type(dt) == datetime:
    if type(dt) == str:
      dt = datetime.strptime(dt, format)
    return dt.replace(tzinfo=timezone.utc).timestamp()
  else:
    if is_string_dtype(dt):
      dt = pd.to_datetime(dt, format=format)
    return dt.values.astype("int64") // 10**9

def df_bool_convert(df:pd.DataFrame, limit:float):
  df = df.copy()
  df[df >= limit] = 1
  df[df < limit] = 0
  return df

def df_bool_filter(df:pd.DataFrame, stampName:str, valueName:str) -> pd.DataFrame:
  res = { stampName:[], valueName:[] }
  mem = None
  for stamp, value in zip(df[stampName], df[valueName]):
    if mem != value:
      res[stampName].append(stamp)
      res[valueName].append(value)
    mem = value
  return pd.DataFrame(res)

def df_bool_to_range(df:pd.DataFrame, stampName:str, valueName:str, min:float=120, state:int=1) -> list:
  res = []
  for i in range(1, len(df)):
    if state == df[valueName][i - 1] and df[stampName][i] - df[stampName][i - 1] >= min:
      res.append((df[stampName][i - 1], df[stampName][i]))
  return res

def df_sum_series(df:pd.DataFrame) -> pd.DataFrame:
  dfs = df.copy()
  for i in range(1, len(df)):
    dfs[i] = dfs[i-1] + df[i]
  return dfs

def df_sum_scale_series(df:pd.DataFrame, scale:pd.DataFrame) -> pd.DataFrame:
  dfs = df.copy()
  dfs[0] *= scale[0]
  for i in range(1, len(df)):
    dfs[i] = dfs[i-1] + (df[i] * scale[i])
  return dfs

def df_range_filter(df:pd.DataFrame, name:str, start:float, stop:float) -> pd.DataFrame:
  return df.loc[lambda x: x[name] >= start].loc[lambda x: x[name] < stop]

PandasObject.rollo_median = df_rollo_median
PandasObject.rollo_mean = df_rollo_mean
PandasObject.rollo_min = df_rollo_min
PandasObject.rollo_max = df_rollo_max
PandasObject.rollo = df_rollo
PandasObject.to_stamp = to_stamp
PandasObject.bool_convert = df_bool_convert
PandasObject.bool_filter = df_bool_filter
PandasObject.bool_to_range = df_bool_to_range
PandasObject.sum_series = df_sum_series
PandasObject.sum_scale_series = df_sum_scale_series
PandasObject.range_filter = df_range_filter

# --------------------------------------------------------------------------------------- DataCollector

class DataCollector:
  
  def __init__(self, *params:str):
    self.data = {}
    self.params = params
    self.Clear()
    
  def Clear(self):
    for param in self.params:
      self.data[param] = []
      
  def Append(self, *values:float):
    for param, value in zip(self.params, values):
      self.data[param].append(value)
      
  def DataFrame(self) -> pd.DataFrame:
    return pd.DataFrame(self.data)
  
# --------------------------------------------------------------------------------------- Loader

class Loader:
  
  @staticmethod
  def getDatatimeString(filePath):
    timestamp = int(os.path.basename(filePath).removesuffix(".csv"))
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")
  
  def __init__(self, path:str="./raw"):
    self.fileList = glob.glob(os.path.join(os.getcwd(), path, "*.csv"))
    self.fileCount = len(self.fileList)
    
  def getFile(self, index:int=0) -> pd.DataFrame:
    if index > self.fileCount:
      return "", pd.DataFrame()
    filePath = self.fileList[index]
    df = pd.read_csv(filePath, header=0)
    return df
  
  def getFiles(self, limit:int=0, offset:int=0) -> dict:
    dfs = {}
    if not limit:
      limit = self.fileCount
    offset = min(offset, self.fileCount)
    limit = min(limit, self.fileCount - offset)
    for i in range(offset, offset + limit):
      filePath = self.fileList[i]
      dt = self.getDatatimeString(filePath)
      dfs[dt] = pd.read_csv(filePath, header=0)
    return dfs

# --------------------------------------------------------------------------------------- Filter

class Filter:
  
  @staticmethod
  def Lowpass(lowcut, fs, order=6):
    nyq = fs / 2
    low = lowcut / nyq
    b, a = butter(order, low, btype='low')
    return b, a
  
  @staticmethod
  def Bandpass(lowcut, highcut, fs, order=6):
    nyq = fs / 2
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a
  
  @staticmethod
  def Highpass(highcut, fs, order=5):
    nyq = fs / 2
    high = highcut / nyq
    b, a = butter(order, high, btype='high')
    return b, a
  
  def __init__(self, band:list|tuple|float=287.5, order:int=6, fs:int=6666):
    if type(band) is list or type(band) is tuple:
      lowcut, highcut = band
    else:
      lowcut, highcut = band, band
    self.b_low, self.a_low = Filter.Lowpass(lowcut, fs, order)
    self.b_band, self.a_band = Filter.Bandpass(lowcut, highcut, fs, order)
    self.b_high, self.a_high = Filter.Highpass(highcut, fs, order)
    
  def LP(self, serie):
    return lfilter(self.b_low, self.a_low, serie)
  
  def BP(self, serie):
    return lfilter(self.b_band, self.a_band, serie)
  
  def HP(self, serie):
    return lfilter(self.b_high, self.a_high, serie)
  
  def FreqLP(self):
    w, h = freqz(self.b_low, self.a_low, worN=2000)
    f = (1000 / 2 / np.pi) * w
    modh = abs(h)
    return f, modh
  
  def FreqBP(self):
    w, h = freqz(self.b_band, self.a_band, worN=2000)
    f = (1000 / 2 / np.pi) * w
    modh = abs(h)
    return f, modh
  
  def FreqHP(self):
    w, h = freqz(self.b_high, self.a_high, worN=2000)
    f = (1000 / 2 / np.pi) * w
    modh = abs(h)
    return f, modh

# --------------------------------------------------------------------------------------- Signal

class Signal:
  def __init__(self, fs:int=6666, t:float=0.5) -> None:
    self.fs = fs
    self.t = t
    self.count = int(fs * t)
    self.time = np.arange(0, t, 1 / fs)
    self.series = pd.DataFrame()
    self.freq = np.fft.rfftfreq(self.count, 1 / fs) 
    self.fft = pd.DataFrame()
    self.scale = 0
    self.withoutOffset = True
  
  def setFilter(self, band:list|tuple|float=287.5, order:int=6) -> None:
    self.filter = Filter(band, order, self.fs)

  def setConvert(self, bit_resolution, scale:float=0, g_range:float=0, withoutOffset:bool=True) -> None:
    self.scale = max(scale, g_range * 9.81) / 2**bit_resolution
    self.withoutOffset = withoutOffset
  
  def Convert(self, df:pd.DataFrame) -> pd.DataFrame:
    if self.scale:
      df *= self.scale
    if self.withoutOffset:
      df -= df.mean()
    return df
  
  def Append(self, df:pd.DataFrame) -> None:
    df = self.Convert(df)
    for key, serie in df.iteritems():
      self.series[key] = serie
      self.fft[key] = np.abs(np.fft.rfft(df[key] * np.hamming(self.count)))
  
  def Filter(self, mode:str):
    sig = Signal(self.fs, self.t)
    df = pd.DataFrame()
    for key, serie in self.series.iteritems():
      if mode == "HP":
        df[key] = self.filter.HP(serie)
      elif mode == "BP":
        df[key] = self.filter.BP(serie)
      elif mode == "LP":
        df[key] = self.filter.LP(serie)
    sig.Append(df)
    return sig
  
  def Integral(self):
    sig = Signal(self.fs, self.t)
    sig.withoutOffset = False
    df = pd.DataFrame()
    for key, serie in self.series.iteritems():
      integral = []
      v0 = 0
      for value in serie.values:
        value = (value * (self.t / self.count)) + v0
        integral.append(value)
        v0 = value
      df[key] = np.array(integral)
      sig.Append(df)
    return sig
  
  def TrueRMS(self) -> float:
    rms = 0
    for key, serie in self.series.iteritems():
      rms += serie.std()
    return rms
  
  def MaxPeak(self) -> float:
    max_peak = 0
    for key, serie in self.series.iteritems():
      peak = serie.max() - serie.min()
      if peak > max_peak:
        max_peak = peak
    return max_peak
  
  def MergeFFT(self) -> pd.DataFrame:
    fft = [0] * math.ceil(self.count / 2)
    for key, value in self.fft.iteritems():
      fft += value
    return fft
  
  def DistFreq(self, factor:float=0.5) -> float:
    return frequency_dist(self.freq, self.MergeFFT(), factor)
    
# ---------------------------------------------------------------------------------------

# Zwracana jest częstotliwość, dla której procentowa wartość sumy widma
# przekroczy wskaźnik 'factor'
def frequency_dist(freq, value, factor:float=0.5) -> float:
  fft = pd.DataFrame({"freq": freq, "value": value})
  fft["dist"] = fft["value"].sum_series()
  return freq[(fft.loc[lambda x: x["dist"] >= fft["value"].sum() * factor]).index[0]]

# Wyciąga z przebiegu FFT:
# - kolejne najbardziej znaczące składowe częstotliwości widma 'freq:list'
# - wraz z ich wartości 'value:list'
def frequency_picker(freq, value, count:int=3, roll:int=3, scale:float=0, offset:float=0) -> list:
  fft = pd.DataFrame({"freq": freq, "value": value})
  fft["roll"] = fft["value"].rolling(window=roll).max().rolling(window=roll).median()
  mem, peaks = 0, []
  rise = True
  for i, value in fft["roll"].iteritems():
    if value > mem:
      rise = True
      mem = value
    elif value < mem:
      if rise:
        peaks.append(mem)
      rise = False
    mem = value
  freq, value = [], []
  peakMax = max(peaks)
  for i in range(count):
    peakValue = max(peaks)
    index = list(fft["value"]).index(peakValue)
    if(peakValue >= scale * peakMax + offset):
      freq.append(fft["freq"][index])
      value.append(peakValue)
      peaks.remove(peakValue)
    else:
      break  
  return freq, value

# ---------------------------------------------------------------------------------------

def curve_steady_state(x:np.array, a:float=0, b:float=0, c:float=1, d:float=1) -> float:
  return (a * np.log(x + c) / (x + d)) + b

def steady_state_value(x, y) -> float|None:
  x, y = np.array(x), np.array(y)
  x = np.array(x - x[0])
  try:
    popt, _ = curve_fit(curve_steady_state, x, y, p0=(0, 0, 1, 1))
    a, b, c, d = popt
    return b
  except:
    return None