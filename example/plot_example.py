from turtle import up
import numpy as np
import scipy.stats as stats
from plot import Plot

data = []
time = []

opt = {
  "max": 100,
  "min": -100, # range = max - min
  "sigma": 0.3, # trueSigma = range * sigma
  "gain": 0.05 # # trueGain = range * gain
}

def normMinMax(y:np.array):
  maxY = max(y)
  minY = min(y)
  return (y - minY) / (maxY - minY)

r = opt["max"] - opt["min"]
u = opt["min"] + (r / 2)
sigma = r * opt["sigma"]
gain = r * opt["gain"]

x = np.arange(opt["min"], opt["max"], 0.1)
down = stats.norm.pdf(x, opt["min"], sigma)
up = stats.norm.pdf(x, opt["max"], sigma)
down = gain * normMinMax(down)
up = gain * normMinMax(up)

plot = Plot("x", "y")
plot.Add("down", x, down)
plot.Add("up", x, up)
plot.View()