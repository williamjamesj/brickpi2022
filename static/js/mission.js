// This file contains the functions that pertain to starting, stopping and monitoring the progress of a mission.
/*
     Mission Logic:
        1. When the page loads, the server is asked if there is a current mission.
        2. Mission starts when the user clicks the button.
        3. Server creates a mission id, which is saved inthe user's session variable.
        4. All actions that the robot performs are then assigned that mission id.
        5. Once the user then stops the mission, the timestamp is recorded again (calculating duration), and stopping further actions from being assigned the mission id.


*/
var mission = false
send_data("/check_mission", {}, responseDestination=mission_check);

function update_mission() {
    if (mission) {
        button = document.getElementById("mission");
        button.innerHTML = "Stop Mission";
        button.className = "btn btn-danger";
    } else {
        button = document.getElementById("mission");
        button.innerHTML = "Start Mission";
        button.className = "btn btn-success";
    }
}

function toggle_mission() {
    if (!mission) {
        send_data("/start_mission", {});
        mission = true;
    } else {
        send_data("/stop_mission", {});
        mission = false;
    }
    update_mission();
}
function mission_check(result) {
    if (result.status == "mission") {
        mission = true;
    } else {
        mission = false;
    }
    update_mission();
}