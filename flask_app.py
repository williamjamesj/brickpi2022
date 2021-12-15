from flask import Flask, render_template, session, request, redirect, url_for, jsonify, Response, logging
from interfaces import databaseinterface, camerainterface
import robot
from global_vars import *
import logging

#Creates the Flask Server Object
app = Flask(__name__); app.debug = True
logging.basicConfig(filename='logs/flask.log', level=logging.INFO)

#Log messages
def log(message):
    app.logger.info(message)
    return

# Load the ROBOT
@app.route('/robotload', methods=['GET','POST'])
def robotload():
    sensordict = None
    log("LOADING THE ROBOT")
    global ROBOT
    if not ROBOT: 
        ROBOT = robot.Robot(20, app.logger)
        ROBOT.configure_sensors() #defaults have been provided but you can 
        sensordict = ROBOT.get_all_sensors()
    '''global DATABASE
    if not DATABASE:
        DATABASE = databaseinterface.Database('databases/test.sqlite', app.logger)
    global CAMERA
    if not CAMERA:
        CAMERA = camerainterface.Camera()'''
    
    return jsonify({ 'message':'robot loaded' })

#-YOUR FLASK CODE------------------------------------------------------------------------
# Dashboard
@app.route('/', methods=['GET','POST'])
def robotdashboard():
    return render_template('dashboard.html')






















#-CAMERA CODE-----------------------------------------------------------------------
# Continually gets the frame from the pi camera
def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n') 

#embeds the videofeed by returning a continual stream as above
@app.route('/videofeed')
def videofeed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(CAMERA), mimetype='multipart/x-mixed-replace; boundary=frame') #not actually sure what this code does    

#----------------------------------------------------------------------------
#Shutdown the ROBOT incase anything not working
@app.route('/robotshutdown', methods=['GET','POST'])
def robotshutdown():
    log("SHUTDOWN THE ROBOT")
    '''if ROBOT:
        ROBOT.safe_exit()'''
    return jsonify({'message':'robot shutdown'})

#Shut down the web server if necessary
@app.route('/shutdown', methods=['GET','POST'])
def shutdown():
    log("SHUTDOWN")
    '''if ROBOT:
        ROBOT.safe_exit()'''
    func = request.environ.get('werkzeug.server.shutdown'); func()
    return jsonify({'message':'shutdown web server'})

#---------------------------------------------------------------------------
#main method called web server application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True) #runs a local server on port 5000