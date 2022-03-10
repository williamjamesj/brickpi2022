// Changes the navbar to reflect the current page
function update_navbar(path) {
    dictionaryNavbar = {"/login":"login","/dashboard":"dashboardnavbar","/sensors":"sensors","/account_settings":"accountsettings","/logout":"logout"};
    document.getElementById(dictionaryNavbar[path]).classList.add("active");
}
