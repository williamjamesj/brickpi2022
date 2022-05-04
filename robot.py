#This is where your main robot code resides. It extendeds from the BrickPi Interface File
#It includes all the code inside brickpiinterface. The CurrentCommand and CurrentRoutine are important because they can keep track of robot functions and commands. Remember Flask is using Threading (e.g. more than once process which can confuse the robot)
from interfaces.brickpiinterface import *
from interfaces.camerainterface import CameraInterface
import global_vars as GLOBALS
import logging
import time

class Robot(BrickPiInterface):
    
    def __init__(self, timelimit=10, logger=logging.getLogger()):
        super().__init__(timelimit, logger)
        self.CurrentCommand = "stop" #use this to stop or start functions
        self.CurrentRoutine = "stop" #use this stop or start routines
        return

    """Motor encoder code inspired by https://github.com/DexterInd/BrickPi3/blob/master/Software/Python/Examples/LEGO-Motor_Position.py"""
    def reset_motors(self): # power is in percent, speed is in degrees per second
        """Resets the motors to 0, to track movement."""
        self.BP.offset_motor_encoder(self.BP.PORT_A, self.BP.get_motor_encoder(self.BP.PORT_A)) # Reset both motor's encoders.
        self.BP.offset_motor_encoder(self.BP.PORT_D, self.BP.get_motor_encoder(self.BP.PORT_D))
        return
    
    def limits_and_positions(self, power, speed, posD, posA): # PosD is for the left motor, and posA is for the right motor.
        self.BP.set_motor_limits(self.BP.PORT_A, power, speed) # Set speed and power limits for MOTOR A
        self.BP.set_motor_limits(self.BP.PORT_D, power, speed) # Set speed and power limits for MOTOR D
        self.BP.set_motor_position(self.BP.PORT_A, posA)
        self.BP.set_motor_position(self.BP.PORT_D, posD)
        return

    def turn(self, degrees, power=100, speed=200):
        """This function turns the robot a certain number of degrees. 
        It turns in a clockwise direction when the desired degrees are positive, and an anticlockwise direction when the desired degrees are negative. """
        degrees = degrees*2
        self.CurrentCommand = "turn"
        self.reset_motors() # Motor A is the right motor, and motor D is the left motor.
        self.limits_and_positions(power, speed, degrees+10, -1*degrees-10) # Without the +10 and -10, the robot will become stuck, being unable to finish its turn. Degrees+2 is used to attempt to overshoot the necessary position, however the robot will stop turning when it reaches the desired position.
        while not (self.BP.get_motor_encoder(self.BP.PORT_D) >= degrees or self.BP.get_motor_encoder(self.BP.PORT_A) <= -1*degrees):
            time.sleep(0.01)
        return
    
    def drive_forward(self, distance=42.5, power=100, speed=200): # 42.5 is approximately the size of a sector.
        distance = distance*20.4627783975 # This is a magical number that takes into account the size of the wheels, and converts in to the number of degrees that need to be travelled.
        self.CurrentCommand = "drive"
        self.reset_motors()
        self.limits_and_positions(power, speed, distance+15, distance+15)
        while not (self.BP.get_motor_encoder(self.BP.PORT_D) >= distance or self.BP.get_motor_encoder(self.BP.PORT_A) >= distance): # This only waits for one motor to reach the desired position, even though it would be more accurate to wait for both.
            time.sleep(0.01)
        return

    def search_maze(self):
        self.CurrentRoutine = "search"
        





# Only execute if this is the main file, good for testing code
if __name__ == '__main__':
    time.sleep(2)
    logging.basicConfig(filename='logs/robot.log', level=logging.INFO)
    ROBOT = Robot(timelimit=10)  #10 second timelimit before
    # CAMERA = CameraInterface()
    # time.sleep(1)
    # CAMERA.start()
    # frame = CAMERA.get_frame()
    try:
        ROBOT.configure_sensors() #This takes 4 seconds
        ROBOT.drive_forward()
        ROBOT.turn(360)
    except:
        ROBOT.stop_all()
        ROBOT.safe_exit()
        print("Keyboard Interrupt")

    # ROBOT.turn(ROBOT.left,20)
    # ROBOT.stop_all()
    # time.sleep(1)
    # ROBOT.turn(ROBOT.backward,20)
    # ROBOT.stop_all()
    # time.sleep(1)
    # ROBOT.turn(ROBOT.left,20)
    # ROBOT.stop_all()
    # time.sleep(1)
    # ROBOT.turn(ROBOT.right,20)
    # ROBOT.stop_all()
    # time.sleep(1)
    # ROBOT.turn(ROBOT.forward,20)
    # ROBOT.stop_all()
    
    # try:
    #     ROBOT.search_maze()
    # except KeyboardInterrupt:
    #     ROBOT.stop_all()
    #     ROBOT.safe_exit()
    #     print("Keyboard Interrupt")

    # ROBOT.move_square(1,2.5)
    # ROBOT.rotate_power_degrees_IMU(20,-90)
    # start = time.time()
    # limit = start + 10
    # while (time.time() < limit):
    #     compass = ROBOT.get_compass_IMU()
    #     print(compass)
    # sensordict = ROBOT.get_all_sensors()
    # ROBOT.safe_exit()
    ROBOT.stop_all()
    ROBOT.safe_exit()
