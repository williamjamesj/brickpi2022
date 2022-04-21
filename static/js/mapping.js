/* ------------------------------------------------------------------------
- A Custom JS File uses JSXGraph - https://jsxgraph.uni-bayreuth.de/wp/about/index.html
--------------------------------------------------------------------------*/
var turtle = null;
var alpha = 0;
var movements = [];

function load_map()
{
   var width = screen.width * 0.45;
    var brd = JXG.JSXGraph.initBoard('box',{ boundingbox: [-width, 300, width, -300], keepaspectratio:true });
    turtle = brd.create('turtle',[0, 0], {strokeOpacity:0.5});
    turtle.setPenSize(3);
    turtle.right(90);
}

// TURTLE EXAMPLE
function drawmap() {
   turtle.forward(2);
   if (Math.floor(alpha / 360) % 2 === 0) {
      turtle.left(1);        // turn left by 1 degree
   } else {
      turtle.right(1);       // turn right by 1 degree
   }

   alpha += 1;
   if (alpha < 1440) {  // stop after two rounds
       setTimeout(drawmap, 20); 
   }
}

function getMovements() {
   send_data("/mazeaccess", {}, drawRobot)
}

function drawRobot(results) {
   let originalLength = movements.length
   let newLength = results.length
   
}
load_map();
// drawmap();

console.log("doot")