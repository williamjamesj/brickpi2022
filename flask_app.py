from flask import Flask, render_template, session, request, redirect, flash, url_for, jsonify, Response, logging
from interfaces import databaseinterface, camerainterface
import robot #robot is class that extends the brickpi class
from global_vars import *
import logging, time

#Creates the Flask Server Object
app = Flask(__name__); app.debug = True
SECRET_KEY = 'my random key can be anything' #this is used for encrypting sessions
app.config.from_object(__name__) #Set app configuration using above SETTINGS
logging.basicConfig(filename='logs/flask.log', level=logging.INFO)
DATABASE = databaseinterface.Database('databases/RobotDatabase.db', app.logger)

#Log messages
def log(message):
    app.logger.info(message)
    return

#create a login page
@app.route('/', methods=['GET','POST'])
def login():
    if 'userid' in session:
        return redirect('/dashboard')
    message = ""
    if request.method == "POST":
        email = request.form.get("email")
        userdetails = DATABASE.ViewQuery("SELECT * FROM users WHERE email = ?", (email,))
        log(userdetails)
        if userdetails:
            user = userdetails[0] #get first row in results
            if user['password'] == request.form.get("password"):
                session['userid'] = user['userid']
                session['permission'] = user['permission']
                session['name'] = user['name']
                return redirect('/dashboard')
            else:
                message = "Login Unsuccessful"
        else:
            message = "Login Unsuccessful"
    return render_template('login.html', data = message)    

# Load the ROBOT
@app.route('/robotload', methods=['GET','POST'])
def robotload():
    sensordict = None
    global CAMERA
    if not CAMERA:
        log("LOADING CAMERA")
        CAMERA = camerainterface.Camera()
        time.sleep(1)
    global ROBOT
    if not ROBOT: 
        log("LOADING THE ROBOT")
        ROBOT = robot.Robot(20, app.logger)
        ROBOT.configure_sensors() #defaults have been provided but you can 
    sensordict = ROBOT.get_all_sensors()
    return jsonify(sensordict)

#-YOUR FLASK CODE------------------------------------------------------------------------
# Dashboard
@app.route('/dashboard', methods=['GET','POST'])
def robotdashboard():
    if not 'userid' in session:
        return redirect('/')
    enabled = int(ROBOT != None)
    return render_template('dashboard.html', robot_enabled = enabled )































#-CAMERA CODE-----------------------------------------------------------------------
# Continually gets the frame from the pi camera
def gen(cam):
    """Video streaming generator function."""
    while True:
        frame = cam.get_frame()
        if frame:
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n') 

#embeds the videofeed by returning a continual stream as above
@app.route('/videofeed')
def videofeed():
    log("READING CAMERA")
    global CAMERA
    if CAMERA:
        """Video streaming route. Put this in the src attribute of an img tag."""
        return Response(gen(CAMERA), mimetype='multipart/x-mixed-replace; boundary=frame') 
    else:
        return '', 204
#----------------------------------------------------------------------------
#Shutdown the robot, camera and database
def shutdowneverything():
    log("SHUT DOWN EVERYTHING")
    global ROBOT
    if ROBOT:
        ROBOT.safe_exit(); ROBOT = None
    global CAMERA
    if CAMERA:
        CAMERA = None
    return

#Ajax handler for shutdown button
@app.route('/robotshutdown', methods=['GET','POST'])
def robotshutdown():
    shutdowneverything()
    return jsonify({'message':'robot shutdown'})

#Shut down the web server if necessary
@app.route('/shutdown')
def shutdown():
    shutdowneverything()
    func = request.environ.get('werkzeug.server.shutdown'); func()
    return jsonify({'message':'shutdown web server'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

#---------------------------------------------------------------------------
#main method called web server application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True) #runs a local server on port 5000