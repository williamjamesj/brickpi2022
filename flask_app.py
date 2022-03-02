from flask import Flask, render_template, session, request, redirect, flash, url_for, jsonify, Response, logging
from interfaces import databaseinterface, camerainterface, soundinterface
import robot #robot is class that extends the brickpi class
import global_vars as GLOBALS #load global variables
import logging, time
from passlib.hash import sha256_crypt
import pyotp

#Creates the Flask Server Object
app = Flask(__name__); app.debug = True
SECRET_KEY = 'my random key can be anything' #this is used for encrypting sessions
app.config.from_object(__name__) #Set app configuration using above SETTINGS
logging.basicConfig(filename='logs/flask.log', level=logging.INFO)
GLOBALS.DATABASE = databaseinterface.DatabaseInterface('databases/RobotDatabase.db', app.logger)
# qrcode = QRcode(app)

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
        userdetails = GLOBALS.DATABASE.ViewQuery("SELECT * FROM users WHERE email = ?", (email,))
        log(userdetails)
        if userdetails:
            user = userdetails[0] #get first row in results
            correct_password = sha256_crypt.verify(request.form.get("password"), user['password'])
            if correct_password:
                if user["OTPcode"]:
                    session['tempuserid'] = user['userid']
                    return redirect("/2fa")
                session['userid'] = user['userid']
                session['permission'] = user['permission']
                session['name'] = user['name']
                session["email"] = user["email"]
                return redirect('/dashboard')
            else:
                flash("Login unsuccessful.", "warning")
        else:
            flash("Login unsuccessful.", "warning")
    return render_template('login.html', data = message)    

# Load the ROBOT
@app.route('/robotload', methods=['GET','POST'])
def robotload():
    sensordict = None
    if not GLOBALS.CAMERA:
        log("LOADING CAMERA")
        try:
            GLOBALS.CAMERA = camerainterface.CameraInterface()
        except Exception as error:
            log("FLASK APP: CAMERA NOT WORKING")
            GLOBALS.CAMERA = None
        if GLOBALS.CAMERA:
            GLOBALS.CAMERA.start()
    if not GLOBALS.ROBOT: 
        log("FLASK APP: LOADING THE ROBOT")
        GLOBALS.ROBOT = robot.Robot(20, app.logger)
        GLOBALS.ROBOT.configure_sensors() #defaults have been provided but you can 
        GLOBALS.ROBOT.reconfig_IMU()
    if not GLOBALS.SOUND:
        log("FLASK APP: LOADING THE SOUND")
        GLOBALS.SOUND = soundinterface.SoundInterface()
        GLOBALS.SOUND.say("I am ready")
    sensordict = GLOBALS.ROBOT.get_all_sensors()
    return jsonify(sensordict)

# ---------------------------------------------------------------------------------------
# Dashboard
@app.route('/dashboard', methods=['GET','POST'])
def robotdashboard():
    if not 'userid' in session:
        return redirect('/')
    enabled = int(GLOBALS.ROBOT != None)
    return render_template('dashboard.html', robot_enabled = enabled )

#Used for reconfiguring IMU
@app.route('/reconfig_IMU', methods=['GET','POST'])
def reconfig_IMU():
    if GLOBALS.ROBOT:
        GLOBALS.ROBOT.reconfig_IMU()
        sensorconfig = GLOBALS.ROBOT.get_all_sensors()
        return jsonify(sensorconfig)
    return jsonify({'message':'ROBOT not loaded'})

#calibrates the compass but takes about 10 seconds, rotate in a small 360 degrees rotation
@app.route('/compass', methods=['GET','POST'])
def compass():
    data = {}
    if GLOBALS.ROBOT:
        data['message'] = GLOBALS.ROBOT.calibrate_imu(10)
    return jsonify(data)

@app.route('/sensors', methods=['GET','POST'])
def sensors():
    data = {}
    if GLOBALS.ROBOT:
        data = GLOBALS.ROBOT.get_all_sensors()
    return jsonify(data)

# YOUR FLASK CODE------------------------------------------------------------------------

@app.route("/finecontrol", methods=["GET","POST"])
def finecontrol(power,direction,action):
    if request.method == "POST":
        print(power,direction,action)
        return jsonify({})
    return render_template("finecontrol.html")

@app.route("/shoot", methods=["GET","POST"])
def shoot():
    data = {}
    if GLOBALS.SOUND:
        GLOBALS.SOUND.say("OwOwOwO")
    if GLOBALS.ROBOT:
        GLOBALS.ROBOT.spin_medium_motor(-2000)
    return jsonify(data)

@app.route("/moveforward", methods=["GET","POST"])
def moveforward():
    data = {}
    if GLOBALS.ROBOT:
        GLOBALS.ROBOT.move_power_time(50,10)
    return jsonify(data)

@app.route("/moveright", methods=["GET","POST"])
def moveright():
    data = {}
    if GLOBALS.ROBOT:
        data = GLOBALS.ROBOT.rotate_power_degrees_IMU(50,-10)
    return jsonify(data)


@app.route("/moveleft", methods=["GET","POST"])
def moveleft():
    data = {}
    if GLOBALS.ROBOT:
        data = GLOBALS.ROBOT.rotate_power_degrees_IMU(50,10)
    return jsonify(data)

@app.route("/stop", methods=["GET","POST"])
def stop():
    data = {}
    if GLOBALS.ROBOT:
        data = GLOBALS.ROBOT.stop_all()
    return jsonify(data)

