#!/usr/bin/python
# crontab -e
# INSERT THE FOLLOWING LINE:
# * * * * * python3 /home/pi/Desktop/MyProject/task.py > /home/pi/Desktop/MyProject/logs/log.txt

from interfaces import grovepiinterface, urlrequest
import json, time, datetime

grovepiinterface.set_digit_display_time_digitalport(4)

[temp,hum] = grovepiinterface.read_temp_humidity_sensor_digitalport(7)
dictofvalues = {"temp":temp,"hum":hum}
print(dictofvalues)

url = "https://nielbrad.pythonanywhere.com/uploadhistory"

response = urlrequest.sendurlrequest(url, dictofvalues)
dictofresults = json.loads(response)

led = dictofresults['led']
grovepiinterface.set_led_digitalport_value(3,led)