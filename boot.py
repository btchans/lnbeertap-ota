# This file is executed on every boot (including wake-boot from deepsleep)

from json import config
json = config("config/config.json")
import ugit
import time
import network

## connect to wifi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

ssid = json.GetContent("ssid")
pwd = json.GetContent("pwd")
# might already be connected somehow.
if wlan.isconnected() == False:
    wlan.connect(ssid, pwd)

while not wlan.isconnected():
    time.sleep(1)
    pass

ugit.pull_all(isconnected=True)