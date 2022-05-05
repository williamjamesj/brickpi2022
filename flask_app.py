import datetime
from flask import Flask, render_template, session, request, redirect, flash, url_for, jsonify, Response, logging
from interfaces import databaseinterface, camerainterface, soundinterface
import robot #robot is class that extends the brickpi class
import global_vars as GLOBALS #load global variables
import logging, time
from passlib.hash import sha256_crypt
import pyotp

#Creates the Flask Server Object and other necessary objects.
app = Flask(__name__); app.debug = True
SECRET_KEY = 'cRkgzGZbfkuY7sktRzk5qksUhKWYdZZIjuPpqZ4AbFg' #this is used for encrypting session tokens
app.config.from_object(__name__) #Set app configuration using above SETTINGS
logging.basicConfig(filename='logs/flask.log', level=logging.INFO)
GLOBALS.DATABASE = databaseinterface.DatabaseInterface('databases/RobotDatabase.db', app.logger)
EXEMPT_PATHS = ["/","/2fa","/favicon.ico"] # All of the paths that are not protected by authentication.

#Log messages
def log(message):
    app.logger.info(message)
    return

def logaction(form,power=0,degrees=0,duration=0,mission=0):
    GLOBALS.DATABASE.ModifyQuery("INSERT INTO actions (actiontype,actionpower,actiondegrees,actionduration,missionid,timestamp) VALUES (?,?,?,?,?,?)",(form,power,degrees,duration,mission,time.time()))
    GLOBALS.MAP.append([form,power,degrees,duration])
    return

@app.route("/mazeaccess", methods=['GET','POST'])
def return_maze():
    return jsonify(GLOBALS.MAP)

@app.route("/actionbackdoor")
def actionbackdoor():
    return jsonify(GLOBALS.DATABASE.ViewQuery("SELECT * FROM actions"))

# Before accessing ANY page (other than sign in pages), check if the user is logged in, as there is no public facing functionality for this website.
@app.before_request
def check_login():
    exempt_page = request.path in EXEMPT_PATHS or request.path.startswith("/static") # Check if it is one of the pages that is allowed (login and 2fa especially, to avoid a loop) or if it is a static file.
    logged_in = 'userid' in session
    if not (logged_in or exempt_page):
        return redirect("/") # Redirect to the login if the user has not logged in.
    

#create a login page
@app.route('/', methods=['GET','POST'])
def login():
    if 'userid' in session:
        return redirect('/dashboard')
    if request.method == "POST":
        email = request.form.get("email")
        userdetails = GLOBALS.DATABASE.ViewQuery("SELECT * FROM users WHERE email = ?", (email,))
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
                session["missionID"] = None
                return redirect('/dashboard')
            else:
                flash("Login unsuccessful.", "warning")
        else:
            flash("Login unsuccessful.", "warning")
    return render_template('login.html')    

# Load the ROBOT
@app.route('/robotload', methods=['GET','POST'])
def robotload():
    GLOBALS.MAP = []
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
        if GLOBALS.ROBOT.BP == "Give up all hope.":
            return jsonify(sensordict)
        GLOBALS.ROBOT.configure_sensors() #defaults have been provided but you can 
        GLOBALS.ROBOT.reconfig_IMU()
    if not GLOBALS.SOUND:
        log("FLASK APP: LOADING THE SOUND")
        GLOBALS.SOUND = soundinterface.SoundInterface()
    sensordict = GLOBALS.ROBOT.get_all_sensors()
    return jsonify(sensordict)

# ---------------------------------------------------------------------------------------
# Dashboard
@app.route('/dashboard', methods=['GET','POST'])
def robotdashboard():
    if request.method == "POST":
        location = request.form.get("location")
        notes = request.form.get("notes")
        missionid = session["lastMissionID"]
        GLOBALS.DATABASE.ModifyQuery("UPDATE missions SET location = ?, notes = ? WHERE missionID = ?",(location,notes,missionid))
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
        temp = int(open("/sys/class/thermal/thermal_zone0/temp").read().rstrip())/1000
        data["pitemp"] = temp
        data = GLOBALS.ROBOT.get_all_sensors()
    return jsonify(data)

@app.route('/sensor_view')
def sensor_view():
    data = {}
    if GLOBALS.ROBOT:
        data = GLOBALS.ROBOT.get_all_sensors()
        temp = int(open("/sys/class/thermal/thermal_zone0/temp").read().rstrip())/1000
        data["pitemp"] = temp
    return render_template('sensor_view.html',int=int, data = data)
# YOUR FLASK CODE------------------------------------------------------------------------

@app.route("/finecontrol", methods=["GET","POST"])
def finecontrol():
    if request.method == "POST":
        data = request.get_json()
        if data["action"] == "move" and GLOBALS.ROBOT:
            print("moving",data["power"], data["time"])
            GLOBALS.ROBOT.move_power_time(int(data["power"]), int(data["time"]),deviation=2)
        elif data["action"] == "turn":
            print("turning",data["power"], data["degrees"])
            GLOBALS.ROBOT.rotate_power_degrees_IMU(int(data["power"]), int(data["degrees"]))
        elif data["action"].split(" ")[0] == "say":
            print(" ".join(data["action"].split(" ")[1:]))
            GLOBALS.SOUND.say(" ".join(data["action"].split(" ")[1:]))
        return jsonify({})

    return render_template("finecontrol.html")

