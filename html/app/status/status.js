
        var rrdDir = "status/";
        var rrdTemp = rrdDir + "temp.rrd";
        var rrdHr = rrdDir + "hr.rrd";
        var rrdFan = rrdDir + "fan.rrd";
        var rrdPool = rrdDir + "pool.rrd";
        var rrdClouds = rrdDir + "clouds.rrd";
        var rrdWater= rrdDir + "water.rrd";


        var graph_opts={legend: { noColumns:4}, yaxis: { min: 0, position: "right" }, lines: { show: true } };
        var hr_graph_opts={legend: { noColumns:4}, yaxis: { min: 0, max: 100, position: "right" }, lines: { show: true } };
        var onoff_graph_opts={legend: { noColumns:4}, yaxis: { min: 0, max: 1, position: "right" }, lines: { show: true } };
        var clouds_graph_opts={legend: { noColumns:4}, yaxes: [ { min: 0, max: 100, position: "left" }, { min: 0, position: "right" } ] , lines: { show: true } };

        var ds_graph_opts={'In':{ label: 'In', color: "#ff8000",
                                    checked: true,
                                    lines: { show: true, fill: false, fillColor:"#ffff80"} },
                            'Out':{ label: 'Out', color: "#00c0c0",
                                    checked: true,
                                    lines: { show: true, fill: false} }
                        };

        var water_ds_graph_opts={'temp':{ label: 'Temp', color: "#0000cc",
                                    checked: true,
                                    lines: { show: true, fill: false, fillColor:"#ffff80"} },
                        };

        var fan_ds_graph_opts={'fan':{ label: 'fan', color: "#880000",
                                    checked: true,
                                    lines: { show: true, fill: true, fillColor: { colors: ["#330000", "#880000"] } } },
                        };

        var onoff_ds_graph_opts={'on':{ label: 'pool', color: "#880000",
                                    checked: true,
                                    lines: { show: true, fill: true, fillColor: { colors: ["#330000", "#880000"] } } },
                        };

        var clouds_ds_graph_opts={'clouds':{ label: 'Cloudiness (%)', color: "#333333",
                                    checked: true,
                                    lines: { show: true, fill: true, fillColor: { colors: ["#bbbbbb", "#333333"] } } },
                            'rain':{ label: 'Rain (mm/h)', color: "#0000cc", yaxis: 2,
                                    checked: true,
                                    lines: { show: true, fill: false} }
                        };
 
        var rrdflot_defaults={ graph_height: "15em", 
                                graph_width: "40em", 
                                graph_only: false, 
                            };



        simple = new rrdFlotAsync("temp",rrdTemp,null,graph_opts,ds_graph_opts,rrdflot_defaults);
        simple = new rrdFlotAsync("hr",rrdHr,null,hr_graph_opts,ds_graph_opts,rrdflot_defaults);
        simple = new rrdFlotAsync("clouds",rrdClouds,null,clouds_graph_opts,clouds_ds_graph_opts,rrdflot_defaults);
        simple = new rrdFlotAsync("fan",rrdFan,null,onoff_graph_opts,fan_ds_graph_opts,rrdflot_defaults);
        simple = new rrdFlotAsync("pool",rrdPool,null,onoff_graph_opts,onoff_ds_graph_opts,rrdflot_defaults);
        simple = new rrdFlotAsync("water",rrdWater,null,graph_opts,water_ds_graph_opts,rrdflot_defaults);

