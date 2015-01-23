#!/usr/bin/python
# -*- coding:utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4


# Imports
import webiopi, logging, os, time, datetime, ephem, re, json, sys, rrdtool
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from webiopi.devices.sensor.onewiretemp import DS18B20


# Enable debug output
webiopi.setDebug()
#webiopi.setInfo()

# Retrieve GPIO lib
GPIO = webiopi.GPIO


# Webiopi dir
webio_dir = "/home/pi/homeiopi/"


# Config
cfgFile = webio_dir + "cfg/cfg.json"
cfgAll = json.load(open(cfgFile))
jobsFile = webio_dir + "cfg/aps_jobs.sqlite"
statusDir = webio_dir + "html/app/status/"


# Sensors & commands GPIOs
try:
    tmp_pool = DS18B20(slave=cfgAll["sensors"]["tmp_pool"])
except:
    webiopi.exception("! error getting sensors GPIOs ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))

 
# Location (used for computing sunrise/sunset)
cfgLoc = cfgAll["location"][0]
lat, lon = cfgLoc["lat"], cfgLoc["lon"]


# APScheduler
jobstores = {
    'file': SQLAlchemyJobStore(url='sqlite:///' + jobsFile)
}

sched = BackgroundScheduler(jobstores=jobstores)
 

# Called by WebIOPi at script loading
def setup():
    webiopi.info("Script with macros - Setup")
    try:
        # Setup GPIOs
        for app in cfgAll["app"]:
            map = cfgAll["app"][app]["map"]
            #webiopi.debug("map=%s" % map)
            for item in map:
                if "cmd" in item:
                #webiopi.debug("cmd=%s" % cmd)
                    for i in item["cmd"]:
                        gpio = i["gpio"]
                        GPIO.setFunction(gpio, GPIO.OUT)
                        GPIO.digitalWrite(gpio, GPIO.LOW)
        # Setup APScheduler
        global sched
        sched.start()
    except:
        webiopi.exception("! setup failed ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
        pass


# Looped by WebIOPi
#def loop():


# Called by WebIOPi at server shutdown
def destroy():
    webiopi.info("Script with macros - Destroy")
    try:
        # Reset GPIOs
        for app in cfgAll["app"]:
            map = cfgAll["app"][app]["map"]
            #webiopi.debug("map=%s" % map)
            for item in map:
                if "cmd" in item:
                #webiopi.debug("cmd=%s" % cmd)
                    for i in item["cmd"]:
                        gpio = i["gpio"]
                        GPIO.setFunction(gpio, GPIO.OUT)
                        GPIO.digitalWrite(gpio, GPIO.LOW)
        # Shutdown APScheduler
        global sched
        sched.shutdown()
    except:
        webiopi.exception("! destroy failed ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
        pass



def getGPIO(app, num, idx):
    try:
        num = int(num)
        idx = int(idx)
        #webiopi.debug("num = %s, idx = %s" % (num, idx))
        cfg = cfgAll["app"][app]
        cmd = cfg["map"][num]["cmd"]
        act = cmd[idx]["gpio"]
        deact = None
        # Look for paired command
        nidx = not idx
        if nidx < len(cmd):
            deact = cmd[nidx]["gpio"]
        #webiopi.debug("act = %s, deact = %s" % (act, deact))
        return act, deact
    except:
        webiopi.exception("! error getting GPIO config ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))


@webiopi.macro
def actRemote(app, num, idx):
    try:
        act, deact = getGPIO(app, num, idx)
        cfg = cfgAll["app"][app]
        duration = cfg["duration"]
        actState = GPIO.digitalRead(act)
        deactState = None
        if deact:
            deact = int(deact)
            deactState = GPIO.digitalRead(deact)
        if actState:
            # Cancel deactivate timer
            job = checkProg(act)
            if job:
                #webiopi.debug("job id: %s" % job.id)
                sched.remove_job(job.id)
            # Deactivate
            GPIO.digitalWrite(act, 0)
        else:
            if deactState:
                # Cancel deactivate timer
                job = checkProg(deact)
                if job:
                    sched.remove_job(job.id)
                # Deactivate
                GPIO.digitalWrite(deact, 0)
            # Activate 
            GPIO.digitalWrite(act, 1)
            # Deactivate program if duration > 0
            if duration > 0:
                # Schedule deactivate job
                progId = str(act) + "-" + "deact"
                exec_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + duration))
                sched.add_job(deactRemote, "date", [str(act)], id=progId, next_run_time=exec_date, name=progId )
    except:
        webiopi.exception("! error activating remote ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))
        

@webiopi.macro
def actRemoteAll(app, idx):
    try:
        cfg = cfgAll["app"][app]

        # List running jobs
        jobs = []
        map = cfg["map"]
        #webiopi.debug("map = %s" % map)
        for i in range(len(map)):
            act, deact = getGPIO(app, i, idx)
            # Check if a job is running
            job = checkProg(act)
            if job:
                #webiopi.debug("job = %s" % job)
                jobs.append([job, i])
            #webiopi.debug("jobs = %s" % jobs)

        # Activate all if no jobs are running
        if not jobs:
            for i in range(len(map)):
                actRemote(app, i, idx)

        # Deactivate running jobs if any
        else:
            for jobinfo in jobs:
                job, i = jobinfo[0], jobinfo[1]
                #webiopi.debug("job: %s, i = %s " % (job, i))
                actRemote(app, i, idx)
    except:
        webiopi.exception("! error activating all remotes ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))


 

def deactRemote(act):
    try:
        act = int(act)
        GPIO.digitalWrite(act, 0)
    except:
        webiopi.exception("! error deactivating remote ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))




def actProg(prog, rank, act, deact, duration):
    try:
        progRun = str(act) + '-' + rank + '-' + prog
        webiopi.info("running prog: %s" % progRun)
        duration = int(duration)
        # check GPIOs state
        act = int(act)
        actState = GPIO.digitalRead(act)
        deactState = None
        if deact:
            deact = int(deact)
            deactState = GPIO.digitalRead(deact)
        # Activate if none is already active
        if not actState and not deactState:
            GPIO.digitalWrite(act, 1)
            # Schedule deactivate job
            progId = str(act) + '-' + 'deact'
            exec_date = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + duration))
            sched.add_job(deactRemote, "date", [str(act)], id=progId, next_run_time=exec_date, name=progId)
        # do not activate if another job is running
        else:
            webiopi.info("end prog %s ! another job is running ! do nothing" % progRun)
    except:
        webiopi.exception("! error activating program ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))



def progSun(prog, rank, act, deact, duration, is_rise, h, m):
    try:
        h = int(h)
        m = int(m)
        is_rise = int(is_rise)
        act = int(act)
        deact = int(deact)
        # UTC offset
        utc_time = 1
        webiopi.debug("UTC offset = %s - A calculer selon date !!!!" % utc_time)
        now = datetime.datetime.now()
        webiopi.debug("now = %s" % now)
        #test_utctime = datetime.tzinfo.utcoffset(now)
        #webiopi.debug("UTC offset = %s" % test_utctime)
        # User offset
        delay = datetime.timedelta(hours=int(h), minutes=int(m))               
        webiopi.debug("user delay= %s" % delay)
        # compute sunrise/sunset time with ephem module
        o = ephem.Observer()
        o.lat, o.lon, o.date = lat, lon, datetime.date.today()
        sun = ephem.Sun(o)
        next_event = o.next_rising if is_rise else o.next_setting
        sunTime = ephem.Date(next_event(sun, start=o.date) + utc_time*ephem.hour).datetime()
        #test_sunTime = ephem.Date(next_event(sun, start=o.date)).datetime() + test_utctime
        webiopi.debug("sunTime= %s" % sunTime)
        #webiopi.debug("test_sunTime= %s" % test_sunTime)
        nextTime = sunTime + delay
        webiopi.debug("nextTime = %s" % nextTime)
        progId = str(act) + '-' + rank + '-' + 'sun'
        sched.add_job(actProg, "date", [prog, rank, str(act), str(deact), str(duration)], id=progId, name=progId, next_run_time=nextTime, jobstore='file')
    except:
        webiopi.exception("! error activating sun prog ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))



def actFan_OLD(prog, rank, act, deact, duration, hrMin, hrMax):
    try:
        act = int(act)
        hrMin = int(hrMin)
        hrMax = int(hrMax)
        duration = int(duration)
        rrd = statusDir + "hr.rrd"
        (hrAvg, hrLast) = avgRRD(rrd, "In", 1800)
        hrAvg = float(hrAvg)
        hrLast = float(hrLast)
        actState = int(GPIO.digitalRead(act))
        if hrAvg is None or hrLast is None:
            webiopi.debug("hr measurement error - do nothing !")
        else:
            if not actState:
                # Fan is off - check last value
                if hrMin < hrLast < hrMax:
                    webiopi.debug("fan off - hr OK - do nothing !")
                else:
                    webiopi.debug("fan off - hr NOK - activate fan !")
                    GPIO.digitalWrite(act, 1)
            else:
                # Fan is on - check last and average value
                if hrMin < hrLast < hrMax and hrMin < hrAvg < hrMax:
                    webiopi.debug("fan on - hr OK - deactivate fan")
                    GPIO.digitalWrite(act, 0)
                else:
                    webiopi.debug("fan on - hr NOK - do nothing !")
    except:
        webiopi.info("! echec commande fan ! %s - %s" % (sys.exc_info()[0], sys.exc_info()[1]))


def actFan(prog, rank, act, deact, duration, hrMin, hrMax):
    try:
        act = int(act)
        hrMin = int(hrMin)
        hrMax = int(hrMax)
        duration = int(duration)
        rrd = statusDir + "hr.rrd"
        delay = 1800
        last = lastRRD(rrd, "In", delay)
        #webiopi.debug("last = %s" % last)
        actState = int(GPIO.digitalRead(act))
        if not last:
            # hr unknown
            webiopi.warning("hr unknown - activate fan")
            GPIO.digitalWrite(act, 1)
        else:
            # check if any hr NOK
            hrOK = True
            for val in last:
                if val < hrMin or val > hrMax:
                    hrOK = False
            if not actState:
                # Fan is off
                if hrOK is True:
                    webiopi.debug("fan off - hr OK - do nothing !")
                else:
                    webiopi.debug("fan off - hr NOK - activate fan !")
                    GPIO.digitalWrite(act, 1)
            else:
                # Fan is on
                if hrOK is True:
                    webiopi.debug("fan on - hr OK - deactivate fan")
                    GPIO.digitalWrite(act, 0)
                else:
                    webiopi.debug("fan on - hr NOK - do nothing !")
    except:
        webiopi.info("! echec commande fan ! %s - %s" % (sys.exc_info()[0], sys.exc_info()[1]))


def progPool(prog, rank, act, deact, duration):
    try:
        act = int(act)
        # Activate pump for delay before measurement
        delay = 1200
        GPIO.digitalWrite(act, 1)
        # not reboot-proof method !!!!!
        time.sleep(delay)
        GPIO.digitalWrite(act, 0)
        rrd = statusDir + "water.rrd"
        temp = lastRRD(rrd, "temp", 0)
        #temp = tmp_pool.getCelsius()
        webiopi.debug("Pool water temp: %s°C" % temp)
        # Calculate filtration total time
        temp = round(float(temp), 1)
        if temp < 10:
            tFilter = 3600
        elif temp > 24:
            # max filter time
            tFilter = 12*3600
        else:
            tFilter = round(temp/2*3600)
        # Filtration on 2 steps
        duration = round(tFilter/2)
        webiopi.debug("Pool filtration step duration: %ss" % duration)
        today = datetime.date.today()
        run1 = datetime.datetime.combine(today, datetime.time(8, 0))
        run2 = datetime.datetime.combine(today, datetime.time(14, 0))
        sched.add_job(actProg, "date", [prog, rank, str(act), deact, str(duration)], id=str(act) + '-' + rank + '-' + 'pool1', name='run1', next_run_time=run1, jobstore='file')
        sched.add_job(actProg, "date", [prog, rank, str(act), deact, str(duration)], id=str(act) + '-' + rank + '-' + 'pool2', name='run2', next_run_time=run2, jobstore='file')
    except:
        webiopi.info("! pool command error ! %s - %s" % (sys.exc_info()[0], sys.exc_info()[1]))



@webiopi.macro
def getTime():
    try:
        now = datetime.datetime.now()
        day = now.strftime("%a")
        date = now.strftime("%d"+"/"+"%m")
        time = now.strftime("%H : %M")
        # webiopi.debug("now = %s" % now)
        return json.JSONEncoder().encode([day, date, time])
    except:
         webiopi.exception("! error getting system time ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))



@webiopi.macro
def setTime(year, month, day, hour, min, sec):
    try:
        webiopi.debug("time: %s %s %s %s %s %s" % (year, month, day, hour, min, sec))
        date_str = month + day + hour + min + year
        webiopi.debug("date_str = %s" % date_str)
        os.system('date %s' % date_str) 
        return getTime()
    except:
         webiopi.exception("! error setting system time ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))




@webiopi.macro
def getConf(app):
    try:
        #webiopi.debug("%s" % cfgAll)
        return json.JSONEncoder().encode(cfgAll["app"][app])        
    except:
         webiopi.exception("! error getting prog ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))




@webiopi.macro
def getProg(app, prog, rank, num, idx):
    try:
        act, deact = getGPIO(app, num, idx)
        jobs = checkProg(act, rank)
        webiopi.debug("jobs: %s " % jobs)
        # Send job data if any
        if jobs:
            jobType, d, p1, p2 = getData(jobs[0])
            jobData = {"type": jobType, "gpio": act, "day_of_week": d, "p1": p1, "p2": p2}
        else:
            jobData = {"type": None, "gpio": act}
        return json.JSONEncoder().encode(jobData)
    except:
        webiopi.exception("! error getting prog ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))




@webiopi.macro
def setProg(app, prog, rank, num, idx, d, p1=None, p2=None):
    try:
        act, deact = getGPIO(app, num, idx)
        cfg = cfgAll["app"][app]
        duration = cfg["duration"]
        itemcfg = cfg["map"][int(num)]
        name = itemcfg["name"]
        cmd = itemcfg["cmd"]
        idxid = cmd[int(idx)]["id"]
        if True:
            # Check if data is valid
            d, p1, p2 = cleanData(prog, d, p1, p2)
            # Send error if data is invalid
            if d is None or p1 is None or p2 is None:
                jobData = {"type": "error", "gpio": act, "day_of_week": d, "p1": p1, "p2": p2}
                return json.JSONEncoder().encode(jobData)
            # Check if a job is running
            jobs = checkProg(act, rank)
            # remove active job on gpio if any
            if jobs:
                for job in jobs:
                    sched.remove_job(job.id)
            # create new job if none was running
            else:
                progId = str(act) + '-' + rank
                progName = app + '-' + name + '-' + idxid + '-' + rank
                if prog == "now":
                    duration = (int(p1)*60 + int(p2))*60
                    actProg(prog, rank, act, deact, duration)
                elif prog == "cron":
                    sched.add_job(actProg, "cron", day_of_week=d, hour=p1, minute=p2, args=[prog, rank, act, deact, duration], id=progId, name=progName, jobstore="file")
                elif prog == "sun":
                    # compute sunrise/sunset before yearly min sunrise/sunset
                    if idx:
                        is_rise = "0"
                        hourStart = 17
                    else:
                        is_rise = "1"
                        hourStart = 5
                    sched.add_job(progSun, "cron", day_of_week=d, hour=hourStart, minute=0, args=[prog, rank, act, deact, duration, is_rise, p1, p2], id=progId, name=progName, jobstore="file")
                elif prog == "freq":
                    h = "*/" + str(p1)
                    duration = int(p2)*60
                    sched.add_job(actProg, "cron", day_of_week=d, hour=h, args=[prog, rank, act, deact, duration], id=progId, name=progName, jobstore="file")
                elif prog == "fan":
                    #minute = "*/" + str(int(duration/60))
                    sched.add_job(actFan, "cron", day_of_week=d, minute="*/5", args=[prog, rank, act, deact, duration, p1, p2], id=progId, name=progName, jobstore="file")
                elif prog == "pool":
                    sched.add_job(progPool, "cron", day_of_week=d, hour=7, args=[prog, rank, act, deact, duration], id=progId, name=progName, misfire_grace_time=21600, jobstore="file")
                    #actPool(prog, rank, act, deact, duration)
            return getProg(app, prog, rank, num, idx)
    except:
        webiopi.exception("! error setting prog ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))




@webiopi.macro
def setProgAll(app, prog, rank, idx, d, p1=None, p2=None):
    # check if no job running in javascript
    try:
        idx = int(idx)
        cfg = cfgAll["app"][app]
        ret = []
        # Check if data is valid
        day, p1v, p2v = cleanData(prog, d, p1, p2)
        webiopi.debug("day, p1v, p2v = %s %s %s" % (day, p1v, p2v))
        # Return error if data is invalid
        if day is None or p1v is None or p2v is None:
            jobData = {"type": "error", "gpio": idx, "day_of_week": day, "p1": p1v, "p2": p2v}
            ret.append(json.JSONEncoder().encode(jobData))
            #webiopi.debug("ret = %s" % ret)
        else:
            # List running jobs
            jobsRun = []
            map = cfg["map"]
            #webiopi.debug("map = %s" % map)
            for i in range(len(map)):
                cmd = cfg["map"][i]["cmd"]
                act = cmd[idx]["gpio"]
                # Check if a job is running
                jobs = checkProg(act, rank)
                if jobs:
                    for job in jobs:
                        webiopi.debug("job = %s" % job)
                        jobsRun.append([job, i])
            webiopi.debug("jobsRun = %s" % jobsRun)

            # Activate all if no jobs are running
            if not jobsRun:
                for i in range(len(map)):
                    ret.append(setProg(app, prog, rank, i, idx, d, p1, p2))
            # Deactivate running jobs if any
            else:
                for jobinfo in jobsRun:
                    job, i = jobinfo[0], jobinfo[1]
                    webiopi.debug("job = %s, i = %s" % (job, i))
                    name = job.args[0]
                    webiopi.debug("app, name, rank, i, idx, d, p1, p2 = %s %s %s %s %s %s %s %s" % (app, name, rank, i, idx, d, p1, p2))
                    ret.append(setProg(app, name, rank, i, idx, d, p1, p2))
        return json.JSONEncoder().encode(ret)
    except:
        webiopi.exception("! error setting all progs ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))



def checkProg(gpio, rank=None):
    try:
        if rank is None:
            id = str(gpio) + '-' + "deact"
            job = sched.get_job(id)
            #webiopi.debug("job: %s" % job)
            return job
        else:
            jobs = []
            # Get main job
            id = str(gpio) + '-' + rank
            job = sched.get_job(id)
            if job:
                jobs.append(job)
            # Get sons job
            for job in sched.get_jobs():
                result = re.match(id + "\-.+$", job.id)
                if result:
                    # LOGIC if job.id match str(gpio) + '-' + rank + '-' *
                    webiopi.debug("job: %s" % job)
                    #if job.args[2] == gpio and job.args[1] == rank:
                    jobs.append(job)
            #webiopi.debug("jobs: %s" % jobs)
            if jobs:
                return jobs
    except:
        webiopi.exception("! error checking prog ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))




def checkProgOLD(prog, gpio, rank=None):
    try:
        if prog == "deact":
            id = str(gpio) + '-' + "deact"
            job = sched.get_job(id)
            #webiopi.debug("job: %s" % job)
            return job
        elif prog == "any":
            jobs = []
            for job in sched.get_jobs():
                if job.args[2] == gpio and job.args[1] == rank:
                    jobs.append(job)
            #webiopi.debug("jobs: %s" % jobs)
            return jobs
        else:
            id = str(gpio) + '-' + rank
            job = sched.get_job(id)
            #webiopi.debug("job: %s" % job)
            return job
    except:
        webiopi.exception("! error checking prog ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))



def cleanData(prog, d, p1, p2):
    try:
        d = str(d)
        if p1:
            p1 = int(p1)
        if p2:
            p2 = int(p2)
        # Check days data
        result = re.match("[0-6]+$", d)
        if not result:
            d = None
        else:
            # Clean days data
            data = ""
            for day in d:
                if data == "":
                    data += day
                else:
                    data += ',' + day
            d = data
        # Check parameters data
        if prog == "now" or prog == "cron" or prog == "sun":
            #result = re.match("[0-2]?[0-9]$", p1)
            #if not result:
            if not 0 <= p1 <= 23:
                p1 = None
            #result = re.match("[0-5]?[0-9]$", p2)
            #if not result:
            if not 0 <= p2 <= 59:
                p2 = None
        elif prog == "freq":
            #result = re.match("\d+$", p2)
            if not 1 <= p1 <= 24:
                p1 = None
            if not (1 <= p2 <= 1440 and p2/60 < p1):
                p2 = None
        elif prog == "fan":
            if not 0 <= p1 <= 100:
                p1 = None
            if not (0 <= p2 <= 100 and p1 < p2):
                p2 = None
        elif prog == "pool":
            p1 = 0
            p2 = 0
        return d, p1, p2
    except:
        webiopi.exception("! error cleaning data ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))

    

# Get data from running job
def getData(job):
    try:
        jobType = job.args[0]
        jobTrig = job.trigger.fields
        d = str(jobTrig[4])
        if jobType == "now":
            p1 = 0
            p2 = 0
        elif jobType == "cron":
            p1 = str(jobTrig[5])
            p2 = str(jobTrig[6])
        elif jobType == "sun":
            p1 = job.args[6]
            p2 = job.args[7]
            #p1 = str(jobTrig[6])
            #p2 = str(jobTrig[7])
        elif jobType == "freq":
            freqCron = str(jobTrig[5])
            match = re.search("\*\/(\d+)", freqCron)
            p1 = match.group(1)
            p2 = int(job.args[4])/60
        elif jobType == "fan":
            p1 = job.args[5]
            p2 = job.args[6]
        elif jobType == "pool":
            p1 = 0
            p2 = 0
        return jobType, d, p1, p2
    except:
        webiopi.exception("! error getting job data ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))




def checkData(prog, d, p1, p2):
    try:
        d, p1, p2 = str(d), str(p1), str(p2)
        #webiopi.debug("d = %s" % d)
        if prog == "cron" or "sun" or "date":
            #result = re.match("[0-6](-[0-6])?$", d)
            result = re.match("[0-6]+$", d)
            if not result:
                d = None
        result = re.match("[0-2]?[0-9]$", p1)
        if not result:
            p1 = None
        # result = re.match("[0-5]?[0-9]$", p2)
        result = re.match("\d+$", p2)
        if not result:
            p2 = None
        return d, p1, p2
    except:
        webiopi.exception("! error checking data ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))



def next_weekday(d, h, m):
    try:
        now = datetime.datetime.now()
        days_ahead = d - now.weekday()
        target = datetime.time(int(h),int(m),0,1)
        #webiopi.debug("days_ahead= %s " % days_ahead)
        if days_ahead == 0 and target > now.time(): 
            days_ahead = 0
        elif days_ahead <= 0:
            days_ahead += 7
        return now + datetime.timedelta(days_ahead)
    except:
        webiopi.exception("! error guessing next week day ! %s %s" % (sys.exc_info()[0], sys.exc_info()[1]))


# Get last values from RRD
def lastRRD(rrd, dsName, delay):
    try:
        delay = int(delay)
        if delay == 0:
            info = rrdtool.info(rrd)
            last = info['ds[' + dsName + '].last_ds']
        else:
            fetch = rrdtool.fetch(rrd, 'AVERAGE', '--start', 'end-' + str(delay) + 'sec')[2]
            last = []
            for pair in fetch:
                if pair[0]:
                    last.append(pair[0])
        return last
    except:
        webiopi.exception("! error getting last values from RRD ! %s - %s" % (sys.exc_info()[0], sys.exc_info()[1]))


# Calculate average value from RRD
def avgRRD(rrd, dsName, delay):
    try:
        delay = int(delay)
        info = rrdtool.info(rrd)
        last = info['ds[' + dsName + '].last_ds']
        lasts = rrdtool.fetch(rrd, 'AVERAGE', '--start', 'end-' + str(delay) + 'sec')[2]
        #webiopi.debug(lasts)
        total = 0
        vals = 0
        for pair in lasts:
            if pair[0]:
                hrIn = float(pair[0])
                #webiopi.debug("hrIn = %s" % hrIn)
                total += hrIn
                vals += 1
        #webiopi.debug("total=%s" % total)
        if vals > 1:
            avg = round(total/vals, 1)
        else:
            webiopi.warn("not enough values! delay too short (%s)" % delay)
            avg = last
        webiopi.debug("avg, last = %s, %s" % (avg, last))
        return avg, last
    except:
        webiopi.exception("! error calculating average value from RRD ! %s - %s" % (sys.exc_info()[0], sys.exc_info()[1]))

