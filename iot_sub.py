#!/usr/bin/python

import subprocess
import ssl
import time
import paho.mqtt.client as mqtt
import json
import threading
import re

from sense_hat import SenseHat

from grovepi import *
from grove_rgb_lcd import *

config_file = 'iot_sub.conf'
disp_data={}


def init():
    conf_str = open(config_file).read()
    return json.loads(conf_str)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print('Connected with result code '+str(rc))

#
def on_disconnect(client, userdata, rc):
    print('Disconnected with result code '+str(rc))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global temperature
    global humidity
    global button
    global pressure
    global compass
    global potentiometer
    
    #print(msg.topic+' '+str(msg.payload))#debug
    data = json.loads(msg.payload)
    #print(data) #debug

    m = re.search(r'(?<=/)\w+', msg.topic) 
    
    disp_data[m.group(0)] = data[m.group(0)]
    
# Helper function        
def on_log(client, userdata, level, buf):
    print('Debug %d: %s'%(level, buf))

def sense_display_info(sense):
    global disp_data

    while True:
        x, y, z = sense.get_accelerometer_raw().values()
        x = round(x, 0)
        y = round(y, 0)
        if x == -1:
            sense.set_rotation(180)
        elif y == -1:
            sense.set_rotation(90)
        elif y == 1:
            sense.set_rotation(270)
        else:
            sense.set_rotation(0)

        for [name, value] in disp_data.items():
            sense.show_message(name+':'+value+' ', text_coloyr=[0,255,0])

        time.sleep(1)

def grove_display_info():
    global disp_data
    
    setText('')
    setRGB(0,255,0)
    
    while True:
        disp_str = '>>>'
        for [name, value] in disp_data.items():
            disp_str = disp_str + " " + name + ':' + value
        for i in range(len(disp_str)):
            setText_norefresh(disp_str[i:])
            time.sleep(0.5)
        
def main():
    # Init
    conf = init()

    if (conf['type']=='sensehat'):
        sense = SenseHat()
        disp_thread = threading.Thread(target=sense_display_info, args=(sense,))    
    elif (conf['type']=='grovepi'):
        disp_thread = threading.Thread(target=grove_display_info)
        
    disp_thread.daemon = True
    disp_thread.start()

    client = mqtt.Client(conf['id'])

    client.tls_set( './cert/CARoot.pem',
                    './cert/'+conf['id']+'-certificate.pem.crt',
                    './cert/'+conf['id']+'-private.pem.key',
                    cert_reqs=ssl.CERT_NONE,
                    tls_version=ssl.PROTOCOL_TLSv1_2)	

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    #client.on_log = on_log #debug

    client.connect(conf['entrypoint'], conf['port'], 60)

    client.subscribe('iot/+/'+conf['display'])

    running = True
    while running:
        client.loop()

        if (conf['type']=='sensehat'):
            for event in sense.stick.get_events():
                if ((event.direction == 'up') or (event.direction == 'down')) and (event.action == 'released'):
                    running = False

    client.disconnect()
    
    if (conf['type']=='sensehat'):
        sense.clear()
    elif (conf['type']=='grovepi'):
        setRGB(0,0,0)
        setText('')
        
if __name__ == '__main__':
	main()
