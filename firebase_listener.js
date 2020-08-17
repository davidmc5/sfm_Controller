

//this file is for the raspberry pi node.js

// Import Firebase API keys and controller credentials
//https://www.stanleyulili.com/node/node-modules-learn-how-to-import-and-use-functions-from-another-file/
//https://stackoverflow.com/a/7612052
const {apiKey, authDomain, databaseURL, storageBucket, serviceAccountCredentialsPath,siteId,
        password, email} = require('./google_services.js')

// Fine site ID for a known WAN IP
//https://stackoverflow.com/a/46615568
function findSiteId(siteIp){
  //returns the siteId for a given WAN IP, or null for unknown IP
  var sites = database.ref().child('sites');
  var query = sites.orderByChild("siteConfig/ip/wanIp").equalTo(siteIp);
  let siteid = 'NONE';

  return query.once('value').then(function(snapshot) {
    //returns the name of the SITEID
    snapshot.forEach(function (data){
      siteid = data.key;
    });
    console.log('SITEID FOUND: ' + siteid);
    return siteid;
  });
}

function getSiteId(siteIp){
  return findSiteId(siteIp).then(function(siteid){
    console.log('MERDA: ' + siteid);
  });
}


//import firebase from "firebase"; //for ES6 imports or TypeScript
var firebase = require("firebase");

//get a handle of the Firebase instance
config = {
    "apiKey": apiKey,
    "authDomain": authDomain,
    "databaseURL": databaseURL,
    "storageBucket" : storageBucket,
    "serviceAccount": serviceAccountCredentialsPath
}
firebase.initializeApp(config);


// Get a reference to the database service
var database = firebase.database();


//https://firebase.google.com/docs/auth/web/auth-state-persistence
firebase.auth().signInWithEmailAndPassword(email, password).catch(function(error) {
    	// Handle Errors here.
    	var errorCode = error.code;
    	var errorMessage = error.message;

    	console.log('Auth Error!');
    	console.log(errorCode);
    	console.log(errorMessage);
});



