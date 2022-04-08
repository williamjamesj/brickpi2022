// Changes the navbar to reflect the current page
function update_navbar(path) {
    try {
        dictionaryNavbar = {"/":"login","/login":"login","/dashboard":"dashboardnavbar","/sensor_view":"sensors","/accountsettings":"accountsettings","/logout":"logout","/missions":"missions"};
        document.getElementById(dictionaryNavbar[path]).classList.add("active");
    } catch (err) {

    }
}
