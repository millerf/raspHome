    var conf;
    var timers = ["year", "month", "day", "hour", "min", "sec"]

    webiopi().ready(function() {
                var content = $("#content");
                var header = $("#header");
                
                // Get conf
                //webiopi().callMacro("getConf", [], updateConf);

                var time = $('<div id="time" class="time">');
                header.append(time);

                // Get system time 
                webiopi().callMacro("getTime", [], updateSysTime);
                // Refresh clock
                setInterval(function(){ webiopi().callMacro("getTime", [], updateSysTime);}, 1000);

                // Create command panel
        		var panel = $('<div class="panel">');
                //alert(map);
                       // Create boxes
                        var box = $('<div class="box">');
                        var main = $('<div class="main">');
                        // Create buttons
                               
                                // Description
                                var desc = $('<div class="desc">');
                                desc.append("Time");
                                main.append(desc);

                                // Activate button
                                var btn = webiopi().createButton("sendBtn", "set", setTime);
                                btn.attr("class", "LOW");
                                main.append(btn);

                                // Timer button
                                for (i=0;i<timers.length;i++) {
                                    id = timers[i];
                                    var btn = $('<input type="number" min="0" class="progVal" id="' + id + '" ><label for="' + id + '"> ' + id + '</label>');
                                main.append(btn);


                                box.append(main);
                                panel.append(box);    
                        }
		
                content.append(panel);

	webiopi().refreshGPIO(false);	
	});


    function updateConf(macro, args, response) {
        conf = jQuery.parseJSON(response);
                alert(conf);
        //return conf;
/*
        alert(data["volets"][0]["nom"]);
        map = data.volets;
        progs = data.progs;
        days = data.days;
        timers = data.timers;
        rank = data.rank;
*/

    }


    function updateSysTime(macro, args, response) {
        //alert(response);
        var timeList = jQuery.parseJSON(response);
        $("#time").html(timeList[0]+"<br>");
        $("#time").append(timeList[1]+"<br>");
        $("#time").append(timeList[2]);
    }

    function setTime() {
        var data = []
        for (i=0;i<timers.length;i++) {
            id = "#" + timers[i];
            data.push($(id).val())
        }
        webiopi().callMacro("setTime", data, updateSysTime);
    }


