#!/usr/bin/python
# -*- coding:utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4


# Imports
import webiopi, logging
import time, subprocess, sys, re, json
#sys.path.append('/usr/local/lib/python3.2/dist-packages')
import rrdtool, requests
from threading import Timer
from webiopi.devices.sensor.onewiretemp import DS18B20

# Enable debug output
webiopi.setDebug()
#webiopi.setInfo()
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)


# Retrieve GPIO lib
GPIO = webiopi.GPIO


# Webiopi dir
webio_dir = "/home/pi/homeiopi/"

# Config
cfgFile = webio_dir + "cfg/cfg.json"
cfgAll = json.load(open(cfgFile))

# RRDs
statusDir = webio_dir + "html/app/status/"
temp_rrd = statusDir + "temp.rrd"
hr_rrd = statusDir + "hr.rrd"
clouds_rrd = statusDir + "clouds.rrd"
fan_rrd = statusDir + "fan.rrd"
pool_rrd = statusDir + "pool.rrd"
water_rrd = statusDir + "water.rrd"


# Sensors & commands GPIOs
try:
    gpioDHT22 = cfgAll["sensors"]["DHT22"]
    gpioFan = cfgAll["app"]["ventilation"]["map"][0]["cmd"][0]["gpio"]
    gpioPool = cfgAll["app"]["pool"]["map"][0]["cmd"][0]["gpio"]
    tmp0 = DS18B20(slave=cfgAll["sensors"]["tmp0"])
except:
    webiopi.exception("! error getting sensors GPIOs ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))



# Called by WebIOPi at script loading
def setup():
    webiopi.info("Script with macros - Setup")
    try:
        # Setup GPIOs
        GPIO.setFunction(gpioDHT22, GPIO.OUT)
        GPIO.digitalWrite(gpioDHT22, GPIO.LOW)
        GPIO.setFunction(gpioFan, GPIO.OUT)
        GPIO.digitalWrite(gpioFan, GPIO.LOW)
    except:
        webiopi.exception("! setup failed ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
        pass



# Looped by WebIOPi
def loop():
    try:
        # Mesures
        (tempOut, hrOut, clouds, rain) = measure_out()
        (tempIn, hrIn) = measure_in(gpioDHT22)
        fanState = check_state(gpioFan)
        poolState = check_state(gpioPool)
        try:
            water = tmp0.getCelsius()
            webiopi.debug("DS18B20_temp = %s" % water)
        except:
            webiopi.exception("! DS18B20 error ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
            water = "U"
        # RRDs update
        tempRRD = rrdtool.update(temp_rrd, 'N:%s:%s' %(tempIn, tempOut))
        hrRRD = rrdtool.update(hr_rrd, 'N:%s:%s' %(hrIn, hrOut))
        cloudsRRD = rrdtool.update(clouds_rrd, 'N:%s:%s' %(clouds, rain))
        fanRRD = rrdtool.update(fan_rrd, 'N:%s' % (fanState)) 
        poolRRD = rrdtool.update(pool_rrd, 'N:%s' % (poolState)) 
        waterRRD = rrdtool.update(water_rrd, 'N:%s' % (water)) 
    except:
        webiopi.info("! loop failed ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
        pass
    finally:
        # delay next measure in 5 min
        time.sleep(300)


# Called by WebIOPi at server shutdown
def destroy():
    webiopi.info("Script with macros - Destroy")
    try:
        # Reset GPIOs
        GPIO.setFunction(gpioDHT22, GPIO.OUT)
        GPIO.digitalWrite(gpioDHT22, GPIO.LOW)
        GPIO.setFunction(gpioFan, GPIO.OUT)
        GPIO.digitalWrite(gpioFan, GPIO.LOW)
    except:
        webiopi.info("! destroy failed ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
        pass



def measure_in(gpio):
    try:
        script = webio_dir + "scripts/adafruit_dht"
        tries = 5
        for i in range(tries):
            val = str(subprocess.check_output([script, "22", str(gpio)]))
            match = re.search('Temp.+\s([\d\.]+)\s.+Hum.+\s([\d\.]+)\s%', val)
            if match:
                temp, hr = match.group(1), match.group(2)
                webiopi.debug("DHT22 measure: temp=%s hr=%s" % (temp, hr))
                break
            else:
                # Erreur mesure gpioDHT22
                webiopi.debug("! DHT22 error ! - %s" % val)
                if i == tries-1:
                    temp = "U"
                    hr = "U"
                    webiopi.info("! DHT22 error ! - stop trying")
                else:
                    time.sleep(2)
    except:
        temp = "U"
        hr = "U"
        webiopi.exception("! DHT22 error ! %s" % sys.exc_info()[1])
    finally:
        return temp, hr




def measure_out():
    # get WeatherUnderground data
    try:
        api_key = cfgAll["WU_API_key"]
        loc = cfgAll["location"][0]
        country = loc["country"]
        city = loc["city"]
        url = "http://api.wunderground.com/api/" + api_key + "/conditions/q/" + country + "/" + city + ".json"
        dat = requests.get(url).json()["current_observation"]
        try:
            temp = str(round(dat["temp_c"], 1))
        except:
            temp = "U"
        #hr = str(round(dat["relative_humidity"], 1))
        match = re.search('([\d\.]+)%', dat["relative_humidity"])
        if match:
            hr = match.group(1)
        else:
            hr = "U"
        match = re.search('([\d\.]+)', dat["precip_1hr_metric"])
        if match:
            rain = match.group(1)
        else:
            rain = "U"
        #match = re.search('([\d\.]+)%', dat["clouds"]["all"])
        clouds = "0"
    except:
        temp = "U"
        hr = "U"
        clouds = "U"
        rain = "U"
        webiopi.info("! echec mesures WU ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
    finally:
        return temp, hr, clouds, rain
 


def check_state(gpio):
    try:
        gpio = int(gpio)
        gpioState = int(GPIO.digitalRead(gpio))
    except:
        gpioState = "U"
        webiopi.info("! error checking gpio %s state ! %s - %s"  % (gpio, sys.exc_info()[0], sys.exc_info()[1]))
    finally:
        return gpioState

