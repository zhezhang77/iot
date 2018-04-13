# iot
**IoT example (GrovePi+/SenseHat)**

# Running
+ Use 'git clone' to get the whole folder to local
+ Run 'set_sense.sh' or 'set_grove.sh' accroding your Pi
+ Run 'iot_pub.py' to publish data
+ Run 'iot_sub.py' to subscribe and display data

# Program
* iot_pub.py  
  + Publish sensor data to AWS broker.  
  + Press Ctrl+C on console to exit the program
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
  + Press joystick **up/down** to exit the program (SenseHat)
  + Press Ctrl+C on console to exit the program

# TLS certificates
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
