import grovepi
import grove_rgb_lcd
import datetime
import time
import urlrequest
from di_sensors.easy_mutex import ifMutexAcquire, ifMutexRelease 
from di_sensors.temp_hum_press import TempHumPress
import json

USEMUTEX = True #avoid threading issues

# ------------------------ DEVICES -----------------------------
# Turn on the led using digital port (1 or 0)
def set_led_digitalport_value(port,value=3):
    ifMutexAcquire(USEMUTEX)
    try:
        grovepi.pinMode(port,"OUTPUT") #should be in initialise
        grovepi.digitalWrite(port,value)
    except Exception as error:
        print('Problem with LED ' + repr(error))
    finally:
        ifMutexRelease(USEMUTEX)
    return

# Display the time. Needs to start a Thread
def set_digit_display_time_digitalport(port):
    grovepi.pinMode(port,"OUTPUT")
    grovepi.fourDigit_init(port)
    grovepi.fourDigit_on(port)
    grovepi.fourDigit_brightness(port,8)
    time.sleep(0.5)
    now = datetime.datetime.now()
    grovepi.fourDigit_score(port,now.hour,now.minute)
    return

# Display a number
def set_digit_display_number_digitalport(number,port):
    grovepi.pinMode(port,"OUTPUT")
    grovepi.fourDigit_init(port)
    grovepi.fourDigit_on(port)
    grovepi.fourDigit_brightness(port,8)
    grovepi.fourDigit_number(number)
    return

# OLED monitor - set_OLED_I2C1_RGBtuple_message((0,0,125),"It works!!")
def set_OLED_I2C1_RGBtuple_message(colour, message):   #colour is a tuple of (255,255,255)
    grove_rgb_lcd.setRGB(*colour) 
    grove_rgb_lcd.setText(message)
    return

# grove buzzer is turned on (1 or 0) - this is super annoying
def set_buzzer_digitalport(port, value=1):
    grovepi.pinMode(port,"OUTPUT")
    grovepi.digitalWrite(port,value)
    return

# ------------------------ SENSORS -----------------------------
# Read the distance using sound waves return centimeters (2-350cm)
def read_ultra_digitalport(port):
    grovepi.pinMode(port,"INPUT")
    distance = grovepi.ultrasonicRead(port)
    return distance 

# Read Button return 0 or 1 
def read_button_digitalport(port):
    grovepi.pinMode(port,"INPUT")
    distance = grovepi.digitalRead(port)
    return distance 

# Read temp (0 - 50 degrees Celsius) and humidity (20% - 90%)
def read_temp_humidity_sensor_digitalport(port):
    temp_humidity_list = grovepi.dht(port,0)
    return temp_humidity_list #[temp,hum] = read_temp_humidity_sensor_digitalport(4) - break into parts

# Read sound sensor returns analogue value 0 - 1023 loudness - to translate to decibels you need identify the distance
def read_sound_analogueport(port):
    sound = grovepi.analogRead(port)
    return sound

# Read light sensor returns analogue value 0 - 1023 - not sure how to translate into lux
def read_light_analogueport(port):
    light = grovepi.analogRead(port)
    return light

# read rotation sensor (Grove Rotary Angle Sensor) - can return voltage, degrees
def read_rotation_analogueport(port):
    adc_ref = 5 # Reference voltage of ADC is 5v
    grove_vcc = 5 # Vcc of the grove interface is normally 5v
    grovepi.pinMode(port,"INPUT")
    sensor_value = grovepi.analogRead(port)
    voltage = round((float)(sensor_value) * adc_ref / 1023, 2)
    degrees = round((voltage * 360) / grove_vcc, 2)
    data = [voltage,degrees]
    return data

#only execute the below block if this is the execution point
if __name__ == '__main__':
    [voltage,degrees] = read_rotation_analogueport(2)
    [temp,hum] = read_temp_humidity_sensor_digitalport(2)
    dictofvalues = {"temp":temp,"hum":hum}
    url = "https://nielbrad.pythonanywhere.com/uploadhistory"
    #url = "http://0.0.0.0:5000/handleurlrequest" #if server is running locally
    response = urlrequest.sendurlrequest(url, dictofvalues)
    print(response)
    dict = json.loads(response)
    set_led_digitalport_value(7,dict['led'])
    set_buzzer_digitalport(3, value=0)
    
