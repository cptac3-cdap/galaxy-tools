from galaxy.jobs.mapper import JobMappingException, JobNotReadyException
from galaxy.jobs import JobDestination
import os, csv, sys, random
import datetime
import time
import copy

from lockfile import FileLock
from tsdict import tsdict
import util

def writestatus(statusfile,ipaddr,waiting):
    rows = []
    for ip in ipaddr:
	r = [ip]
	id = ipaddr[ip].get('id')
	index = ipaddr[ip].get('index',-1)
	r.extend(['index',index])
	cpus = ipaddr[ip].get('cpus',-1)
	r.extend(["cpus",cpus])
	running = ipaddr[ip].get('running',0)
	r.extend(["running",running])
	starttime = ipaddr[ip].get('starttime')
	if starttime:
	    r.extend(["time_in_state",(datetime.datetime.now()-starttime).total_seconds()])
	lasttime = ipaddr[ip].get('lasttime')
	if lasttime:
	    r.extend(["lasttime",datetime.datetime.ctime(lasttime)])
	if id:
	    r.extend(['id',index])
	rows.append(r)
    rows.append(["waiting",len(waiting)])
    wh = open(statusfile,'w')
    for r in rows:
	print >>wh, "\t".join(map(str,r))
    wh.close()

lastcall = tsdict()

def pulsar_destinations(app, tool_id, job):
     global lastcall
     if (time.time() - lastcall.get(job.id,0)) < 15:
         raise JobNotReadyException()
     lastcall.set(job.id,time.time())

     tdp = app.config.tool_data_path
     ipaddr = util.read_pulsar_nodes(tdp)
     
     jobfile,joblock = util.lock_jobs(tdp)

     try:
         jobs = util.read_jobs(jobfile,app)
         waiting = util.waiting(jobs)
         toremove = util.toremove(jobs)
         running = util.running(jobs)
         for ip in ipaddr:
             ipaddr[ip]['running'] = running[ip]

         now = datetime.datetime.now()
         for k in list(ipaddr):
             if 'lasttime' in ipaddr[k] and ((now-ipaddr[k]['lasttime']) < datetime.timedelta(seconds=0)):
                 del ipaddr[k]
             elif ipaddr[k].get('running',0) >= (ipaddr[k].get('cpus',0)+1):
                 del ipaddr[k]
     
         if len(ipaddr) == 0 or (len(waiting) > 0 and min(waiting) < job.id):

             if job.id not in waiting:
               util.update_jobs(jobfile,waiting=job.id,toremove=toremove)
             else:
               util.update_jobs(jobfile,toremove=toremove)
             raise JobNotReadyException()       
	
         newip = sorted(ipaddr.items(),key=lambda t: (max(0,t[1].get('running',0)+1-t[1].get('cpus',0)),t[1]['index']))[0][0]

         util.update_jobs(jobfile,dispatch=(job.id,newip),toremove=toremove)

     finally:
          joblock.release()

     params = dict(url="http://%s:8913/"%(newip,),
                   private_token="CPTAC_WinPulsar")

     return JobDestination(runner="pulsar", params=params)
     
