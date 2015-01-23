
    //"use strict";

    // Get app name
    var path = window.location.pathname;
    var app = path.split('/')[2];


    webiopi().ready(function() {

                // Get conf
                webiopi().callMacro("getConf", [app], updateConf);
                
                // Get system time
                var header = $("#header");
                var time = $('<div id="time" class="time">');
                header.append(time);
                var menu = $('<div id="menu" class="header-right">');
                var config = $('<a href="/app/config"> Config </a>');
                var debug = $('<a href="/app/debug"> debug </a>');
                var home = $('<a href="/"> Home </a>');
                //menu.append(config);
                //menu.append(debug);
                menu.append(home);
                //var title = $('<div id="title" class="title">');
                //title.append("- Prout -");
                //header.append(title);
                header.append(menu);
                webiopi().callMacro("getTime", [], updateSysTime);
                // Refresh clock
                setInterval(function(){ webiopi().callMacro("getTime", [], updateSysTime);}, 600000);
                

                /*
                // Set days checkboxes as buttons with jquery-ui
                $(function() {
                        for (j=1; j>=0; j--) {
                            for (var k=0; k<rank.length; k++) {
                                // Prog buttons
                                for (var i=0; i<map.length; i++) {
                                    var btn = $("#progBtn" + rank[k] + map[i]["gpio" + j]);
                                    btn.buttonset();
                                }
                                var btnAll = $("#progBtnAll" + rank[k] + j);
                                btnAll.buttonset();

                                // Day buttons
                                for (var i=0; i<map.length; i++) {
                                    var btn = $("#dayBtn" + rank[k] + map[i]["gpio" + j]);
                                    btn.buttonset();
                                }
                                var btnAll = $("#dayBtnAll" + rank[k] + j);
                                btnAll.buttonset();

                                // Timer buttons
                                for (l=1; l<timers.length; l++) {
                                    if (timers[l] == "hour") { var max = 23; }
                                    else if (timers[l] == "minute") { var max = 60; }
                                    for (var i=0; i<map.length; i++) {
                                        var btn = $("#" + timers[l] + rank[k] + map[i]["gpio" + j]);
                                        btn.spinner({step: 1, min: 0, max: max, numberFormat: "n"});
                                    }                                
                                    var btnAll = $("#" + timers[l] + "All" + rank[k] + j);
                                    btnAll.spinner({step: 1, min: 0, max: max, numberFormat: "n"});
                                }
                                for (var i=0; i<map.length; i++) {
                                    var btn = $("#timerBtn" + rank[k] + map[i]["gpio" + j]);
                                    btn.buttonset();
                                }
                                var btnAll = $("#timerAll" + rank[k] + j);
                                btnAll.buttonset();
                            }
                        }
                });
                */

	webiopi().refreshGPIO(true);	
	});


    var conf, map, progs, days, parameters, rank;

    function updateConf(macro, args, response) {
        conf = $.parseJSON(response);
        days = conf.days;
        map = conf.map;
        progs = conf.progs;
        parameters = conf.parameters;
        ranks = conf.ranks;
        master = conf.master;

                var content = $("#content");
                var header = $("#header");

                var title = $('<div id="title" class="title">');
                title.append(conf["title"]);
                header.append(title);


                // Create command panel
                // Create boxes for each command
                for (var i=0; i<=map.length; i++) {
                       // Create boxes
                        var box = $('<div class="box">');
                        var main = $('<div class="main">');
                        var cfg = map[i];
                        if (cfg != undefined) {
                        // Create buttons for each command
                               
                                // Description
                                var desc = $('<div class="desc">');
                                desc.append(cfg["name"]);
                                main.append(desc);
                                box.append(main);

                                // Program buttons
                                
                                var cmd = cfg["cmd"];
                            if (cmd != undefined) {
                                for (j=0; j<cmd.length; j++) {
                                        var gpio = cmd[j]["gpio"];
                                        // Get progs
                                        for (var k=0; k<ranks; k++) {
                                                webiopi().callMacro("getProg", [app, "get", k, i, j], update);
                                        }

                                        // Create buttons
                                        var boxBtn = $('<div class="boxBtn">');


                                        // Remote button
                                        var label = cmd[j]["label"];
                                        var remoteBtn = webiopi().createMacroButton("gpio" + gpio, label, "actRemote", [app, i, j]);
                                        //var remoteBtn = webiopi().createMacroButton("gpio" + gpio, label, "setProg", [app, "remote", "Z", i, j, "*", "*", "*"]);
                                        boxBtn.append(remoteBtn);


                                        for (var k=0; k<ranks; k++) {
                                            var boxProg = $('<div class="boxProg">');                          
                                            // Set button
                                            var setBtn = createProgButton("set" + k + gpio, "x", setFunc, [gpio, k, i, j]);
                                            boxProg.append(setBtn);

                                            // Prog type buttons
                                            if (progs.length > 1) {
                                                var idProg = "progBtn" + k + gpio;
                                                var progBtn = $('<div class="progBtn" id="' + idProg + '">');
                                                for (var l=0; l<progs.length; l++) {
                                                var id = progs[l]["name"] + k + gpio;
                                                var label = progs[l]["label"];
                                                var btn = $('<input type="radio" id="' + id + '" name="' + idProg + '"><label for="' + id + '">' + label + '</label>');
                                                progBtn.append(btn);
                                                }
                                                boxProg.append(progBtn);
                                            }



                                            // Timer buttons
                                            if (parameters != undefined) {
                                                var idParam = "paramBtn" + k + gpio;
                                                var paramBtn = $('<div class="paramBtn" id="' + idParam + '">');
                                                for (var l=0; l<parameters.length; l++) {
                                                    var id = parameters[l]["id"] + k + gpio;
                                                    var label = parameters[l]["label"];
                                                    var min = parameters[l]["min"];
                                                    var btn = $('<input type="number" min="' + min +'" class="progVal" id="' + id + '" ><label for="' + id + '">' + label + '</label>');
                                                    paramBtn.append(btn);
                                                }
                                                boxProg.append(paramBtn);
                                            }


                                            // Day buttons
                                            if (days != undefined) {
                                                var idDay = "dayBtn" + k + gpio;
                                                var dayBtn = $('<div class="dayBtn" id="' + idDay + '">');
                                                for (var l=0; l<days.length; l++) {
                                                    var id = "day" + l + k + gpio;
                                                    var btn = $('<input type="checkbox" id="' + id + '"><label for="' + id + '">' + days[l] + '</label>');
                                                    dayBtn.append(btn);
                                                }
                                                boxProg.append(dayBtn);
                                            }

                                            boxBtn.append(boxProg);
                                        }
                                        box.append(boxBtn);
                                }
                            }
                            content.append(box);    
                        }
                }


                // Create box for master command
                        // Create box
                        var box = $('<div class="box">');
                        var main = $('<div class="main">');
                        if (master != undefined) {
                        // Create buttons for master command
                               
                            var cfg = master[0];
                            
                                // Description
                                var desc = $('<div class="desc">');
                                desc.append(cfg["name"]);
                                main.append(desc);
                                box.append(main);

                                // Program buttons
                                
                                var cmd = cfg["cmd"];
                                for (j=0; j<cmd.length; j++) {

                                        // Create buttons
                                        var boxBtn = $('<div class="boxBtn">');

                                        
                                        // Remote button
                                        var label = cmd[j]["label"];
                                        var remoteBtn = webiopi().createMacroButton("remoteAll" + j, label, "actRemoteAll", [app, j]);

                                        //var remoteBtn = webiopi().createMacroButton("remoteAll" + j, label, "setProgAll", [app, "remote", "Z", j, "*", "*", "*"]);
                                        remoteBtn.attr("class", "LOW");
                                        boxBtn.append(remoteBtn);
                                        

                                        for (var k=0; k<ranks; k++) {
                                            var boxProg = $('<div class="boxProg">');                                                           
                                            // Set button
                                            var setBtn = createProgButton("setAll" + k + j, "x", setFuncAll, [k, j]);
                                            setBtn.attr("class", "progOff");
                                            boxProg.append(setBtn);
                                            

                                            // Prog type buttons
                                            if (progs.length > 1) {
                                                var idProg = "progBtnAll" + k + j;
                                                var progBtn = $('<div class="progBtn" id="' + idProg + '">');
                                                for (var l=0; l<progs.length; l++) {
                                                var id = progs[l]["name"] + "All" + k + j;
                                                var label = progs[l]["label"];
                                                var btn = $('<input type="radio" id="' + id + '" name="' + idProg + '"><label for="' + id + '">' + label + '</label>');
                                                progBtn.append(btn);
                                                }
                                                boxProg.append(progBtn);
                                            }



                                            // Timer buttons
                                            if (parameters != undefined) {
                                                var idParam = "paramBtnAll" + k + j;
                                                var paramBtn = $('<div class="paramBtn" id="' + idParam + '">');
                                                for (var l=0; l<parameters.length; l++) {
                                                    var id = parameters[l]["id"] + "All" + k + j;
                                                    var label = parameters[l]["label"];
                                                    var min = parameters[l]["min"];
                                                    var btn = $('<input type="number" min="' + min +'" class="progVal" id="' + id + '" ><label for="' + id + '">' + label + '</label>');
                                                    paramBtn.append(btn);
                                                }
                                                boxProg.append(paramBtn);
                                            }


                                            // Day buttons
                                            if (days != undefined) {
                                                var idDay = "dayBtnAll" + k + j;
                                                var dayBtn = $('<div class="dayBtn" id="' + idDay + '">');
                                                for (var l=0; l<days.length; l++) {
                                                    var id = "day" + l + "All" + k + j;
                                                    var btn = $('<input type="checkbox" id="' + id + '"><label for="' + id + '">' + days[l] + '</label>');
                                                    dayBtn.append(btn);
                                                }
                                                boxProg.append(dayBtn);
                                            }

                                            boxBtn.append(boxProg);
                                        }
                                        box.append(boxBtn);
                                }
                                content.append(box);    
                        }





    }


    function updateSysTime(macro, args, response) {
        //alert(response);
        var timeList = $.parseJSON(response);
        $("#time").html(timeList[0]+" "+timeList[1]+"<br>");
        $("#time").append(timeList[2]);
    }


    function createProgButton(id, label, callback, args) {
        var button = $('<button type="button" class="Default">');
        button.attr("id", id);
        button.text(label);
        if ((callback != undefined)) {
            button.on("click", null, args, function (event) { callback(event.data); });
        }
        return button;
    }



    function setFunc(val) {
        var data = [];
        var gpio = val[0];
        var rank = val[1];
        // Insert app name into data list
        data.push(app);

        // Insert program type into data list
        if (progs.length > 1) {
            for (var i=0; i<progs.length; i++) {
                if ($("#" + progs[i]["name"] + rank + gpio).is(':checked') == true) {
                    data.push(progs[i]["name"]);
                }
            }
        }
        else { data.push(progs[0]["name"]); }


        // Insert values into data list
        for (var i=1; i<val.length; i++) {
            data.push(val[i]);
        }

        // Insert checked days
        if (days != undefined) {
            var d = "";
            for (var i=0; i<days.length; i++) {
                if ($("#" + "day" + i + rank + gpio).is(':checked') == true) {
                    d += i;
                }
            }
            //alert(d);
            data.push(d);
        }
        else { data.push("0123456"); }

        // Insert user values
        if (parameters != undefined) {
            for (var i=0; i<parameters.length; i++) {
                data.push($("#" + parameters[i]["id"] + rank + gpio).val());
            }
        }
        //alert(data);
        webiopi().callMacro("setProg", data, update);
    }


    function setFuncAll(val) {
        var data = [];
        var rank = val[0];
        var cmd = val[1];
        // Insert app name into data list
        data.push(app);

        // Insert program type into data list
        if (progs.length > 1) {
            for (var i=0; i<progs.length; i++) {
                if ($("#" + progs[i]["name"] + "All" + rank + cmd).is(':checked') == true) {
                    data.push(progs[i]["name"]);
                }
            }
        }
        else { data.push(progs[0]["name"]); }


        // Insert values into data list
        for (var i=0; i<val.length; i++) {
            data.push(val[i]);
        }

        // Insert checked days
        if (days != undefined) {
            var d = "";
            for (var i=0; i<days.length; i++) {
                if ($("#" + "day" + i + "All" + rank + cmd).is(':checked') == true) {
                    d += i;
                }
            }
            //alert(d);
            data.push(d);
        }
        else { data.push("0123456"); }

        // Insert user values
        if (parameters != undefined) {
            for (var i=0; i<parameters.length; i++) {
                data.push($("#" + parameters[i]["id"] + "All" + rank + cmd).val());
            }
        }
        //alert(data);
        webiopi().callMacro("setProgAll", data, update);
    }



    // Update prog function
    function update(macro, args, response) {
        //if (macro != "getProg") { alert(response);}
        //alert(response)
        var progList = $.parseJSON(response);
        if (macro != "setProgAll") {
            updateProg(macro, args, progList);
        }
        else {
            for (var j=0; j<progList.length; j++) {
                // alert(progList[j]);
                var prog = $.parseJSON(progList[j]);
                updateProg(macro, args, prog);
            }
        }
    }


    // Set prog buttons
    function updateProg(macro, args, prog) {
        //if (macro != "getProg") { alert(prog.type);}
        //alert(prog.type);
        var rank = args[2];
        var idx = args[4];

        // Set button
        var btn = $("#set" + rank + prog.gpio);
        if (prog.type != null && prog.type != "error") {
            btn.attr("class", "progOn");
        }
        else { 
            btn.attr("class", "progOff");
        }

        // Prog buttons
        if (progs.length > 1) {
            for (var i=0; i<progs.length; i++) {
                    var name = progs[i]["name"];
                    var btn = $("#" + name + rank + prog.gpio);
                    // Disable if a program is running
                    if (prog.type != null && prog.type != "error") {
                            // Check box if prog is selected
                            if (name == prog.type) {
                                btn.attr("checked", true);
                            }
                            else {
                                btn.attr("checked", false);
                            }
                            btn.attr("disabled", true);
                    }
                    else { btn.attr("disabled", false); }
                /*if (prog.type != null && prog.type != "error") {
                    alert(name)
                    alert(btn.attr("checked"))
                }*/
            }
        }

        // Day buttons
        if (days != undefined) {
            // Alert if days is invalid
            if (prog.type == "error" && prog.day_of_week == null) {
                    alert("Selection du jour invalide !")
            }
            for (var i=0; i<days.length; i++) {
                    var btn = $("#" + "day" + i + rank + prog.gpio);
                    // Disable if a program is running
                    if (prog.type != null && prog.type != "error") {
                            btn.attr("disabled", true);
                            // Check box if day is selected
                            var result = prog.day_of_week.match(i);
                            if (result != null) { btn.attr("checked", true); }
                            else { btn.attr("checked", false); }
                    }
                    else { btn.attr("disabled", false); }
            }
        }

        // Parameters buttons
        if (parameters != undefined) {
            for (var i=0; i<parameters.length; i++) {
                    // Select buttons from macro
                    var btn = $("#" + parameters[i]["id"] + rank + prog.gpio);
                    var btnAll = $("#" + parameters[i]["id"] + "All" + rank + idx);
                    // Disable and set clock data if a program is running
                    if (prog.type != null && prog.type != "error") {
                            btn.attr("disabled", true);
                            btn.val(prog[parameters[i]["id"]]);
                    }
                    // Else enable and set data to zero
                    else {
                            btn.attr("disabled", false);
                            //btn.val("0"); 
                    }
                    // Set to error state if invalid
                    if (prog.type == "error" && prog[parameters[i]["id"]] == null) {
                            if (macro == "setProgAll") { btnAll.attr("class", "progError"); }
                            else { btn.attr("class", "progError"); }
                    }
                    else {
                            btn.attr("class", "progVal");
                            if (macro == "setProgAll") { btnAll.attr("class", "progVal"); }
                    }
            }
        }
    }

