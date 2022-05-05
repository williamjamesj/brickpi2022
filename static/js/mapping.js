/* ------------------------------------------------------------------------
- A Custom JS File uses JSXGraph - https://jsxgraph.uni-bayreuth.de/wp/about/index.html
--------------------------------------------------------------------------*/
var turtle = null;
var alpha = 0;
var movements = [];


var width = screen.width * 0.45;
var board = JXG.JSXGraph.initBoard('box',{ boundingbox: [-width, 300, width, -300], keepaspectratio:true });
turtle = board.create('turtle', [0,0], {strokeWidth:2, strokeColor: 'blue', arrow: {strokeWidth: 2, strokeColor: 'red'}});
turtle.setPenSize(3);
var victims = []


// // TURTLE EXAMPLE
// function drawmap() {
//    turtle.forward(2);
//    if (Math.floor(alpha / 360) % 2 === 0) {
//       turtle.left(1);        // turn left by 1 degree
//    } else {
//       turtle.right(1);       // turn right by 1 degree
//    }

//    alpha += 1;
//    if (alpha < 1440) {  // stop after two rounds
//        setTimeout(drawmap, 20); 
//    }
// }

function getMovements() {
   console.log("Send data")
   send_data("/mazeaccess", {}, processMovements)
}

function processMovements(results) {
   let originalLength = movements.length // This is the number of movements that the client has logged.
   let newLength = results.length // This is the number of movements that the server has sent.
   if (originalLength < newLength) { // This runs if there are new movements that the client is not aware of.
      var newMovements = results.slice(originalLength, newLength) // Create a list of the new movements.
      moveRobot(newMovements)
      // console.log (newMovements)
      movements = results
      setTimeout(getMovements, 1) // Only wait a millisecond to refresh, as it retrieves faster data, as the user has already waited for the turtle to move.
   }
   else {
      console.log("No new movements.")
      setTimeout(getMovements, 1000)
   }
}

function moveRobot(movements) {
   for (var i = 0; i < movements.length; i++) {
      var movement = movements[i];
      console.log(movement);
      if (movement[0] == "move") {
         if (movement[2] < 0) {
            turtle.left(movement[2]);
         }
         else if (movement[2] > 0) {
            turtle.right(movement[2]);
         }
         else if (movement[1] != 0) {
            turtle.forward(movement[1]);
         }
      } else if (movement[0] == "victim") {
         let victim = board.create('point', [turtle.X(),turtle.Y()]);
         victim.setLabel("Victim "+ (victims.length+1));
         victims.push(victim)

      }
      
   }
}
// drawmap();
getMovements();