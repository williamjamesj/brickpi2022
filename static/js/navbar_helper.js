// Changes the navbar to reflect the current page
function update_navbar(path) {
    try {
        dictionaryNavbar = {"/":"login",  // This dictionary contains all of the url paths and their corresponding navbar elements
                            "/login":"login",
                            "/dashboard":"dashboardnavbar",
                            "/sensor_view":"sensors",
                            "/accountsettings":"accountsettings",
                            "/logout":"logout",
                            "/missions":"missions"};
        document.getElementById(dictionaryNavbar[path]).classList.add("active"); // This adds the active class to the navbar element, emphasising the current page in the navbar.
    } catch (err) { // This catch block supresses an error when the user is on a page that is not in the dictionary, as an error is thrown in this case.

    }
}
