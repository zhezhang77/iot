#!/usr/bin/python

import subprocess
import ssl
import time
import paho.mqtt.client as mqtt
import json
import signal

from grovepi import *
from sense_hat import SenseHat

config_file = 'iot_pub.conf'
running = True

def handle_exit(signal, frame):
    global running
    print 'Ctrl+C pressed'
    running = False
    
def init():
    conf_str = open(config_file).read()
    #print(conf_str)
    return json.loads(conf_str)

def sense_get_temperature(sense):
    temp = sense.get_temperature()
    cpu_temp = subprocess.check_output("vcgencmd measure_temp", shell=True)
    array = cpu_temp.split("=")
    array2 = array[1].split("'")
    cpu_tempf = float(array2[0])
    temp_calibrated = temp - ((cpu_tempf - temp)/2)

    #print('CPU_TEMP = ' + repr(cpu_tempf)) #debug
    #print('OLD_TEMP = ' + repr(temp)) #debug
    #print('NEW_TEMP = ' + repr(temp_calibrated)) #debug

    return float("{0:.1f}".format(temp_calibrated))

def sense_get_humidity(sense):
    return float("{0:.1f}".format(sense.get_humidity()))

def sense_get_pressure(sense):
    return float("{0:.0f}".format(sense.get_pressure()))

def sense_get_compass(sense):
    return float("{0:.0f}".format(sense.get_compass()))

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    # client.subscribe("$SYS/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

def on_log(client, userdata, level, buf):
    print("Debug %d: %s"%(level, buf))

def gen_payload(id, name, value):
    data = {}
    data['id'] = id
    data['time'] = time.time()
    data[name] = value
    return json.dumps(data)

def gen_topic(id, name):
    return("iot/"+name+'/'+id)

def publish(client, id, name, value):
    client.publish(gen_topic(id, name), gen_payload(id, name, value))

def main():
    global running
    
    signal.signal(signal.SIGINT, handle_exit)
    
    # Init
    conf = init()
        
    client = mqtt.Client(conf['id'])

    client.tls_set( "./cert/CARoot.pem",
                    "./cert/"+conf['id']+"-certificate.pem.crt",
                    "./cert/"+conf['id']+"-private.pem.key",
                    cert_reqs=ssl.CERT_NONE,
                    tls_version=ssl.PROTOCOL_TLSv1_2)

    client.on_connect = on_connect
    client.on_message = on_message
    #client.on_log = on_log #debug

    client.connect(conf['entrypoint'], conf['port'], 60)
        
    if (conf['type']=='sensehat'):
        sense = SenseHat()
        sense.set_imu_config(True, False, False) #Campass Only
    elif (conf['type']=='grovepi'):
        pinMode(conf['button'],"INPUT")
	pinMode(conf['potentiometer'],"INPUT")
	time.sleep(1)
	
    #Publish
    while running:
        if (conf['type']=='sensehat'):
            time.sleep(1)
            publish(client, conf['id'], "temperature", repr(sense_get_temperature(sense)))
            publish(client, conf['id'], "humidity",    repr(sense_get_humidity(sense)))
            publish(client, conf['id'], "pressure",    repr(sense_get_pressure(sense)))
            publish(client, conf['id'], "compass",     repr(sense_get_compass(sense)))
            
            eventList = sense.stick.get_events()
            for event in eventList[::-1]:
                if (event.direction == 'middle'):
                    publish(client, conf['id'], "button", event.action)
                    break
        elif (conf['type']=='grovepi'):
            [temp,hum] = dht(conf['dht_port'], conf['dht_type'])
	    button = digitalRead(conf['button'])
	    time.sleep(1)
 	    potentiometer = analogRead(conf['potentiometer'])
 	    publish(client, conf['id'], "temperature",   repr(temp))
            publish(client, conf['id'], "humidity",      repr(hum))
            publish(client, conf['id'], "button",        repr(button))
            publish(client, conf['id'], "potentiometer", repr(potentiometer))
            
    #Disconnect
    client.disconnect()

if __name__ == '__main__':
    main()
