WIFI_SSID = 'speed_of_light'
WIFI_PASSWORD = '299792458'

INTERVAL = 15 * 1

HOST = 'localhost'
SENSOR_URL = 'http://{}:5000/api/sensor_readings'.format(HOST)
CONTROL_URL = 'http://{}:5000/api/control'.format(HOST)
AUTH_TOKEN = 'sam'

PIN_DICT = {
    'TX':1,
    'RX':3,
    'D0':16,
    'D1':5,
    'D2':4,
    'D3':0,
    'D4':2,
    'D5':14,
    'D6':12,
    'D7':13,
    'D8':15,
    'SD2':9,
    'SD3':10,
    'LED1':2,
    'LED2':16,
    'AO':17
}

DEBUG_PIN = 'SD2'

RELAYS = {
    'temperature': {'low': 25, 'high': 30, 'pin': 'D1'},
    'humidity': {'low': 85, 'high': 90, 'pin': 'D5'}

}

INTERMITTENTS = {
    'fan': {'on_mins': 5, 'off_mins': 55, 'pin': 'D2'}
}