firebase.auth().onAuthStateChanged(function(user) {
      if (user) {
            // controller is signed in.
        	//write a log message
        	console.log('got autenticated!');

        	var uid = user.uid;
        	console.log('Authenticated uid: ' + uid);

        	///need to wait to access the database until the user is fully signed in!!!!
        	//ask stackoverflow why there are no examples of this on the web, about waiting for the
        	//auth state change before proceeding reading or writing to database!

        	//To write to database
        	//see this: https://firebase.google.com/docs/database/admin/save-data
          // var switches = database.ref('sites/' + siteId + "/switches");
          // var sensors = database.ref("controllers/" + controller + "/sensors");



          ///vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
          //Example for testing: It adds a new node to firebase
          var node = "123ABCD"
          var relays = 16
          //set database reference on that nodeId
          var newNode = database.ref('sites/' + siteId + '/nodes/' + node);
          //update database field
          //https://stackoverflow.com/questions/33610616/firebase-update-callback-to-detect-error-and-sucssess
          newNode.update({relays}).then(function(){
            console.log('Data updated!');
          }).catch(function(error) {
            console.log('Update error: ' + error);
          });
          ///^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

          //Read data ONCE (this works!)
          //https://firebase.google.com/docs/database/admin/retrieve-data#section-reading-once
          // var siteIps = database.ref('siteIps');
          // siteIps.once("value").then(function (snapshot) {
          //   console.log("SITEIPS:", snapshot.val());
          // });


          ////HELLO HANDSHAKE
          // Retrieve siteId with given WAN IP or null if unknown ip
          // https://stackoverflow.com/a/51614404
          //https://stackoverflow.com/a/40935483
          //https://stackoverflow.com/a/40455744
          // var sites = database.ref().child('sites');
          // var query = sites.orderByChild("siteConfig/ip/wanIp").equalTo("73.5.142.186");
          // // var query = sites.orderByChild("siteConfig/ip/wanIp").equalTo("73.5.142.187");
          // query.once('value').then(function(snapshot) {
          //   console.log(snapshot.val());
          //   console.log('SITES URL = ' + snapshot.ref); //prints the sites URL
          //
          //   console.log('KEY1 = ' + snapshot.ref.key); //prints the parent object name 'sites'
          //   console.log('KEY2 = ' + snapshot.key); //prints the parent object name 'sites'
          //
          //   // console.log('SITEID = ' + snapshot.ref.child.val); //undefined
          //   console.log('Project URL= ' + snapshot.ref.parent); // returns the project url
          //
          //   //returns the name of the SITEID
          //   snapshot.forEach(function (data){
          //     console.log(data.key);
          //   });
          // });

          //vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
          // FOR TESTING HELLO PROCESS
          // console.log('KAKA: ' +  getSiteId("73.5.142.186X") );
          // console.log('KOKO: ' + getSiteID(siteIp)
          getSiteId("73.5.142.186");
          //^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

          //remove all sensor data
          // sensors.remove();

        	//write to the database at the root reference "ref"
        	//On booting, reset all switches' states of the database to the default off.
        	// switches.set({
        	// 	bin_1_sw_1: false,
          //   bin_1_sw_2: false,
          //   bin_1_sw_3: false,
          //   bin_1_sw_4: false,
          //   bin_1_sw_5: false,
          //   bin_1_sw_6: false,
          //   bin_1_sw_7: false,
          //   bin_1_sw_8: false
        	// });

          /// GET Private and Public IP addresses
          var wanIp;
          var lanIp;
          //reference for firebase's IP fields
          var ip = database.ref('sites/' + siteId + '/siteConfig/ip');
          const { exec } = require('child_process');

          // Get Controller's Public IP
          // exec('dig +short myip.opendns.com @resolver1.opendns.com', (err, stdout, stderr) => {
          exec('curl ifconfig.me', (err, stdout, stderr) => {
            if (err) {
              //couldn't execute the command
              return;
            }
            //retrieve controller's public IP
            wanIp = stdout;
            console.log('wanIp: ' + wanIp);
            //Update WAN IP to Database
            ip.update({wanIp}).then(function(){
              console.log('Data updated!');
            }).catch(function(error) {
              console.log('Update error: ' + error);
            });
          });

          //Get controller's private IP
          //"hostname -I | awk '{print $1}'" //this returns only the ipv4
          exec('hostname -I', (err, stdout, stderr) => {
            if (err) {
              // node couldn't execute the command
              return;
            }
            lanIp = stdout;
            console.log('lanIp: ' + lanIp);
            ip.update({lanIp}).then(function(){
              console.log('Data updated!');
            }).catch(function(error) {
              console.log('Update error: ' + error);
            });
          });



          //////////////////////////////////////
          //SPAWN PYTHON CONTROLLER
          //////////////////////////////////////

          //vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
        	// // spawn python script
        	var spawn = require("child_process").spawn;
        	var pyProcess = spawn('python',["controller.py"]);
          //^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

          // THIS CALLBACK IS EXECUTED EVERYTIME A SWITCH IS MOVED
        	// Attach a listener to get a snapshot with the data that has changed
        	// and send that data to the python controller

          /////////////////////////////////////////////
          // GET SNAPSHOT WITH ALL SWITCH Data that changed
          //https://firebase.google.com/docs/reference/admin/node/admin.database.DataSnapshot
          /////////////////////////////////////////////
          /////// SITEID IS HARDCODED! PRI/SEC CONTROLLERS NEED TO LISTEN TO ALL SITEIDS - NEED TO FIX!!!
          var switches = database.ref('/sites/55347/switches');
          ////////////////////////////////////////////////

          switches.on('child_changed', function(snapshot) {
            // //print the switch ID that changed
            // console.log("Switch: " + snapshot.ref.key);
            // //Print the values of specific known fields
            // console.log("NodeID: " + snapshot.child("nodeId").val());
            // console.log("Switch State: " + snapshot.child("swState").val());
            // console.log("Switch Logic: " + snapshot.child("swLogic").val());

            ///Send switch status change to python
            var nodeId = snapshot.child("nodeId").val();
            var swState = snapshot.child("swState").val();
            var swLogic = snapshot.child("swLogic").val();

            //The new line character \n at the end is needed to flush the message
            // pyProcess.stdin.write('NodeID:' + nodeId + '\n');
            //The first parameter is the comand identifyer. ('SWITCH' = relay control)
            var message = 'SWITCH:' + nodeId + ':' + swState + ':' + swLogic;
            console.log("MESSAGE: " + message);
            pyProcess.stdin.write(message + '\n');


            // //get sensor data
            // pyProcess.stdout.on('data', (data) => {
            //   // Do something with the data returned from python script
            //   console.log(data.toString());
            // });
          });




          //get sensor data
          pyProcess.stdout.on('data', (data) => {
              // Here is the data received from python
              console.log("RECEIVED FROM CONTROLLER: " + data.toString());

              //get the sensorId:value pairs. remove the end carriage return
              //var rawValue = data.toString().replace(/\n/g, '')
              var rawValue = data.toString()
              //console.log(rawValue)
              //split id:value
              var splitIdValue = rawValue.split(":");
              var sensorId = splitIdValue[0].toString();
              var sensorValue = splitIdValue[1].toString();
              console.log(sensorId + " " + sensorValue);
              // sensors.update({[sensorId]:sensorValue})

              //send to database. Remove the newline character \n
              //sensors.set({c_1:data.toString().replace(/\n/g, '')})
          });

        	console.log('Listener is installed!');

      } else {
        	// User is not signed in.
        	// Handle Errors here.
        	console.log(user + ": Not Authorized!");
      }
});
