import logging

"""
Displays logs in the console and saves to a file
https://github.com/Xaeian/
2023-09-13 12:00:00
"""

class LogFormatter(logging.Formatter):
  def format(self, record):
    if record.levelname == 'NOTSET': record.levelname = 'NONE'
    elif record.levelname == 'WARNING': record.levelname = 'WARN'
    elif record.levelname == 'CRITICAL': record.levelname = 'CRIT'
    return super().format(record)

def logger(file:str="", stream_lvl=logging.INFO, file_lvl=logging.INFO, stream:bool=True) -> logging.Logger:
  log = logging.getLogger()
  log.setLevel(logging.DEBUG)
  formatter = LogFormatter("%(asctime)s %(levelname)-5s %(message)s", "%Y-%m-%d %H:%M:%S")
  if stream:
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(stream_lvl)
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)
  if file:
    file_handler = logging.FileHandler(file, encoding="utf-8")
    file_handler.setLevel(file_lvl)
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)
  return log