@app.route("/shoot", methods=["GET","POST"])
def shoot():
    data = {}
    if GLOBALS.ROBOT:
        GLOBALS.ROBOT.spin_medium_motor(-2000)
    return jsonify(data)

@app.route("/moveforward", methods=["GET","POST"])
def moveforward():
    power = 25
    duration = 3
    data = {}
    if GLOBALS.ROBOT:
        logaction("move",power=power, duration=duration,mission=session["missionID"])
        GLOBALS.ROBOT.move_power_time(power,duration,deviation=2.5)
    return jsonify(data)

@app.route("/moveright", methods=["GET","POST"])
def moveright():
    power = 25
    data = {}
    if GLOBALS.ROBOT:
        logaction("move",power=power, degrees=270,mission=session["missionID"])
        data = GLOBALS.ROBOT.rotate_power_degrees_IMU(power,-90,2)
    return jsonify(data)


@app.route("/moveleft", methods=["GET","POST"])
def moveleft():
    power = 25
    data = {}
    if GLOBALS.ROBOT:
        logaction("move",power=power, degrees=90,mission=session["missionID"])
        data = GLOBALS.ROBOT.rotate_power_degrees_IMU(power,90,2)
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

@app.route("/check_mission",methods=["POST"])
def check_mission():
    if session["missionID"] is not None:
        return jsonify({"status":"mission"})
    return jsonify({"status":"no mission"})


@app.route("/missions", methods=["GET","POST"]) # This is the view for the list of missions.
def missions():
    data = GLOBALS.DATABASE.ViewQuery("SELECT missions.missionID, name, email, missions.userid, startTime, endTime, notes, location, COUNT(actionid) AS actions FROM (missions INNER JOIN users ON users.userid = missions.userID) LEFT JOIN actions on missions.missionID = actions.missionid GROUP BY missions.missionID ORDER BY missions.startTime DESC;")
    return render_template("missions.html",data=data,datetime=datetime,int=int,str=str)

@app.route("/mission/<id>", methods=["GET","POST"]) # This is the view for an individual mission.
def mission(id):
    data = GLOBALS.DATABASE.ViewQuery("SELECT * FROM (missions LEFT JOIN users ON users.userid = missions.userid) LEFT JOIN actions ON actions.missionid = missions.missionID WHERE missions.missionID = ?",(id,))
    if request.method == "POST":
        location = request.form.get("location")
        notes = request.form.get("notes")
        if GLOBALS.DATABASE.ModifyQuery("UPDATE missions SET location = ?, notes = ? WHERE missionID = ?",(location,notes,id)):
            flash("Mission updated","success")
        else:
            flash("Mission update failed","danger")
        return redirect("/mission/"+id)
    return render_template("missionview.html", data=data, datetime=datetime, int=int, str=str)

@app.route("/start_mission", methods=["GET","POST"])
def start_mission():
    if "userid" in session:
        GLOBALS.DATABASE.ModifyQuery("INSERT INTO missions (userid,startTime) VALUES (?,?)",(session['userid'],int(time.time())))
        missionID = GLOBALS.DATABASE.ViewQuery("SELECT MAX(missionID) as M FROM missions")[0]["M"]
        session["missionID"] = missionID
    return jsonify({"data":"Mission Started."})

@app.route("/stop_mission", methods=["GET","POST"])
def stop_mission():
    if "userid" in session:
        GLOBALS.DATABASE.ModifyQuery("UPDATE missions SET endTime=? WHERE missionID=?",(int(time.time()),session["missionID"]))
        session["lastMissionID"] = session["missionID"]
        session["missionID"] = None
    return jsonify({"data":"Mission Ended."})
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
            if password != "":
                password = sha256_crypt.hash(password)
                GLOBALS.DATABASE.ModifyQuery("UPDATE users SET name = ?, email = ?, password = ? WHERE userid = ?", (name, email, password, session['userid']))
                flash("Account settings and password changed.","success")
            else:
                GLOBALS.DATABASE.ModifyQuery("UPDATE users SET name = ?, email = ? WHERE userid = ?", (name, email, session['userid']))
                flash("Account details updated successfully.","success")
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
    return render_template("2faconfig.html",url=url,code=code,email=session['email'])

@app.route("/2fa", methods=["GET","POST"])
def twofactor():
    if 'tempuserid' not in session:
        return redirect("/login")
    if request.method == "POST":
        user = GLOBALS.DATABASE.ViewQuery("SELECT * FROM users WHERE userid = ?", (session['tempuserid'],))[0]
        token = request.form.get("2fa")
        code = user['OTPcode']
        if pyotp.TOTP(code).verify(token):
            session["userid"] = session['tempuserid']
            session['permission'] = user['permission']
            session['name'] = user['name']
            session["email"] = user["email"]
            session["missionID"] = None
            return redirect('/dashboard')
        else:
            flash("Code invalid.", "warning")
    return render_template("2fa.html")

@app.route("/auto", methods=["GET","POST"])
def automatic():
    if session["missionID"] is not None:
        GLOBALS.ROBOT.search_maze(session["missionID"])
    else:
        GLOBALS.ROBOT.search_maze()
    print("Done.")
    return jsonify({})

@app.route("/return_home", methods=["GET","POST"])
def return_home():
    GLOBALS.HEAD_HOME = True
    return jsonify({})

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
    if GLOBALS.ROBOT:
        if GLOBALS.ROBOT.BP != "Give up all hope.":
            shutdowneverything()
    session.clear()
    return redirect('/')

#---------------------------------------------------------------------------
#main method called web server application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True) #runs a local server on port 5000