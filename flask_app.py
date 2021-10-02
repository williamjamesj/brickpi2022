from flask import Flask, render_template, session, request, redirect, url_for, jsonify, Response
from interfaces import grovepiinterface
from interfaces.camerainterface import *

app = Flask(__name__) #Creates the Flask Server Object
app.debug = True

ledswitch = 0

#Dashboard
@app.route('/', methods=['GET','POST'])
def dashboard():
    return render_template('dashboard.html')

@app.route('/switchled', methods=['GET','POST'])
def switchled():
    global ledswitch
    ledswitch = not(ledswitch)
    grovepiinterface.set_led_digitalport_value(7,ledswitch)
    return jsonify({'message':'Success: light turned on'})

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
    return Response(gen(Camera()), mimetype='multipart/x-mixed-replace; boundary=frame') #not actually sure what this code does    

#main method called web server application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True) #runs a local server on port 5000