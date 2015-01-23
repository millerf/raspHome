#!/usr/bin/python
# -*- coding:utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os, sys, re, rrdtool
from optparse import OptionParser



parser = OptionParser()
parser.add_option("-t", "--temp",
                  action="store_true", dest="tempOn", default=False,
                  help="create temp graph")
parser.add_option("-r", "--rh",
                  action="store_true", dest="hrOn", default=False,
                  help="create relative humidity graph")
parser.add_option("-c", "--clouds",
                  action="store_true", dest="cloudsOn", default=False,
                  help="create clouds graph")
parser.add_option("-d", "--dir", 
                  action="store", type="string", dest="graphdir", default="/media/dnld/",
                  help="write graph to dir")

(options, args) = parser.parse_args()


# Webiopi dir
webio_dir = "/home/pi/homeiopi/"

# RRDs
climatDir = webio_dir + "html/app/climat/"
climatIn_rrd = climatDir + "climatIn.rrd"
climatOMF_rrd = climatDir + "climatOMF.rrd"
cloudsOMF_rrd = climatDir + "cloudsOMF.rrd"
climatOWM_rrd = climatDir + "climatOWM.rrd"
cloudsOWM_rrd = climatDir + "cloudsOWM.rrd"
fan_rrd = climatDir + "fan.rrd"

# Graphs files
tempgraph = options.graphdir + "temp.png"
hrgraph = options.graphdir + "hr.png"
cloudsgraph = options.graphdir + "clouds.png"

duree = args[0]

# Calcul de l'interval de l'axe x
match = re.search('(\d+)([a-zA-Z_])', duree)
try:
    if match:
        n, m = match.group(1), match.group(2)
        hours = {'h': 1, 'd': 24, 'w': 168, 'm': 720}
        t = int(n) * int(hours[m])
        if t <= 6:
            xgrid = "HOUR:1:HOUR:1:HOUR:1:0:%R"
        elif 6 < t <= 24:
            xgrid = "HOUR:2:HOUR:2:HOUR:2:0:%R"
        elif 24 < t <= 72:
            xgrid = "HOUR:4:HOUR:4:HOUR:4:0:%Hh"
        elif 72 < t <= 240:
            xgrid = "DAY:1:DAY:1:DAY:1:86400:%a %d"
        elif 240 < t <= 720:
            xgrid = "DAY:2:DAY:2:DAY:2:0:%d/%m"
        elif 720 < t <= 2160:
            xgrid = "DAY:7:DAY:7:DAY:7:0:%d/%m"
        elif 2160 < t <= 8760:
            xgrid = "MONTH:1:MONTH:1:MONTH:1:2592000:%b"
        else:
            print ("error: duree inconnue: %sh" % t)
except:
    print sys.exc_info()


# Parametres communs
common = ["--imgformat", "PNG",
    "--end", "now",
    "--start", "end-" + duree,
    "--width", "1200",
    "--height", "600",
    "--zoom", "2",
    "--full-size-mode",
    "--border", "0",
    "--x-grid", xgrid,
    "--grid-dash", "1:0",
    "--right-axis", "1:0",
    "--font", "TITLE:16:.",
    "--font", "AXIS:10:.",
    "--font", "UNIT:16:.",
    "--font", "LEGEND:12:.",
    "--color", "BACK#333333",
    "--color", "CANVAS#333333",
    "--color", "AXIS#708090",
    "--color", "FONT#708090",
    "--color", "MGRID#70809033",
    "--slope-mode"]


# Creation des graphs

if options.tempOn:
    print "creating temp graph ..."
    temp = rrdtool.graph(tempgraph,
        common,
        "--title", "Temperature (°C)",
        "--lower-limit", "0",
        "--upper-limit", "25",
        "--y-grid", "2:1",
        "DEF:ds0=" + climatIn_rrd + ":temp:AVERAGE",
        "DEF:ds1=" + climatOMF_rrd + ":temp:AVERAGE",
        "DEF:ds2=" + climatOWM_rrd + ":temp:AVERAGE",
        "VDEF:ds0last=ds0,LAST",
        "VDEF:ds1last=ds1,LAST",
        "LINE3:ds0#FF8C00:tempIn\:\\g",
        "GPRINT:ds0last:%3.1lf °C",
        "LINE3:ds1#008B8B:tempOMF\:\\g",
        "GPRINT:ds1last:%3.1lf °C\\u",
        "LINE3:ds2#7B68EE88:tempOWM\\r:dashes=2,10")
    print "done! file= %s" % (tempgraph)

if options.hrOn:
    print "creating hr graph ..."
    hr = rrdtool.graph(hrgraph,
        common,
        "--title", "Humidité Relative (%)",
        "--lower-limit", "0",
        "--upper-limit", "100",
        "--rigid",
        "--y-grid", "10:1",
        "DEF:ds0=" + climatIn_rrd + ":hr:AVERAGE",
        "DEF:ds1=" + climatOMF_rrd + ":hr:AVERAGE",
        "DEF:ds2=" + climatOWM_rrd + ":hr:AVERAGE",
        "DEF:ds3=" + fan_rrd + ":fan:AVERAGE",
        "VDEF:ds0last=ds0,LAST",
        "VDEF:ds1last=ds1,LAST",
        "CDEF:m3=ds3,100,*",
        "LINE3:ds0#FF8C00:hrIn\:\\g",
        "GPRINT:ds0last:%3.1lf %%",
        "LINE3:ds1#008B8B:hrOMF\:\\g",
        "GPRINT:ds1last:%3.1lf %%\\u",
        "LINE3:ds2#7B68EE88:hrOWM:dashes=2,10",
        "AREA:m3#90EE9033:fan\\r")
    print "done! file= %s" % (hrgraph)


