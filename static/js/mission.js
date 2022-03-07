// This file contains the functions that pertain to starting, stopping and monitoring the progress of a mission.
/*
     Mission Logic:
        1. When the page loads, the server is asked if there is a current mission.
        2. Mission starts when the user clicks the button.
        3. Timestamp is recorded and sent to the server, where a mission id is created and assigned to the user's session variable.
        4. All actions that the robot performs are then assigned that mission id.
        5. Once the user then stops the mission, the timestamp is recorded again (calculating duration), and stopping further actions from being assigned the mission id.


*/
var mission = false
function start_mission() {
    if (!mission) {
        send_data("/start_mission", {});
        button = document.getElementById("mission");
        button.innerHTML = "Stop Mission";
        button.className = "btn btn-danger";
        mission = true;
    } else {
        send_data("/stop_mission", {});
        button = document.getElementById("mission");
        button.innerHTML = "Start Mission";
        button.className = "btn btn-success";
        mission = false;
    }
}