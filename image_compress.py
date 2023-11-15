from my import folder
from PIL import Image
import os

# pip install Pillow
# for e.g.
# img_compress(src="./image.jpg", prefix="compress-", scale=0.5, quality=30)

def img_compress(
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
  img.save(dsc, format, optimize=optimize, quality=quality)

def img_compress_catalog(
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
      img_compress(
        src=fsrc,
        dsc=fdsc,
        quality=quality,
        optimize=optimize,
        scale=scale,
        width=width,
        height=height
      )
  folder.exec_through(scr, dsc, fnc)