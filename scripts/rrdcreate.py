#!/usr/bin/python

import os, sys, rrdtool


filename = sys.argv[1]
rrdinfo = sys.argv[2]


dataTemp = ["--step", "300",
        "--start", '0',
        "DS:In:GAUGE:360:-20:50",
        "DS:Out:GAUGE:360:-20:50"]

dataHR = ["--step", "300",
        "--start", '0',
        "DS:In:GAUGE:360:0:100",
        "DS:Out:GAUGE:360:0:100"]

dataClouds = ["--step", "300",
        "--start", '0',
        "DS:clouds:GAUGE:360:0:100",
        "DS:rain:GAUGE:360:0:U"]

dataWater = ["--step", "300",
        "--start", '0',
        "DS:temp:GAUGE:360:-20:50"]

dataOnOff = ["--step", "300",
        "--start", '0',
        "DS:on:GAUGE:360:0:1"]


RRAavg = ["RRA:AVERAGE:0.8:1:864",
        "RRA:AVERAGE:0.8:6:336",
        "RRA:AVERAGE:0.8:12:720",
        "RRA:AVERAGE:0.8:48:720",
        "RRA:AVERAGE:0.8:288:730"]
        # 3j de donnees moy 5min 80% unknown
        # 1s de donnees moy 30min 80% unknown
        # 30j de donnees moy 1h 80% unknown
        # 4m de donnees moy 4h 80% unknown
        # 2a de donnees moy 24h 80% unknown


if rrdinfo == "temp":
    data = dataTemp
elif rrdinfo == "hr":
    data = dataHR
elif rrdinfo == "clouds":
    data = dataClouds
elif rrdinfo == "water":
    data = dataWater
elif rrdinfo == "onoff":
    data = dataOnOff
else:
    print ("rrdinfo invalide: %s" % rrdinfo)


rrddata = data + RRAavg


valid = raw_input("Le fichier %s va etre cree !\nParametres: \n%s \nSur ??? [o/N]" % (filename, rrddata))

if valid == "o":
    try:
        ret = rrdtool.create(filename, rrddata)
        print ("fichier cree !")
    except:
        print ("ERROR: %s" % (sys.exc_info()[1]))
else:
    print ("Operation annulee !")


