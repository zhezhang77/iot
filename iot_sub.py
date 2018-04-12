#!/usr/bin/python

import subprocess
import ssl
import time
import paho.mqtt.client as mqtt
import json
import threading
import re

from sense_hat import SenseHat

config_file = 'iot_sub.conf'

disp_type = 0
disp_type_max = 4
temperature = "0"
humidity = "0"
button = "N/A"
pressure = "0"
compass = "0"

def init():
    conf_str = open(config_file).read()
    return json.loads(conf_str)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

#
def on_disconnect(client, userdata, rc):
    print("Disconnected with result code "+str(rc))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    global temperature
    global humidity
    global button
    global pressure
    global compass
    
    #print(msg.topic+" "+str(msg.payload))#debug
    data = json.loads(msg.payload)
    #print(data) #debug

    m = re.search(r'(?<=/)\w+', msg.topic) 
    
    if m.group(0) == 'temperature':
        temperature = data['temperature']
    elif m.group(0) == 'humidity':
        humidity = data['humidity']
    elif m.group(0) == 'button':
        button = data['button']
    elif m.group(0) == 'pressure':
        pressure = data['pressure']
    elif m.group(0) == 'compass':
        compass = data['compass']
        
def on_log(client, userdata, level, buf):
    print("Debug %d: %s"%(level, buf))

def sense_display_info(sense):
    global temperature
    global humidity
    global button
    global pressure
    global compass
    
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

        if disp_type == 0:
            sense.show_message("T:"+temperature, text_colour=[255, 0, 0])
        elif disp_type == 1:
            sense.show_message("H:"+humidity, text_colour=[0, 0, 255])
        elif disp_type == 2:
            sense.show_message("B:"+button, text_colour=[0, 255, 0])
        elif disp_type == 3:
            sense.show_message("P:"+pressure, text_colour=[255, 255, 0])
        elif disp_type == 4:
            sense.show_message("C:"+compass, text_colour=[255, 0, 255])
        #else:
        #    sense.clear()
        time.sleep(1)

def main():
    global disp_type

    # Init
    conf = init()

    if (conf['type']=='sensehat'):
        sense = SenseHat()
        disp_thread = threading.Thread(target=sense_display_info, args=(sense,))    
    
    disp_thread.daemon = True
    disp_thread.start()

    client = mqtt.Client(conf['id'])

    client.tls_set( "./cert/CARoot.pem",
                    "./cert/"+conf['id']+"-certificate.pem.crt",
                    "./cert/"+conf['id']+"-private.pem.key",
                    cert_reqs=ssl.CERT_NONE,
                    tls_version=ssl.PROTOCOL_TLSv1_2)	

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    #client.on_log = on_log #debug

    client.connect(conf['entrypoint'], conf['port'], 60)

    client.subscribe("iot/+/"+conf['display'])

    running = True
    while running:
        client.loop()

        if (conf['type']=='sensehat'):
            for event in sense.stick.get_events():
                if ((event.direction == 'up') or (event.direction == 'down')) and (event.action == 'released'):
                    running = False
                elif ((event.direction == 'left') or (event.direction == 'right')) and (event.action == 'released'):
                    disp_type = disp_type + 1
                    if (disp_type > disp_type_max):
                        disp_type = 0

    client.disconnect()
    
    if (conf['type']=='sensehat'):
        sense.clear()

if __name__ == '__main__':
	main()
