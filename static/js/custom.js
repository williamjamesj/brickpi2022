/* This is your custom javascript, it has been embedded into layout.html. 
Any scripts here are available through out the website */

function shutdown()
{
    alert("shutdown");
    new_ajax_helper('/shutdown');
}