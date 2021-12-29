#This is where your main robot code resides. It extendeds from the BrickPi Interface File
#It includes all the code inside brickpiinterface. The CurrentCommand and CurrentRoutine are important because they can keep track of robot functions and commands. Remember Flask is using Threading (e.g. more than once process which can confuse the robot)
from interfaces.brickpiinterface import *
import global_vars as G
import logging

class Robot(BrickPiInterface):
    
    def __init__(self, timelimit=10, logger=logging.getLogger()):
        super().__init__(timelimit, logger)
        self.CurrentCommand = "stop"
        self.CurrentRoutine = "stop"
        return
        
    #Create a function to move time and power which will stop if colour is detected or an object has been found
    




    #Create a function to rotate time and power until and object has been detected
    def rotate_power_untilobjectdetected(self, power):
        self.interrupt_previous_command()
        self.CurrentCommand = "rotate_power_untilobjectdetected"
        self.log("ROBOT: " + self.CurrentCommand)
        starttime = time.time(); timelimit = starttime + self.timelimit
        data = { 'starttime': starttime, 'command': self.CurrentCommand }
        bp = self.BP #alias

        found = False
        bp.set_motor_power(self.rightmotor, -power)
        bp.set_motor_power(self.leftmotor, power)
        while time.time() < timelimit and self.CurrentCommand == "rotate_power_untilobjectdetected":
            #detected an object
            distance = self.get_ultra_sensor()
            #self.log("Ultra: " + str(distance))
            if distance < 50 and distance != 0:
                self.stop_all()
                data['endtime'] = time.time()
                found = True
                break

        self.stop_all()

        if found:
            data['distance'] = distance
            data['thermal'] = self.get_thermal_sensor()
            if G.CAMERA:
                data['cameracolour'] = G.CAMERA.get_camera_colour()
                if data['cameracolour'] == 'red':
                    self.spin_medium_motor(-1200)
        return data




    #Create a function that will shoot an object if the temperature is 5 degrees higher than normal temperature





    #Create a routine that will effective search the maze and keep track of where the robot has been.






# Only execute if this is the main file, good for testing code
if __name__ == '__main__':
    logging.basicConfig(filename='logs/robot.log', level=logging.INFO)
    ROBOT = Robot(timelimit=10)  #10 second timelimit before
    bp = ROBOT.BP
    ROBOT.configure_sensors() #This takes 4 seconds
    ROBOT.rotate_power_degrees_IMU(20,-90)
    start = time.time()
    limit = start + 10
    '''while (time.time() < limit):
        compass = ROBOT.get_compass_IMU()
        print(compass)'''
    sensordict = ROBOT.get_all_sensors()
    ROBOT.safe_exit()