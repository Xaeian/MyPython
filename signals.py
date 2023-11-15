import numpy as np, pandas as pd, math
from scipy.signal import butter, lfilter, freqz

class Filter:

  @staticmethod
  def lowpass(lowcut, fs, order=6):
    nyq = fs / 2
    low = lowcut / nyq
    b, a = butter(order, low, btype='low')
    return b, a

  @staticmethod
  def bandpass(lowcut, highcut, fs, order=6):
    nyq = fs / 2
    low = lowcut / nyq
    high = highcut / nyq
    print(nyq, order, low, high)
    b, a = butter(order, [low, high], btype='band')
    return b, a

  @staticmethod
  def highpass(highcut, fs, order=5):
    nyq = fs / 2
    high = highcut / nyq
    b, a = butter(order, high, btype='high')
    return b, a

  def __init__(self, band:list|tuple|float=287.5, order:int=6, fs:int=6666):
    if type(band) is list or type(band) is tuple:
      lowcut, highcut = band
      self.b_band, self.a_band = Filter.bandpass(lowcut, highcut, fs, order)
    else:
      lowcut, highcut = band, band
    self.b_low, self.a_low = Filter.lowpass(lowcut, fs, order)
    self.b_high, self.a_high = Filter.highpass(highcut, fs, order)

  def lp(self, serie):
    return lfilter(self.b_low, self.a_low, serie)

  def bp(self, serie):
    return lfilter(self.b_band, self.a_band, serie)

  def hp(self, serie):
    return lfilter(self.b_high, self.a_high, serie)

  def freq_lp(self):
    w, h = freqz(self.b_low, self.a_low, worN=2000)
    f = (1000 / 2 / np.pi) * w
    modh = abs(h)
    return f, modh

  def freq_bp(self):
    w, h = freqz(self.b_band, self.a_band, worN=2000)
    f = (1000 / 2 / np.pi) * w
    modh = abs(h)
    return f, modh

  def freq_hp(self):
    w, h = freqz(self.b_high, self.a_high, worN=2000)
    f = (1000 / 2 / np.pi) * w
    modh = abs(h)
    return f, modh

def df_sum_series(df:pd.DataFrame) -> pd.DataFrame:
  dfs = df.copy()
  for i in range(1, len(df)):
    dfs[i] = dfs[i-1] + df[i]
  return dfs

def frequency_dist(freq, value, factor:float=0.5) -> float:
  fft = pd.DataFrame({"freq": freq, "value": value})
  fft["dist"] = df_sum_series(fft["value"])
  return freq[(fft.loc[lambda x: x["dist"] >= fft["value"].sum() * factor]).index[0]]

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
    self._filter = None

  def set_filter(self, band:list|tuple|float=287.5, order:int=6) -> None:
    self._filter = Filter(band, order, self.fs)

  def set_convert(self, bit_resolution, scale:float=0, g_range:float=0, withoutOffset:bool=True) -> None:
    self.scale = max(scale, g_range * 9.81) / 2**bit_resolution
    self.withoutOffset = withoutOffset

  def convert(self, df:pd.DataFrame) -> pd.DataFrame:
    if self.scale:
      df *= self.scale
    if self.withoutOffset:
      df -= df.mean()
    return df

  def append(self, df:pd.DataFrame) -> None:
    df = self.convert(df)
    for key, serie in df.items():
      self.series[key] = serie
      self.fft[key] = np.abs(np.fft.rfft(df[key] * np.hamming(self.count)))

  def filter(self, mode:str):
    sig = Signal(self.fs, self.t)
    df = pd.DataFrame()
    for key, serie in self.series.items():
      if mode == "HP":
        df[key] = self._filter.hp(serie)
      elif mode == "BP":
        df[key] = self._filter.bp(serie)
      elif mode == "LP":
        df[key] = self._filter.lp(serie)
    sig.append(df)
    return sig

  def integral(self):
    sig = Signal(self.fs, self.t)
    sig._filter = self._filter
    sig.withoutOffset = False
    df = pd.DataFrame()
    for key, serie in self.series.items():
      integral = []
      v0 = 0
      for value in serie.values:
        value = (value * (self.t / self.count)) + v0
        integral.append(value)
        v0 = value
      df[key] = np.array(integral)
      sig.append(df)
    return sig

  def derivative(self):
    sig = Signal(self.fs, self.t)
    sig._filter = self._filter
    sig.withoutOffset = False
    df = pd.DataFrame()
    for key, serie in self.series.items():
      df[key] = np.diff(serie.values)
    sig.append(df)

  def true_rms(self) -> float:
    rms = 0
    for _, serie in self.series.items():
      rms += serie.std()
    return rms

  def max_peak(self) -> float:
    max_peak = 0
    for _, serie in self.series.items():
      peak = serie.max() - serie.min()
      if peak > max_peak:
        max_peak = peak
    return max_peak

  def merge_fft(self) -> pd.DataFrame:
    fft = [0] * math.ceil(self.count / 2)
    for _, value in self.fft.items():
      fft += value
    return fft

  def dist_freq(self, factor:float=0.5) -> float:
    return frequency_dist(self.freq, self.merge_fft(), factor)

  def __mul__(self, other):
    if isinstance(other, Signal):
      for key, serie in self.series.items():
        serie *= other[key]
      pass
    else:
      for key, serie in self.series.items():
        serie *= other
    return self
