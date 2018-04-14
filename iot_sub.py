#!/usr/bin/python

import subprocess
import ssl
import time
import paho.mqtt.client as mqtt
import json
import threading
import re
import signal

from sense_hat import SenseHat, ACTION_RELEASED

from grovepi import *
from grove_rgb_lcd import *

config_file = 'iot_sub.conf'
disp_data = {}
disp_type = 0
running = True
grove_light = 0

def handle_exit(signal, frame):
    global running
    print 'Ctrl+C pressed'
    running = False

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

def inc_disp_type(event):
    global disp_type
    if event.action != ACTION_RELEASED:
        disp_type = disp_type + 1
        
color_table=[
    [255,0,0],
    [0,255,0],
    [0,0,255],
    [255,255,0],
    [255,0,255],
    [0,255,255],
    [255,255,255]]

def sense_display_info(sense):
    global disp_data
    global disp_type
    global color_table
    
    while True:
        # Rotation check
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
            
        if (len(disp_data) > 0):
            if (disp_type >= len(disp_data)):
                disp_type = 0

            name = disp_data.keys()[disp_type]
            value = disp_data[name]
            sense.show_message(name+':'+value, text_colour=color_table[disp_type % len(color_table)])

        time.sleep(1)

def grove_display_info():
    global disp_data
    global disp_type
    global grove_light
    
    light_down = 0
    
    curr_disp_type = -1
    setText('')
    setRGB(0,0,0)
    
    while True:
        light = analogRead(grove_light)
        #print(light)
        if (light < 50):
            light_down = light_down + 1
        else:
            light_down = 0
        
        #print("light_down="+repr(light_down))
        if (light_down == 1):
            disp_type = disp_type + 1
                
        if (len(disp_data) > 0):
            if (disp_type >= len(disp_data)):
                disp_type = 0
                
            name = disp_data.keys()[disp_type]
            value = disp_data[name]
            disp_str = name + ': ' + value
        else:
            disp_str = '> No data'
        
        if (curr_disp_type != disp_type):
            curr_disp_type = disp_type
            setRGB(color_table[disp_type][0],
                   color_table[disp_type][1],
                   color_table[disp_type][2])
        setText_norefresh(disp_str)
        time.sleep(1)
        
def main():
    global running
    global disp_type
    global grove_light
    
    signal.signal(signal.SIGINT, handle_exit)
    
    # Init
    conf = init()

    if (conf['type']=='sensehat'):
        sense = SenseHat()
        sense.stick.direction_up = inc_disp_type
        sense.stick.direction_down = inc_disp_type
        sense.stick.direction_left = inc_disp_type
        sense.stick.direction_right = inc_disp_type
        
        disp_thread = threading.Thread(target=sense_display_info, args=(sense,))    
    elif (conf['type']=='grovepi'):
        pinMode(conf['light'],"INPUT")
        grove_light = conf['light'] - 14
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

    while running:
        client.loop()
        
    client.disconnect()
    
    if (conf['type']=='sensehat'):
        sense.clear()
    elif (conf['type']=='grovepi'):
        setRGB(0,0,0)
        setText('')
        
if __name__ == '__main__':
	main()
