#This is where your main robot code resides. It extendeds from the BrickPi Interface File
#It includes all the code inside brickpiinterface. The CurrentCommand and CurrentRoutine are important because they can keep track of robot functions and commands. Remember Flask is using Threading (e.g. more than once process which can confuse the robot)
from interfaces.brickpiinterface import *
# from flask_app import logaction
import global_vars as GLOBALS
import logging
import time

class Robot(BrickPiInterface):
    
    def __init__(self, timelimit=10, logger=logging.getLogger()):
        super().__init__(timelimit, logger)
        self.CurrentCommand = "stop" #use this to stop or start functions
        self.CurrentRoutine = "stop" #use this stop or start routines
        return
    
    def configure_compass(self):
        self.forward = self.get_orientation_IMU()[0]
        self.right = self.forward+90
        self.backward = self.forward+180
        self.left = self.forward+270
        self.uncheckeddirections = [self.right,self.backward,self.left,self.forward]
        self.directions =[]
        for i in self.uncheckeddirections:
            if i > 360:
                i -= 360
            self.directions.append(i)
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
    def move_square(self, squares, error, powermodifier=1):
        power = 25*powermodifier
        time_per_square = 3
        traveltime = time_per_square*squares
        distance = 30
        self.interrupt_previous_command()
        self.CurrentCommand = "move_square"
        start_time = time.time()
        print(start_time)
        end_time = start_time+traveltime
        ultra = self.get_ultra_sensor()
        if power+error > 100:
            self.BP.set_motor_power(self.rightmotor, power-error*powermodifier)   
            self.BP.set_motor_power(self.leftmotor, power)
        else:
            self.BP.set_motor_power(self.rightmotor, power)    
            self.BP.set_motor_power(self.leftmotor, power+error*powermodifier)
        while time.time() < end_time and self.CurrentCommand == "move_square" and ultra >= 10:
            ultra = self.get_ultra_sensor()
            print(ultra)
        print(ultra)
        self.stop_all()
        return


    def search_maze(self):
        # if not self.maze_progress:
        self.maze_progress ={}
        self.x = 0
        self.y = 0
        self.orientation = 0 # 0 is right, 1 is left, 2 is backwards, 3 is forwards
        print(self.directions)
        while True:
            for i in self.directions: # Search all of the four directions that a wall/victim can be.
                distance = ROBOT.get_ultra_sensor()
                if distance > 30:
                    self.maze_progress[str([self.x,self.y,self.directions.index(i)])] = True
                    print(self.orientation,"No Wall")
                else:
                    print(self.orientation,"Wall")
                    self.maze_progress[str([self.x,self.y,self.directions.index(i)])] = False
                print("turning to ",i)
                ROBOT.turn(i,25) # Turn to the necessary direction using the orientation-based turning function
            forward = self.maze_progress[str([self.x,self.y,0])]
            right = self.maze_progress[str([self.x,self.y,1])]
            backward = self.maze_progress[str([self.x,self.y,2])]
            left = self.maze_progress[str([self.x,self.y,3])]
            print(forward,right,backward,left)
            print(self.maze_progress)
            if left:
                self.orientation =  2
                self.turn(self.directions[2],10)
                self.move_square(1,2.5)
                self.x -= 1
            elif right:
                self.orientation =  1
                self.turn(self.directions[0],10)
                self.move_square(1,2.5)
                self.x += 1
            elif forward:
                self.orientation =  0
                self.turn(self.directions[3],10)
                self.move_square(1,2.5)
                self.y += 1
            else:
                self.orientation =  3
                self.turn(self.directions[1],10)
                self.move_square(1,2.5)
                self.y -= 1
        return
            
    # def move_forward_encoder(self,distance):
    #     speed =150 # Degrees per second
    #     power = 100 # 100%
    #     encoder_distance = distance*360/(3.14159265359 * 5.6)
    #     BP = self.BP
    #     BP.offset_motor_encoder(BP.PORT_A, BP.get_motor_encoder(BP.PORT_A))
    #     BP.offset_motor_encoder(BP.PORT_A, BP.get_motor_encoder(BP.PORT_A))
    #     BP.set_motor_limits(BP.PORT_A, power, speed)
    #     BP.set_motor_limits(BP.PORT_D, power, speed)
    #     while True:
    #         print(( BP.get_motor_encoder[BP.PORT_A] %720 ) /2)   # print the encoder degrees 
    #         time.sleep(.1)	
    #Create a function to search for victim
    
    def turn(self, degrees, power):
        current_direction = self.get_orientation_IMU()[0]
        print("Turning to",degrees,"degrees.")
        clockwise = degrees-current_direction # Find the distance the robot has to travel in a clockwise direction.
        counterclockwise = current_direction-degrees # find the distance the robot has to travel in a counterclockwise direction.
        if clockwise > counterclockwise: # Turn clockwise to the destination.
            print("Clockwise.")
            compass = self.get_orientation_IMU()[0]
            while compass < degrees:
                if degrees < 1 and compass > 355:
                    break
                self.BP.set_motor_power(self.rightmotor, -power)
                self.BP.set_motor_power(self.leftmotor, power)
                compass = self.get_orientation_IMU()[0]
                # print(compass)
        else: # Turn counterclockwise to the destination.
            compass = self.get_orientation_IMU()[0]
            while compass > degrees:
                if degrees < 1 and compass > 355:
                    break
                self.BP.set_motor_power(self.rightmotor, power)
                self.BP.set_motor_power(self.leftmotor, -power)
                compass = self.get_orientation_IMU()[0]
                # print(compass)
        print(compass)
        pass

    
    
    
    #Create a routine that will effective search the maze and keep track of where the robot has been.






# Only execute if this is the main file, good for testing code
if __name__ == '__main__':
    logging.basicConfig(filename='logs/robot.log', level=logging.INFO)
    ROBOT = Robot(timelimit=10)  #10 second timelimit before
    bp = ROBOT.BP
    ROBOT.configure_sensors() #This takes 4 seconds
    # ROBOT.move_square(1,2.5)
    # input("Get Straight, then press enter...")
    ROBOT.configure_compass()
    # ROBOT.turn(360,20)
    try:
        ROBOT.search_maze()
    except KeyboardInterrupt:
        ROBOT.stop_all()
        ROBOT.safe_exit()
        print("Keyboard Interrupt")

    # ROBOT.move_square(1,2.5)
    # ROBOT.rotate_power_degrees_IMU(20,-90)
    # start = time.time()
    # limit = start + 10
    # while (time.time() < limit):
    #     compass = ROBOT.get_compass_IMU()
    #     print(compass)
    # sensordict = ROBOT.get_all_sensors()
    ROBOT.safe_exit()
