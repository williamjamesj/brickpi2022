from flask import Flask, render_template, session, request, redirect, url_for, jsonify, Response
from interfaces import grovepiinterface
from interfaces.camerainterface import *

CAMERA = Camera() #make a global variable for the camera

app = Flask(__name__) #Creates the Flask Server Object
app.debug = True

#Dashboard
@app.route('/', methods=['GET','POST'])
def dashboard():
    return render_template('dashboard.html')

# CAMERA CODE (Not Sure how it works)
def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n') 

@app.route('/videofeed')
def videofeed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(CAMERA), mimetype='multipart/x-mixed-replace; boundary=frame') #not actually sure what this code does    

#main method called web server application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True) #runs a local server on port 5000