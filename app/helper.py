import network
import machine

try:
    import utime as time
except Exception as e:
    print(e)
    import time

import config

def deepsleep():
    print('Going into deepsleep for:', config.INTERVAL)
    rtc = machine.RTC()
    rtc.irq(trigger=rtc.ALARM0, wake=machine.DEEPSLEEP)
    rtc.alarm(rtc.ALARM0, config.INTERVAL * 1000)
    machine.deepsleep()

def is_debug():
    debug = machine.Pin(config.PIN_DICT[config.DEBUG_PIN], machine.Pin.IN, machine.Pin.PULL_UP)
    if debug.value() == 0:
        print('Debug mode detected.')
        return True
    return False

def connect_wifi():
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('Connecting to WiFi...')
        sta_if.active(True)
        sta_if.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        while not sta_if.isconnected():
            time.sleep(1)
    print('Network config:', sta_if.ifconfig())

def show_error():
    led = machine.Pin(config.PIN_DICT['LED1'], machine.Pin.OUT)
    led2 = machine.Pin(config.PIN_DICT['LED2'], machine.Pin.OUT)
    for i in range(3):
        led.on()
        led2.off()
        time.sleep(1)
        led.off()
        led2.on()
        time.sleep(1)
    led.on()
    led2.on()

def turn_off_pins():
    all_outputs = {}
    all_outputs.update(config.RELAYS)
    all_outputs.update(config.INTERMITTENTS)
    for k,v in all_outputs.items():
        pin = machine.Pin(config.PIN_DICT[v['pin']])
        pin.on()

def celsius_to_fahrenheit(c):
    return (c * 9/5) + 32