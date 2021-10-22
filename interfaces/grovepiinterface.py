import grovepi
import grove_rgb_lcd
import datetime
import time
try:
    import urlrequest                    
except ImportError: #could be being called from flask file
    pass #must be trying to run from the web server.
from di_sensors.easy_mutex import ifMutexAcquire, ifMutexRelease 
from di_sensors.temp_hum_press import TempHumPress
import json

USEMUTEX = True #avoid threading issues

# ------------------------ DEVICES -----------------------------
# Turn on the led using digital port (1 or 0)
def set_led_digitalport_value(port,value=1):
    ifMutexAcquire(USEMUTEX) #if calling functions from a web server, we need to be careful of threads
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
    now = datetime.datetime.now()
    grovepi.fourDigit_score(port,now.hour,now.minute)
    return

# Display a number
def set_digit_display_number_digitalport(number,port):
    leading_zero = 0
    grovepi.pinMode(port,"OUTPUT")
    grovepi.fourDigit_init(port)
    grovepi.fourDigit_on(port)
    grovepi.fourDigit_brightness(port,8)
    grovepi.fourDigit_number(port,number,leading_zero)
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
    time.sleep(0.03)
    return distance 

# Read water flow sensor
def read_waterflow_digitalport(port):
    period = 2000
    grovepi.flowEnable(port,period)
    waterflow = grovepi.flowRead()
    #THIS MAY NEED TO RUN OVER 10 SECONDS TO GET A PROPER WATER FLOW
    grovepi.flowDisable()
    return waterflow

# Read the PH Level
def read_ph_analogueport(port):
    adc_ref = 5 #Reference voltage of ADC is 5v
    grovepi.pinMode(port,"INPUT")
    sensor_value = grovepi.analogRead(port)
    ph = 7 - 1000 * (float)(sensor_value) * adc_ref / 59.16 / 1023
    return ph

# Read Button return 0 or 1 
def read_button_digitalport(port):
    grovepi.pinMode(port,"INPUT")
    distance = grovepi.digitalRead(port)
    return distance 

# Read temp (0 - 50 degrees Celsius) and humidity (20% - 90%)
def read_temp_humidity_sensor_digitalport(port):
    grovepi.pinMode(port,"INPUT")
    temp_humidity_list = grovepi.dht(port,0)
    return temp_humidity_list #[temp,hum] = read_temp_humidity_sensor_digitalport(4) - break into parts

# Read sound sensor returns analogue value 0 - 1023 loudness - to translate to decibels you need identify the distance
def read_sound_analogueport(port):
    grovepi.pinMode(port,"INPUT")
    sound = grovepi.analogRead(port)
    return sound

# Read the moisture sensor
def read_moisture_analogueport(port):
    grovepi.pinMode(port,"INPUT")
    moisture = grovepi.analogRead(port)
    return moisture

# Read light sensor returns analogue value 0 - 1023 - not sure how to translate into lux
def read_light_analogueport(port):
    grovepi.pinMode(port,"INPUT")
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

# --------------------------------------------------------------------------------
# an example of how to send data to the server.
def send_data_to_server():
    [temp,hum] = read_temp_humidity_sensor_digitalport(7)
    dictofvalues = {"temp":temp,"hum":hum}
    print(dictofvalues)
    url = "https://nielbrad.pythonanywhere.com/uploadhistory"
    #url = "http://0.0.0.0:5000/handleurlrequest" #if server is running locally
    response = urlrequest.sendurlrequest(url, dictofvalues)
    print(response)
    resultsdict = json.loads(response)
    #set_OLED_I2C1_RGBtuple_message((255,0,0), resultsdict['message'])
    return

# ---------------------------------------------------------------------------------
#only execute the below block if this is the execution point
if __name__ == '__main__':
    send_data_to_server()
    