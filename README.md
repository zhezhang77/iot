# iot
**IoT example (GrovePi+/SenseHat)**   

# Library Required
+ Sense Hat ( included in RASPBIAN STRETCH 2018-03-13 )
  ```sh
  sudo apt-get install sense-hat 
  ```
+ GrovePi
  ```sh
  sudo curl -kL dexterindustries.com/update_grovepi | bash
  sudo reboot
  ```
+ Paho
  ```sh
  sudo pip install paho-mqtt
  ```   
  
# Running
+ Use 'git clone' to get the whole folder to local
+ Run 'set_sense.sh' or 'set_grove.sh' accroding the type your sensor board
+ Run 'iot_pub.py' to publish data
  - The status of middle button of joystick will be published (Sense Hat)
+ Run 'iot_sub.py' to subscribe and display data
  - Use Up, Down, Left or Right to switch displayed info (Sense Hat)
  - Cover light sensor to switch displayed info (GrovePi+)   
+ Press Ctrl+C on console to exit the program   

# Code
* iot_pub.py  
  + Publish sensor data to AWS broker.  
  + **Topic:** 
  ```c
    iot/temperature/client_id     (GrovePi+/SenseHat)
    iot/humidity/client_id        (GrovePi+/SenseHat)
    iot/button/client_id          (GrovePi+/SenseHat)
    iot/rotary/client_id          (GrovePi+)
    iot/pressure/client_id        (SenseHat)
    iot/compass/client_id         (SenseHat)
    ...
  ```
* iot_sub.py  
  + Subscribe to iot/+/<display id> to receive data from specific client
  
# TLS certificates
All certificates should be placed in **cert** folder.  
<html><table>
<tr><td> CARoot.pem </td><td> CA file </td></tr>
<tr><td> **********-certificate.pem.crt </td><td> Client Certificate file </td></tr>
<tr><td> **********-public.pem.key </td><td> Client Public Key (unused for client) </td></tr> 
<tr><td> **********-private.pem.key </td><td> Client Private Key </td></tr>
</table></html>   

# Broker Info
<html><table>
<tr><td> Server </td><td> a1zd8y5etgd1ze.iot.ap-northeast-1.amazonaws.com  </td></tr>
<tr><td> Port </td><td> 8883 </td></tr>
</table></html>   

# MQTT.fx Settings
![MQTT.fx Settings](https://github.com/zhezhang77/iot/blob/master/mqttfx_setting.PNG)
