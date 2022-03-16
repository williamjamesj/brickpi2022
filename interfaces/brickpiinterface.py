#To contract or expand sections use Control K and then Control 0
try:
    import brickpi3 # import the BrickPi3 drivers
    from di_sensors.easy_mutex import ifMutexAcquire, ifMutexRelease 
    from di_sensors.inertial_measurement_unit import InertialMeasurementUnit
    from di_sensors.temp_hum_press import TempHumPress
except ImportError:
    print("BrickPi not installed") #module not found
    
import time, math, sys, logging, threading

MAGNETIC_DECLINATION = 11 #set for different magnetic fields based on location
USEMUTEX = True #avoid threading issues

class SensorStatus():
    ENABLED = 1
    DISABLED = 5 #number of attempts before disabled
    NOREADING = 999 #just using 999 to represent no reading

#Created a Class to wrap the robot functionality, one of the features is the idea of keeping track of the CurrentCommand, this is important when more than one process is running...
class BrickPiInterface():

    #Initialise timelimit and logging
    def __init__(self, timelimit=20, logger=logging.getLogger()):
        self.logger = logger
        self.CurrentCommand = "loading"
        self.Configured = False #is the robot yet Configured?
        self.BP = None
        try:
            self.BP = brickpi3.BrickPi3() # Create an instance of the BrickPi3
            self.config = {} #create a dictionary that represents if the sensor is Configured
            self.timelimit = timelimit #fail safe timelimit - motors turn off after timelimit
            self.imu_status = 0; self.Calibrated = False
            self.thread_running = False
            self.CurrentCommand = "stop" #when the device is ready for a new instruction it 
        except (ImportError, NameError) as E:
            print(E)
            self.BP = "Give up all hope."
        return

    #------------------- Initialise Ports ---------------------------
    # motorports = {'rightmotor':bp.PORT_A,'leftmotor':bp.PORT_D,'mediummotor':bp.PORT_B }
    # sensorports = { 'thermal':bp.PORT_3,'colour':bp.PORT_2,'ultra':bp.PORT_1,'imu':1 }
    # if some ports do not exist, set as disabled
    # this will take 3-4 seconds to initialise
    def configure_sensors(self, motorports=None, sensorports=None):
        bp = self.BP
        if motorports == None:
            motorports = {'rightmotor':bp.PORT_A, 'leftmotor':bp.PORT_D, 'mediummotor':bp.PORT_B }
        if sensorports == None:
            sensorports = { 'thermal':bp.PORT_3,'colour':bp.PORT_2,'ultra':bp.PORT_1,'imu':1 }
        self.thread_running = False #end thread if its still running
        self.rightmotor = motorports['rightmotor']
        self.leftmotor = motorports['leftmotor']
        self.largemotors = motorports['rightmotor'] + motorports['leftmotor']
        self.mediummotor = motorports['mediummotor']

        #setup colour sensor
        self.config['colour'] = SensorStatus.DISABLED; self.colour = None
        if 'colour' in sensorports:
            self.colour = sensorports['colour']
            if self.colour:
                try:
                    bp.set_sensor_type(self.colour, bp.SENSOR_TYPE.EV3_COLOR_COLOR)
                    time.sleep(1)
                    self.config['colour'] = SensorStatus.ENABLED #SensorStatus.ENABLED
                except Exception as error:
                    self.log("Cannot initialise Color Sensor")

        #set up ultrasonic
        self.config['ultra'] = SensorStatus.DISABLED; self.ultra = None
        if 'ultra' in sensorports:    
            self.ultra = sensorports['ultra']
            if self.ultra:
                try:
                    bp.set_sensor_type(self.ultra, bp.SENSOR_TYPE.EV3_ULTRASONIC_CM)
                    time.sleep(1.2)
                    self.config['ultra'] = SensorStatus.ENABLED
                except Exception as error:
                    self.log("Cannot initialise Ultra Sonic Sensor")

        #set up imu
        self.config['imu'] = SensorStatus.DISABLED; self.imu = None
        if 'imu' in sensorports:  
            self.imu = sensorports['imu']   
            if self.imu:    
                try:
                    self.imu = InertialMeasurementUnit()
                    time.sleep(0.5)
                    self.config['imu'] = SensorStatus.ENABLED
                except Exception as error:
                    self.log("Cannot initialise IMU Sensor now trying to reconfig")
                    self.reconfig_IMU()

        #set up thermal - thermal sensor uses a thread because else it disables motors
        self.config['thermal'] = SensorStatus.DISABLED; self.thermal = None
        if 'thermal' in sensorports: 
            self.thermal = sensorports['thermal']
            if self.thermal != None:
                try:
                    bp.set_sensor_type(self.thermal, bp.SENSOR_TYPE.I2C, [0, 20])
                    time.sleep(1)
                    self.config['thermal'] = SensorStatus.ENABLED
                except Exception as error:
                    self.log("Cannot initialise Thermal Sensor")
                    bp.set_sensor_type(self.thermal, bp.SENSOR_TYPE.NONE)
            if self.config['thermal'] == SensorStatus.ENABLED:
                self.get_thermal_sensor() #do one read
                if self.config['thermal'] < SensorStatus.DISABLED:
                    self.log("BRICKPIINTERFACE: Starting thermal sensor thread")
                    self.__start_thermal_infrared_thread() #thread is started
                else:
                    bp.set_sensor_type(self.thermal, bp.SENSOR_TYPE.NONE)

        bp.set_motor_limits(self.mediummotor, 100, 600) #set power / speed limit 
        self.Configured = True #there is a 4 second delay - before robot is Configured
        return

    #-- Start Infrared I2c Thread ---------#
    def __start_thermal_infrared_thread(self):
        if self.thread_running: #thread is already running
            return
        self.thread_running = True
        self.thermal_thread = threading.Thread(target=self.__update_thermal_sensor_thread, args=(1,))
        self.thermal_thread.daemon = True
        self.thermal_thread.start()
        return

    #changes the logger
    def set_log(self, logger):
        self.logger=logger
        return

    #-----------SENSOR COMMAND----------------#
    #get the current voltage - need to work out how to determine battery life
    def get_battery(self):
        return self.BP.get_voltage_battery()

    #You need to calibrate the IMU for the compass to work!!!!
    def calibrate_imu(self, timelimit=20):
        if self.config['imu'] >= SensorStatus.DISABLED or not self.Configured:
            return
        self.stop_all() #stop everything while calibrating...
        self.CurrentCommand = "calibrate_imu"
        self.log("Move around the robot to calibrate the Compass Sensor...")
        self.imu_status = 0
        elapsed = 0; start = time.time()
        timelimit = start + timelimit #maximum of 20 seconds to calibrate compass sensor

        while self.imu_status != 3 and time.time() < timelimit:
            newtime = time.time()
            newelapsed = int(newtime - start)
            if newelapsed > elapsed:
                elapsed = newelapsed
                self.log("Calibrating IMU. Status: " + str(self.imu_status) + " Time: " + str(elapsed))
            ifMutexAcquire(USEMUTEX)
            try:
                self.imu_status = self.imu.BNO055.get_calibration_status()[3]
                self.config['imu'] = SensorStatus.ENABLED
                time.sleep(0.01)
            except Exception as error:
                self.log("IMU Calibration Error: " + str(error))
                self.config['imu'] += 1
            finally:
                ifMutexRelease(USEMUTEX)
        self.stop_all()
        if self.imu_status == 3:
            self.log("IMU Compass Sensor has been calibrated")
            self.Calibrated = True
            return "IMU Compass Sensor has been calibrated"
        else:
            self.Calibrated = False
            self.log("Calibration unsuccessful. Please rotate in 3 dimensions")
            return "Calibration unsuccessful. Please rotate in 3 dimensions"
        return

    #hopefully this is an emergency reconfigure of the IMU Sensor
    def reconfig_IMU(self):
        ifMutexAcquire(USEMUTEX)
        try:
            self.imu.BNO055.i2c_bus.reconfig_bus()
            time.sleep(0.1) #restabalise the sensor
            self.config['imu'] = SensorStatus.ENABLED
        except Exception as error:
            self.log("IMU RECONFIG HAS FAILED " + str(error))
            self.config['imu'] = SensorStatus.DISABLED
        finally:
            ifMutexRelease(USEMUTEX)
        return

    # Returns the compass value from the IMU sensor - note if the IMU is placed near a motor it can be affected -SEEMS TO RETURN A VALUE BETWEEN -180 and 180. 
    # It also helps to calibrate the compass before use.
    def get_compass_IMU(self):
        heading = SensorStatus.NOREADING
        if self.config['imu'] >= SensorStatus.DISABLED:
            return heading
        ifMutexAcquire(USEMUTEX)
        try:
            (x, y, z)  = self.imu.read_magnetometer()
            time.sleep(0.01)
            self.config['imu'] = SensorStatus.ENABLED
            heading = int(math.atan2(x, y)*(180/math.pi)) + MAGNETIC_DECLINATION 
            #make it 0 - 360 degrees
            if heading < 0:
                heading += 360
            elif heading > 360:
                heading -= 360
        except Exception as error:
            self.log("IMU: " + str(error))
            self.config['imu'] += 1
        finally:
            ifMutexRelease(USEMUTEX)
        return heading

    #returns the absolute orientation value using euler rotations, I think this is calilbrated from the compass sensor and therefore requires calibration
    def get_orientation_IMU(self):
        readings = (SensorStatus.NOREADING,SensorStatus.NOREADING,SensorStatus.NOREADING)
        if self.config['imu'] >= SensorStatus.DISABLED:
            return readings
        ifMutexAcquire(USEMUTEX)
        try:
            readings = self.imu.read_euler()
            time.sleep(0.01)
            self.config['imu'] = SensorStatus.ENABLED
        except Exception as error:
            self.log("IMU Orientation: " + str(error))
            self.config['imu'] += 1
        finally:
            ifMutexRelease(USEMUTEX)
        return readings  
    
    #returns the acceleration from the IMU sensor - could be useful for detecting collisions or an involuntary stop
    def get_linear_acceleration_IMU(self):
        readings = (SensorStatus.NOREADING,SensorStatus.NOREADING,SensorStatus.NOREADING)
        if self.config['imu'] >= SensorStatus.DISABLED:
            return readings
        ifMutexAcquire(USEMUTEX)
        try:
            #readings = self.imu.read_accelerometer()
            readings = self.imu.read_linear_acceleration()
            #readings = tuple([int(i*100) for i in readings])
            time.sleep(0.01)
            self.config['imu'] = SensorStatus.ENABLED
        except Exception as error:
            self.log("IMU Acceleration: " + str(error))
            self.config['imu'] += 1
        finally:
            ifMutexRelease(USEMUTEX)   
        return readings

    #get the gyro sensor angle/seconds acceleration from IMU sensor
    def get_gyro_sensor_IMU(self):
        gyro_readings = (SensorStatus.NOREADING,SensorStatus.NOREADING,SensorStatus.NOREADING)
        if self.config['imu'] >= SensorStatus.DISABLED:
            return gyro_readings
        ifMutexAcquire(USEMUTEX)
        try:
            gyro_readings = self.imu.read_gyroscope() #degrees/s
            time.sleep(0.01)
            self.config['imu'] = SensorStatus.ENABLED
        except Exception as error:
            self.log("IMU GYRO: " + str(error))
            self.config['imu'] += 1
        finally:
            ifMutexRelease(USEMUTEX)
        return gyro_readings

    #gets the temperature using the IMU sensor
    def get_temperature_IMU(self):
        temp = SensorStatus.NOREADING
        if self.config['imu'] >= SensorStatus.DISABLED:
            return temp
        ifMutexAcquire(USEMUTEX)
        try:
            temp = self.imu.read_temperature()
            time.sleep(0.01)
            self.config['imu'] = SensorStatus.ENABLED
        except Exception as error:
            self.log("IMU Temp: " + str(error))
            self.config['imu'] += 1
        finally:
            ifMutexRelease(USEMUTEX)
        return temp

    #get the ultrasonic sensor
    def get_ultra_sensor(self):
        distance = SensorStatus.NOREADING
        if self.config['ultra'] >= SensorStatus.DISABLED:
            return distance
        bp = self.BP
        ifMutexAcquire(USEMUTEX)
        try:
            distance = bp.get_sensor(self.ultra)
            time.sleep(0.3)
            self.config['ultra'] = SensorStatus.ENABLED
        except Exception as error:
            self.log("ULTRASONIC: " + str(error))
            self.config['ultra'] += 1
        finally:
            ifMutexRelease(USEMUTEX) 
        return distance

    #returns the colour current sensed - "NOREADING", "Black", "Blue", "Green", "Yellow", "Red", "White", "Brown"
    def get_colour_sensor(self):
        if self.config['colour'] >= SensorStatus.DISABLED:
            return "NOREADING"
        bp = self.BP
        value = 0
        colours = ["NOREADING", "Black", "Blue", "Green", "Yellow", "Red", "White", "Brown"]
        ifMutexAcquire(USEMUTEX)
        try: 
            value = bp.get_sensor(self.colour) 
            time.sleep(0.01)
            self.config['colour'] = SensorStatus.ENABLED
        except Exception as error:
            self.log("COLOUR: " + str(error))
            self.config['colour'] += 1
        ifMutexRelease(USEMUTEX)                
        return colours[value]

    #updates the thermal sensor by making continual I2C transactions through a thread
    def __update_thermal_sensor_thread(self, name):
        bp = self.BP
        while self.thread_running:
            self.update_thermal_sensor()
        self.log("BRICKPIINTERFACE: Exiting the Thermal Sensor Thread")
        bp.set_sensor_type(self.thermal, bp.SENSOR_TYPE.NONE) 
        return

    #updates the thermal sensor - can be called once or by a thread
    def update_thermal_sensor(self):
        ifMutexAcquire(USEMUTEX)
        bp = self.BP
        TIR_I2C_ADDR        = 0x0E      # TIR I2C device address 
        TIR_AMBIENT         = 0x00      # Ambient Temp
        TIR_OBJECT          = 0x01      # Object Temp
        TIR_SET_EMISSIVITY  = 0x02      
        TIR_GET_EMISSIVITY  = 0x03
        TIR_CHK_EMISSIVITY  = 0x04
        TIR_RESET           = 0x05
        try:
            bp.transact_i2c(self.thermal, TIR_I2C_ADDR, [TIR_OBJECT], 2)
            time.sleep(0.01)
        except Exception as error:
            self.config['thermal'] = SensorStatus.DISABLED
            self.thread_running = False #exit thread
            self.log("THERMAL UPDATE: " + str(error))
        ifMutexRelease(USEMUTEX) 
        return

    #return the infrared temperature
    def get_thermal_sensor(self):
        temp = SensorStatus.NOREADING

        if (self.config['thermal'] >= SensorStatus.DISABLED):
            return temp

        bp = self.BP

        if not self.thread_running:
            self.update_thermal_sensor() #run a single read of the thermal sensor

        #thread is running which is continually calling updated thermal sensor
        try:
            value = bp.get_sensor(self.thermal) # read the sensor values
            time.sleep(0.01)
            self.config['thermal'] = SensorStatus.ENABLED
            temp = (float)((value[1] << 8) + value[0]) # join the MSB and LSB part
            temp = temp * 0.02 - 0.01                  # Converting to Celcius
            temp = temp - 273.15                       
        except Exception as error:
            self.log("THERMAL READ: " + str(error))
            #disable automatically so that thread does not start
            self.config['thermal'] = SensorStatus.DISABLED
            #self.config['thermal'] += 1
        return float("%3.f" % temp)

    #disable thermal sensor - might be needed to reenable motors (they disable for some reason when thermal sensor is active)
    def disable_thermal_sensor(self):
        bp = self.BP
        bp.set_sensor_type(self.thermal, bp.SENSOR_TYPE.NONE) 
        return

    #--------------MOTOR COMMANDS-----------------#
    #simply turns motors on, dangerous because it does not turn them off
    def move_power(self, power, deviation=0):
        self.interrupt_previous_command()
        bp = self.BP
        self.CurrentCommand = "move_power"
        starttime = time.time()
        timelimit = starttime + self.timelimit
        bp.set_motor_power(self.rightmotor, power)
        bp.set_motor_power(self.leftmotor, power + deviation)
        while ((time.time() < timelimit) and (self.CurrentCommand == "move_power")):
            continue
        elapsedtime = time.time() - starttime
        self.stop_all()
        return elapsedtime

    #moves for the specified time (seconds) and power - use negative power to reverse
    def move_power_time(self, power, t, deviation=0):
        self.interrupt_previous_command()
        bp = self.BP
        self.CurrentCommand = "move_power_time"
        timelimit = time.time() + t
        bp.set_motor_power(self.rightmotor, power)
        bp.set_motor_power(self.leftmotor, power + deviation)
        while (time.time() < timelimit) and (self.CurrentCommand == "move_power_time"):
            continue
        self.stop_all()
        return

    #Rotate power and time, -power to reverse
    def rotate_power_time(self, power, t):
        self.interrupt_previous_command()
        self.CurrentCommand = "rotate_power_time"
        bp = self.BP
        target = time.time() + t
        bp.set_motor_power(self.rightmotor, -power)
        bp.set_motor_power(self.leftmotor, power)
        while (time.time() < target) and (self.CurrentCommand == "rotate_power_time"):
            continue
        self.stop_all() 
        return

    #Rotate power 
    def rotate_power(self, power):
        bp = self.BP #alias
        self.interrupt_previous_command()
        self.CurrentCommand = "rotate_power"
        starttime = time.time()
        timelimit = starttime + self.timelimit
        bp.set_motor_power(self.rightmotor, -power)
        bp.set_motor_power(self.leftmotor, power)
        while time.time() < timelimit and self.CurrentCommand == "rotate_power":
            continue
        elapsedtime = time.time() - starttime
        self.stop_all()
        return elapsedtime
        
    #Rotates the robot with power and degrees using the IMU sensor. Negative degrees = left.
    #the larger the number of degrees and the lower the power, the more accurate
    def rotate_power_degrees_IMU(self, power, degrees, marginoferror=3):
        bp = self.BP
        if (self.config['imu'] >= SensorStatus.DISABLED):
            return
        self.interrupt_previous_command()
        self.CurrentCommand = "rotate_power_degrees_IMU"
        
        data = {'rotated':0,'elapsed':0}

        symbol = '<'; limit = 0
        if degrees == 0:
            return
        elif degrees < 0:
            symbol = '>='; limit = degrees+marginoferror
        else:
            symbol = '<='; limit = degrees-marginoferror; power = -power
        totaldegreesrotated = 0; lastrun = 0
        
        starttime = time.time(); timelimit = starttime + self.timelimit
        #start motors 
        bp.set_motor_power(self.rightmotor, power)
        bp.set_motor_power(self.leftmotor, -power)

        while eval("totaldegreesrotated" + str(symbol) + "limit") and (self.CurrentCommand == "rotate_power_degrees_IMU") and (time.time() < timelimit) and (self.config['imu'] < SensorStatus.DISABLED):
            lastrun = time.time()
            gyrospeed = self.get_gyro_sensor_IMU()[2] #rotate around z-axis
            totaldegreesrotated += (time.time() - lastrun)*gyrospeed
            #self.log(totaldegreesrotated)
        self.stop_all()

        data['action'] = self.CurrentCommand
        data['elapsed'] = time.time() - starttime
        data['rotated'] = totaldegreesrotated
        return data

    #rotates the robot until faces targetheading - only works for a heading between 0 - 360
    def rotate_power_heading_IMU(self, power, targetheading, marginoferror=8):
        if (self.config['imu'] >= SensorStatus.DISABLED):
            return
        self.interrupt_previous_command()
        self.CurrentCommand = "rotate_power_heading"
        bp = self.BP
        if targetheading < 0:
            targetheading += 360
        elif targetheading > 360:
            targetheading -= 360
        heading = self.get_compass_IMU()
        time.sleep(0.1)
        if heading == targetheading:
            return
        symbol = '<'; limit = 0
        if heading < targetheading:
            symbol = '<='; limit = targetheading-marginoferror; 
        else:
            symbol = '>='; limit = targetheading+marginoferror; power = -power
        
        self.log("Starting Heading: " + str(heading) + " with Power: " + str(power))

        expression = 'heading' + symbol + 'limit'
        self.log('Rotating while ' + 'heading '+ symbol + " " + str(limit))
        
        elapsedtime = 0; starttime = time.time(); timelimit = starttime + self.timelimit
         
        #start rotating until heading is reached
        bp.set_motor_power(self.rightmotor, -power)
        bp.set_motor_power(self.leftmotor, power)
        while (eval(expression) and (self.CurrentCommand == "rotate_power_heading") and (time.time() < timelimit) and (self.config['imu'] < SensorStatus.DISABLED)):
            heading = self.get_compass_IMU()
            #self.log("Current heading: " + str(heading))
        self.stop_all()
        elapsedtime = time.time() - starttime
        return elapsedtime

    #spins the medium motor - this can be used for shooter or claw
    def spin_medium_motor(self, degrees):
        self.interrupt_previous_command()
        self.CurrentCommand = "spin_medium_motor"
        degrees = -degrees #if negative -> reverse motor
        bp = self.BP
        if degrees == 0:
            return
        bp.offset_motor_encoder(self.mediummotor, bp.get_motor_encoder(self.mediummotor)) #reset encoder
        limit = 0; symbol ='<'
        currentdegrees = 0 
        if degrees > 0:
            symbol = '<'; limit = degrees - 5
        else:
            symbol = '>'; limit = degrees + 5
        expression = 'currentdegrees' + symbol + 'limit'
        currentdegrees = bp.get_motor_encoder(self.mediummotor)

        elapsedtime = 0; starttime = time.time(); timelimit = starttime + self.timelimit
        while (eval(expression) and (self.CurrentCommand == "spin_medium_motor") and (time.time() < timelimit)):
            currentdegrees = bp.get_motor_encoder(self.mediummotor) #where is the current angle
            bp.set_motor_position(self.mediummotor, degrees)
            currentdegrees = bp.get_motor_encoder(self.mediummotor) #ACCURACY PROBLEM
        self.stop_all()
        elapsedtime = time.time() - starttime
        return elapsedtime

    #log out warnings
    def log(self, message):
        self.logger.info(message)
        return

    #rotate left motor but does not stop, use stop_all() to stop motor
    def set_left_motor_power(self, power):
        self.BP.set_motor_power(self.leftmotor, power)
        return

    #rotate right motor but does not stop, use stop_all() to stop motor
    def set_right_motor_power(self, power):
        self.BP.set_motor_power(self.rightmotor, power)
        return    

    #stop all motors and set current command to stop
    def stop_all(self):
        self.CurrentCommand = "stop"
        bp = self.BP
        bp.set_motor_power(self.largemotors+self.mediummotor, 0)
        return
        
    #returns the current command
    def get_current_command(self):
        return self.CurrentCommand

    #interuppt previous command
    def interrupt_previous_command(self):
        if self.CurrentCommand != "stop": #wait for current command to exit
            self.CurrentCommand = "stop"
            time.sleep(1)
        return

    #returns a dictionary of all current sensors
    def get_all_sensors(self):
        sensordict = {} #create a dictionary for the sensors
        sensordict['battery'] = self.get_battery()
        sensordict['colour'] = self.get_colour_sensor()
        sensordict['ultrasonic'] = self.get_ultra_sensor()
        sensordict['thermal'] = self.get_thermal_sensor()
        sensordict['acceleration'] = self.get_linear_acceleration_IMU()
        sensordict['compass'] = self.get_compass_IMU()
        sensordict['gyro'] = self.get_gyro_sensor_IMU()
        sensordict['temperature'] = self.get_temperature_IMU()
        sensordict['orientation'] = self.get_orientation_IMU()
        return sensordict

    #---EXIT--------------#
    # call this function to turn off the motors and exit safely.
    def safe_exit(self):
        bp = self.BP
        self.CurrentCommand = 'stop'
        self.thread_running = False
        self.stop_all() #stop all motors
        time.sleep(1)
        self.log("Exiting")
        bp.reset_all() # Unconfigure the sensors, disable the motors
        time.sleep(2) #gives time to reset??
        return

    
#--------------------------------------------------------------------
# Only execute if this is the main file, good for testing code
if __name__ == '__main__':
    logging.basicConfig(filename='logs/robot.log', level=logging.INFO)
    ROBOT = BrickPiInterface(timelimit=10)  #20 second timelimit before
    bp = ROBOT.BP; bp.reset_all(); time.sleep(2) #this will halt previou program is still running
    ROBOT.configure_sensors() #This takes 4 seconds
    input("Press enter to start: ")
    ROBOT.spin_medium_motor(300)
    ROBOT.rotate_power_degrees_IMU(17,90)
    print(ROBOT.get_all_sensors())
    ROBOT.safe_exit()