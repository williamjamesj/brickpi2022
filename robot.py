#This is where your main robot code resides. It extendeds from the BrickPi Interface File
#It includes all the code inside brickpiinterface. The CurrentCommand and CurrentRoutine are important because they can keep track of robot functions and commands. Remember Flask is using Threading (e.g. more than once process which can confuse the robot)
from interfaces.brickpiinterface import *
import global_vars as GLOBALS
import logging

class Robot(BrickPiInterface):
    
    def __init__(self, timelimit=10, logger=logging.getLogger()):
        super().__init__(timelimit, logger)
        self.CurrentCommand = "stop" #use this to stop or start functions
        self.CurrentRoutine = "stop" #use this stop or start routines
        return
        
        
    #Create a function to move time and power which will stop if colour is detected or wall has been found
    def move_forward_until_wall(self,power,error,limit):
        self.interrupt_previous_command()
        self.CurrentCommand = "move_forward_until_wall"
        start_time = time.time()
        timelimit = start_time + self.timelimit
        if power+error > 100:
            self.BP.set_motor_power(self.rightmotor, power-error)    
            self.BP.set_motor_power(self.leftmotor, power)
        else:
            self.BP.set_motor_power(self.rightmotor, power)    
            self.BP.set_motor_power(self.leftmotor, power+error)
        ultra = self.get_ultra_sensor()
        while ((time.time() < timelimit) and (self.CurrentCommand =="move_forward_until_wall") and (ultra > limit and ultra != 0)):
            ultra = self.get_ultra_sensor()
            print(ultra)
            continue
        print(ultra)
        elapsed_time = time.time() - start_time
        self.stop_all()
        return elapsed_time



    # Maze Searching Functions
    def move_square(self, squares, error):
        power = 50
        time_per_square = 3.3
        traveltime = time_per_square*squares
        distance = 30
        self.interrupt_previous_command()
        self.CurrentCommand = "search_maze"
        start_time = time.time()
        print(start_time)
        end_time = start_time+traveltime
        ultra = self.get_ultra_sensor()
        if power+error > 100:
            self.BP.set_motor_power(self.rightmotor, power-error)    
            self.BP.set_motor_power(self.leftmotor, power)
        else:
            self.BP.set_motor_power(self.rightmotor, power)    
            self.BP.set_motor_power(self.leftmotor, power+error)
        while time.time() < end_time and self.CurrentCommand == "search_maze" and ultra >= 20:
            ultra = self.get_ultra_sensor()
            print(ultra)
        self.stop_all()
        return

    #Create a function to search for victim
    

    
    
    
    #Create a routine that will effective search the maze and keep track of where the robot has been.






# Only execute if this is the main file, good for testing code
if __name__ == '__main__':
    logging.basicConfig(filename='logs/robot.log', level=logging.INFO)
    ROBOT = Robot(timelimit=10)  #10 second timelimit before
    bp = ROBOT.BP
    ROBOT.configure_sensors() #This takes 4 seconds
    # ROBOT.move_forward_until_wall(50,2.5,20)
    ROBOT.move_square(1,2.5)
    # ROBOT.rotate_power_degrees_IMU(20,-90)
    # start = time.time()
    # limit = start + 10
    # while (time.time() < limit):
    #     compass = ROBOT.get_compass_IMU()
    #     print(compass)
    # sensordict = ROBOT.get_all_sensors()
    # ROBOT.safe_exit()
