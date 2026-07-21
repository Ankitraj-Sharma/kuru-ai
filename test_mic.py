import sounddevice as sd
import numpy as np

devices = sd.query_devices()
print(f"Total audio devices: {len(devices)}")
default_in = sd.query_devices(kind='input')
print(f"Default Input Device: {default_in['name']}")
