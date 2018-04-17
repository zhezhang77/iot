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
disp_data = {} # dict
disp_type = 0  # current display item num
running = True # control if program should exit

# Notify thread to exit when receive Ctrl-C from console
def handle_exit(signal, frame):
	global running
	print 'Ctrl+C pressed'
	running = False

# read config file
def init():
	conf_str = open(config_file).read()
	return json.loads(conf_str)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
	print('Connected with result code '+str(rc))

# The callback for when the client disconnect from the server.
def on_disconnect(client, userdata, rc):
	print('Disconnected with result code '+str(rc))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
	global disp_data

	#print(msg.topic+' '+str(msg.payload))#debug
	data = json.loads(msg.payload)
	#print(data) #debug

	m = re.search(r'(?<=/)\w+', msg.topic)

	disp_data[m.group(0)] = data[m.group(0)]

# Helper function
def on_log(client, userdata, level, buf):
	print('Debug %d: %s'%(level, buf))

# Increase disp_type when receiving specific event
def sense_inc_disp_type(event):
	global disp_type
	if event.action != ACTION_RELEASED:
		disp_type = disp_type + 1

# Color table for different type of data
color_table=[
	[255,0,0],
	[0,255,0],
	[0,0,255],
	[255,255,0],
	[255,0,255],
	[0,255,255],
	[255,255,255]]

# display data on sense hat
def sense_display_info(sense):
	global disp_data
	global disp_type
	global color_table
	global running

	while running:
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

		#time.sleep(1)
	sense.clear()

# display data on grovepi
def grove_display_info():
	global disp_data
	global disp_type
	global running

	light_down = 0

	curr_disp_type = -1
	setText('')
	setRGB(0,0,0)

	while running:
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

	setRGB(0,0,0)
	setText('')

# message thread function
def message_loop(client):
	global running

	while running:
		client.loop()
		time.sleep(1)

	client.disconnect()

def main():
	global running
	global disp_type

	# Set signal
	signal.signal(signal.SIGINT, handle_exit)

	# Read config file
	conf = init()

	# Init hardware
	if (conf['type']=='sensehat'):
		sense = SenseHat()

		# Bind display item switching to up/down/left/right button
		sense.stick.direction_up = sense_inc_disp_type
		sense.stick.direction_down = sense_inc_disp_type
		sense.stick.direction_left = sense_inc_disp_type
		sense.stick.direction_right = sense_inc_disp_type

		# Create display thread
		disp_thread = threading.Thread(target=sense_display_info, args=(sense,))
	elif (conf['type']=='grovepi'):
		# Set port mode
		pinMode(conf['light'],"INPUT")
		pinMode(conf['button'], "INPUT")
		grove_light = conf['light'] - 14
		grove_button = conf['button']
		# Create display thread
		disp_thread = threading.Thread(target=grove_display_info)

	# Start display thread
	disp_thread.daemon = False
	disp_thread.start()

	# Set connection
	client = mqtt.Client(conf['id'])
	client.tls_set( './cert/CARoot.pem',
					'./cert/'+conf['id']+'-certificate.pem.crt',
					'./cert/'+conf['id']+'-private.pem.key',
					cert_reqs=ssl.CERT_NONE,
					tls_version=ssl.PROTOCOL_TLSv1_2)

	# Set client callback
	client.on_connect = on_connect
	client.on_disconnect = on_disconnect
	client.on_message = on_message
	#client.on_log = on_log #debug

	# Connect to broker
	client.connect(conf['entrypoint'], conf['port'], 60)

	# Subscribe to topics
	client.subscribe('iot/+/'+conf['display'])

	# Create message thread
	mesg_thread = threading.Thread(target=message_loop, args=(client,))
	mesg_thread.daemon = False
	mesg_thread.start()

	# deal with input to toggle disp_type
	while running:
		if (conf['type']=='grovepi'):
			#button = digitalRead(grove_button)
			#if (button == 1):
			#    button_trigger = button_trigger + 1
			#else:
			#    button_trigger = 0
			#print('button:'+repr(button)+' '+repr(button_trigger))

			light = analogRead(grove_light)
			if (light < 50):
				light_trigger = light_trigger + 1
			else:
				light_trigger = 0
			#print('light:'+repr(light)+' '+repr(light_trigger))

			if (light_trigger == 1):
				disp_type = disp_type + 1
			#print("inc disp+type")
		else:
			pass

	time.sleep(1)

if __name__ == '__main__':
	main()
