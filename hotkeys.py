from pynput import keyboard

press_keys:dict = {}
release_keys:dict = {}

def press(key:str, fnc):
  press_keys[key] = fnc
  
def release(key:str, fnc):
  release_keys[key] = fnc
  
def on_press(key):
  try:
    key = str(key).strip("'")
    if key in press_keys:
      press_keys[key]()
  except AttributeError:
    pass
  
def on_release(key):
  try:
    key = str(key).strip("'")
    if key in release_keys:
      release_keys[key]()
  except AttributeError:
    pass

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()