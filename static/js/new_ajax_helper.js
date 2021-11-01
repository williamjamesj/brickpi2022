//This ajax helper caters for files and does not require JQuery, an example of its use can be seen below:
/*
  testinput = document.getElementById('testinput').value; //get data from form fields
  testfile = document.getElementById("testfile").files[0];
  fd = new FormData(); //create a form object since one does not exist
  fd.append("testinput", testinput); //name and value
  fd.append("testfile", testfile);
  new_ajax_helper('/test',fd); //send the formobject to the url, you can define a callback 
*/

function new_ajax_helper(url, formobject=null, callback=defaulthandler, method='POST')
{
    //create a request object
    var xhr = new XMLHttpRequest();

    xhr.open(method, url, true);
    xhr.onreadystatechange = function() //callback function
    {
        if (xhr.readyState == 4) //4 means data received
        {
            results = JSON.parse(xhr.responseText); //change into a object
            callback(results);
        }
    }
    xhr.send(formobject); //send the form data
}

function defaulthandler(results)
{
    console.log(results.data);
}
