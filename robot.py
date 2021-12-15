#This is where your main robot code resides. It extendeds from the BrickPi Interface File
#It includes all the code inside brickpiinterface. The CurrentCommand and CurrentRoutine are important because they can keep track of robot functions and commands. Remember Flask is using Threading (e.g. more than once process which can confuse the robot)
from interfaces.brickpiinterface import *
import global_vars

class Robot(BrickPiInterface):

     def __init__(self, timelimit=20, logger=logging.getLogger()):
        super().__init__(timelimit, logger)
        self.CurrentCommand = "stop"
        self.CurrentRoutine = "stop"
        return
    
    #Create a function to move time and power which will stop if colour is detected or an object has been found

    #Create a function to rotate time and power until and object has been detected