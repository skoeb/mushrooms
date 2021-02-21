import config

import dht
import network
import machine
import time
import sys
import json
import config

def run():
    led = machine.Pin(config.PIN_DICT['LED1'], machine.Pin.OUT)
    led2 = machine.Pin(config.PIN_DICT['LED2'], machine.Pin.OUT)
    power_pin = machine.Pin(config.PIN_DICT['D3'], mode=machine.Pin.OUT)
    while True:
        led.on()
        power_pin.on()
        led2.off()
        time.sleep(5)
        led.off()
        power_pin.off()
        led2.on()
        time.sleep(5)

run()
