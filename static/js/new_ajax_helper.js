//This ajax helper caters for files and does not require JQuery, an example of its use can be seen below:
/*
  In pythonanywhere you will need to link it within the HTML: <script src='/static/js/new_ajax_helper.js'></script>

  testinput = document.getElementById('testinput').value; //get data from form fields
  testfile = document.getElementById("testfile").files[0];
  fd = new FormData(); //create a form object since one does not exist
  fd.append("testinput", testinput); //name and value
  fd.append("testfile", testfile);
  new_ajax_helper('/test',defaulthandler,fd); //send the formobject to the url, you can define a callback 
*/

function new_ajax_helper(url, callback=defaulthandler, formobject=null, method='POST')
{
    //create a request object
    var xhr = new XMLHttpRequest();

    xhr.open(method, url, true);
    xhr.onreadystatechange = function() //callback function
    {
        if (xhr.readyState == 4) //4 means data received
        {
            results = JSON.parse(xhr.responseText); //change JSON into a Javascript object
            callback(results); //call the callback function
        }
    }
    xhr.send(formobject); //send the form data
}

function defaulthandler(results)
{
    console.log(results.data);
}