if options.cloudsOn:
    print "creating clouds graph ..."
    clouds = rrdtool.graph(cloudsgraph,
        common,
        "--vertical-label", "Cloudiness (%)",
        "--lower-limit", "0",
        "--upper-limit", "100",
        "--rigid",
        "--y-grid", "10:1",
        "--right-axis", "0.1:0",
        "--right-axis-label", "Precipitations (mm/h)",
        "DEF:ds0=" + cloudsOMF_rrd + ":clouds:AVERAGE",
        "DEF:ds1=" + cloudsOWM_rrd + ":clouds:AVERAGE",
        "DEF:ds2=" + cloudsOMF_rrd + ":rain:AVERAGE",
        "DEF:ds3=" + cloudsOWM_rrd + ":rain:AVERAGE",
        "CDEF:m2=ds2,10,*",
        "CDEF:m3=ds3,10,*",
        "LINE3:ds0#008B8B:cloudsOMF",
        "LINE3:ds1#7B68EE22:cloudsOWM\\u",
        "LINE3:m2#008B8B:rainOMF:dashes=2,10",
        "LINE3:m3#7B68EE22:rainOWM\\r:dashes=2,10:dash-offset=10")
    print "done! file= %s" % (cloudsgraph)

'''
print "creating temp graph ..."
temp = rrdtool.graph(tempgraph,
    common,
    "--title", "Temperature (°C)",
    "--lower-limit", "0",
    "--upper-limit", "25",
    "--y-grid", "2:1",
    "DEF:ds0=" + climat_rrd + ":tempIn:AVERAGE",
    "DEF:ds1=" + climat_rrd + ":tempOut:AVERAGE",
    "DEF:ds2=" + climat2_rrd + ":tempOWM:AVERAGE",
    "VDEF:ds0last=ds0,LAST",
    "VDEF:ds1last=ds1,LAST",
    "LINE3:ds0#FF8C00:tempIn\:\\g",
    "GPRINT:ds0last:%3.1lf °C",
    "LINE3:ds1#008B8B:tempOut\:\\g",
    "GPRINT:ds1last:%3.1lf °C\\u",
    "LINE3:ds2#7B68EE88:tempOWM\\r:dashes=2,10")
print "done! file= %s" % (tempgraph)


print "creating hr graph ..."
hr = rrdtool.graph(hrgraph,
    common,
    "--title", "Humidité Relative (%)",
    "--lower-limit", "0",
    "--upper-limit", "100",
    "--rigid",
    "--y-grid", "10:1",
    "DEF:ds0=" + climat_rrd + ":hrIn:AVERAGE",
    "DEF:ds1=" + climat_rrd + ":hrOut:AVERAGE",
    "DEF:ds2=" + climat2_rrd + ":hrOWM:AVERAGE",
    "DEF:ds3=" + fan_rrd + ":fan:AVERAGE",
    "VDEF:ds0last=ds0,LAST",
    "VDEF:ds1last=ds1,LAST",
    "CDEF:m3=ds3,100,*",
    "LINE3:ds0#FF8C00:hrIn\:\\g",
    "GPRINT:ds0last:%3.1lf %%",
    "LINE3:ds1#008B8B:hrOut\:\\g",
    "GPRINT:ds1last:%3.1lf %%\\u",
    "LINE3:ds2#7B68EE88:hrOWM:dashes=2,10",
    "AREA:m3#90EE9033:fan\\r")
print "done! file= %s" % (hrgraph)


print "creating clouds graph ..."
clouds = rrdtool.graph(cloudsgraph,
    common,
    "--vertical-label", "Cloudiness (%)",
    "--lower-limit", "0",
    "--upper-limit", "100",
    "--rigid",
    "--y-grid", "10:1",
    "--right-axis", "0.1:0",
    "--right-axis-label", "Precipitations (mm/h)",
    "DEF:ds0=" + clouds_rrd + ":cloudsOMF:AVERAGE",
    "DEF:ds1=" + clouds_rrd + ":cloudsOWM:AVERAGE",
    "DEF:ds2=" + clouds_rrd + ":rainOMF:AVERAGE",
    "DEF:ds3=" + clouds_rrd + ":rainOWM:AVERAGE",
    "CDEF:m2=ds2,10,*",
    "CDEF:m3=ds3,10,*",
    "LINE3:ds0#008B8B88:cloudsOMF",
    "LINE3:ds1#7B68EE88:cloudsOWM\\u",
    "LINE3:m2#008B8B:rainOMF:dashes=2,10",
    "LINE3:m3#7B68EE:rainOWM\\r:dashes=2,10:dash-offset=10")
print "done! file= %s" % (cloudsgraph)

'''