@app.route("/sensorview", methods=["GET","POST"])
def sensorview():
    data = None
    return render_template("sensorview.html",data=data)

@app.route("/mission", methods=["GET","POST"])
def mission():
    # If formdata
        # Get form data
        # save data to database
    data = None
    return render_template("mission.html",data=data)






@app.route("/admin", methods=["GET","POST"]) # Allows administrators to view users.
def admin():
    if 'userid' in session:
        if session['permission'] != 'admin':
            return redirect('/dashboard')
    else:
        return redirect('/')
    users = GLOBALS.DATABASE.ViewQuery("SELECT * FROM users")
    return render_template("admin.html", users = users)

@app.route("/createuser", methods=["GET","POST"]) # Allows the admin to create new users.
def createuser():
    if 'userid' in session:
        if session['permission'] != 'admin':
            return redirect('/dashboard')
    else:
        return redirect('/')
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        password = sha256_crypt.hash(password)
        permission = request.form.get("permission")
        if permission == "on":
            permission = "admin"
        else:
            permission = "user"
        GLOBALS.DATABASE.ModifyQuery("INSERT INTO users (name, email, password, permission) VALUES (?,?,?,?)", (name, email, password, permission))
        return redirect('/admin')
    return render_template("createuser.html")

@app.route("/accountsettings", methods=["GET","POST"])
def accountsettings():
    if "userid" not in session:
        return redirect("/")
    userdetails = GLOBALS.DATABASE.ViewQuery("SELECT * FROM users WHERE userid = ?", (session['userid'],))[0]
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        oldpassword = request.form.get("oldpassword")
        correct_password = sha256_crypt.verify(oldpassword, userdetails['password'])
        if correct_password:
            password = sha256_crypt.hash(password)
            GLOBALS.DATABASE.ModifyQuery("UPDATE users SET name = ?, email = ?, password = ? WHERE userid = ?", (name, email, password, session['userid']))
            flash("Account settings updated","success")
            return redirect('/dashboard')
        else:
            flash("Incorrect password","warning")
            return redirect('/accountsettings')
    return render_template("accountsettings.html", userdetails = userdetails)

@app.route("/2faconfig", methods=["GET","POST"])
def twofactorconfig():
    if "userid" not in session:
        return redirect("/")
    if request.method == "POST":
        token = request.form.get("2fa")
        code = request.form.get("code")
        if pyotp.TOTP(code).verify(token):
            GLOBALS.DATABASE.ModifyQuery("UPDATE users SET OTPcode = ? WHERE userid = ?", (code, session['userid']))
            flash(message="2FA enrollment complete!", category="success")
            return redirect('/accountsettings')
        else:
            flash(message="Invalid code. A new QR Code has been generated.", category="warning")
            return redirect('/2faconfig')
    code = pyotp.random_base32()
    url = pyotp.totp.TOTP(code).provisioning_uri(session['email'], issuer_name="Robot Controller")
    return render_template("2faconfig.html",url=url,code=code)

@app.route("/2fa", methods=["GET","POST"])
def twofactor():
    if request.method == "POST":
        user = GLOBALS.DATABASE.ViewQuery("SELECT * FROM users WHERE userid = ?", (session['tempuserid'],))[0]
        token = request.form.get("2fa")
        code = user['OTPcode']
        if pyotp.TOTP(code).verify(token):
            session["userid"] = session['tempuserid']
            session['permission'] = user['permission']
            session['name'] = user['name']
            session["email"] = user["email"]
            return redirect('/dashboard')
    return render_template("2fa.html")





























# -----------------------------------------------------------------------------------
# CAMERA CODE-----------------------------------------------------------------------
# Continually gets the frame from the pi camera
def videostream():
    """Video streaming generator function."""
    while True:
        if GLOBALS.CAMERA:
            frame = GLOBALS.CAMERA.get_frame()
            if frame:
                yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n') 
            else:
                return '', 204
        else:
            return '', 204 

#embeds the videofeed by returning a continual stream as above
@app.route('/videofeed')
def videofeed():
    if GLOBALS.CAMERA:
        log("FLASK APP: READING CAMERA")
        """Video streaming route. Put this in the src attribute of an img tag."""
        return Response(videostream(), mimetype='multipart/x-mixed-replace; boundary=frame') 
    else:
        return '', 204
        
#----------------------------------------------------------------------------
#Shutdown the robot, camera and database
def shutdowneverything():
    log("FLASK APP: SHUTDOWN EVERYTHING")
    if GLOBALS.CAMERA:
        GLOBALS.CAMERA.stop()
    if GLOBALS.ROBOT:
        GLOBALS.ROBOT.safe_exit()
    GLOBALS.CAMERA = None; GLOBALS.ROBOT = None; GLOBALS.SOUND = None
    return

#Ajax handler for shutdown button
@app.route('/robotshutdown', methods=['GET','POST'])
def robotshutdown():
    shutdowneverything()
    return jsonify({'message':'robot shutdown'})

#Shut down the web server if necessary
@app.route('/shutdown', methods=['GET','POST'])
def shutdown():
    shutdowneverything()
    func = request.environ.get('werkzeug.server.shutdown')
    func()
    return jsonify({'message':'Shutting Down'})

@app.route('/logout')
def logout():
    shutdowneverything()
    session.clear()
    return redirect('/')

#---------------------------------------------------------------------------
#main method called web server application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True) #runs a local server on port 5000