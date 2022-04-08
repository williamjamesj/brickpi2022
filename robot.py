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
        self.BP.reset_motor_encoder(self.BP.PORT_A)
        self.BP.reset_motor_encoder(self.BP.PORT_B)
        ninetydegrees = 85
        # if not self.maze_progress:
        self.maze_progress ={}
        self.x = 0
        self.y = 0
        self.orientation = 0
        while True:
            for i in range (4): # Search all of the four directions that a wall/victim can be.
                if self.orientation >= 4:
                    self.orientation = 0
                distance = ROBOT.get_ultra_sensor()
                if distance > 30:
                    self.maze_progress[str([self.x,self.y,self.orientation])] = True
                    print(self.orientation,"No Wall")
                else:
                    print(self.orientation,"Wall")
                    self.maze_progress[str([self.x,self.y,self.orientation])] = False
                ROBOT.rotate_power_degrees_IMU(10, ninetydegrees) # Turn Right ~ 90 Degrees
                self.orientation += 1
            forward = self.maze_progress[str([self.x,self.y,0])]
            right = self.maze_progress[str([self.x,self.y,1])]
            behind = self.maze_progress[str([self.x,self.y,2])]
            left = self.maze_progress[str([self.x,self.y,3])]
            print(self.maze_progress)
            if left:
                self.orientation =  2
                ROBOT.rotate_power_degrees_IMU(10, 3*ninetydegrees)
                self.move_square(1,2.5)
            elif right:
                self.orientation =  1
                ROBOT.rotate_power_degrees_IMU(10, ninetydegrees)
                self.move_square(1,2.5)
            elif forward:
                self.orientation =  0
                self.move_square(1,2.5)
            else:
                self.orientation =  3
                ROBOT.rotate_power_degrees_IMU(10, 2*ninetydegrees)
                self.move_square(1,2.5)
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
    

    
    
    
    #Create a routine that will effective search the maze and keep track of where the robot has been.






# Only execute if this is the main file, good for testing code
if __name__ == '__main__':
    logging.basicConfig(filename='logs/robot.log', level=logging.INFO)
    ROBOT = Robot(timelimit=10)  #10 second timelimit before
    bp = ROBOT.BP
    ROBOT.configure_sensors() #This takes 4 seconds
    # ROBOT.move_square(1,2.5)
    # input("Get Straight, then press enter...")
    try:
        ROBOT.search_maze()
    except KeyboardInterrupt:
        ROBOT.stop_all()
        ROBOT.safe_exit()
        print("Keyboard Interrupt")
    # for i in range(10):
    #     print(ROBOT.get_ultra_sensor())
    # ROBOT.move_forward_until_wall(50,2.5,20)
    # for i in range(10):
    #     powermodifier = 1
    #     if i%2 != 0:
    #         powermodifier = -1
    #     ROBOT.move_square(1,2.5,powermodifier=powermodifier)

    # ROBOT.move_square(1,2.5)
    # ROBOT.rotate_power_degrees_IMU(20,-90)
    # start = time.time()
    # limit = start + 10
    # while (time.time() < limit):
    #     compass = ROBOT.get_compass_IMU()
    #     print(compass)
    # sensordict = ROBOT.get_all_sensors()
    ROBOT.safe_exit()
