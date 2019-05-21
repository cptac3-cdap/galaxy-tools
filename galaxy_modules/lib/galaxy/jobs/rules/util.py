
from lockfile import FileLock
import csv, datetime, os.path
from collections import defaultdict

def read_pulsar_nodes(tooldatapath,readyonly=True):
    
    nodesfile = os.path.join(tooldatapath,'pulsar_nodes.loc.nodes')
    lock = FileLock(nodesfile)
    lock.acquire()
    try:
        nodes = {}
        theindex = 1
        thepindex = 1
        thetindex = 1
        h = open(nodesfile)
        for r in csv.reader(h,dialect='excel-tab'):
            # print >>sys.stderr, r
            if r[1] == 'stop':
                timestamp = datetime.datetime.strptime(r[2],"%a %b %d %H:%M:%S %Y")
                nodes[r[0]] = dict(awsname=r[3],timestamp=timestamp,ip=r[0],state='terminated')
                thetindex += 1
            elif r[1] == 'start':
                timestamp = datetime.datetime.strptime(r[2],"%a %b %d %H:%M:%S %Y")
                nodes[r[0]] = dict(index=theindex,awsname=r[3],cpus=int(r[4]),timestamp=timestamp,ip=r[0],state='ready')
                theindex += 1
            elif r[1] == 'pending':
                timestamp = datetime.datetime.strptime(r[2],"%a %b %d %H:%M:%S %Y")
                ip = "pending-%d"%(thepindex,)
                nodes[ip] = dict(awsname=r[3],timestamp=timestamp,state='pending')
                thepindex += 1
        h.close()
    finally:
        lock.release()

    aws2ip = dict()
    for n in nodes.values():
        if 'ip' in n and 'awsname' in n:
            aws2ip[n['awsname']] = n['ip']

    for n in list(nodes):
        if nodes[n]['state'] == 'pending':
            if 'awsname' in nodes[n]:
                aws = nodes[n]['awsname']
                if aws in aws2ip and aws2ip[aws] in nodes:
                    del nodes[n]

    if readyonly:
        for n in list(nodes):
            if nodes[n]['state'] != 'ready':
                del nodes[n]

    return nodes

def pending_pulsar_node(tooldatapath,**node):
    nodesfile = os.path.join(tooldatapath,'pulsar_nodes.loc.nodes')
    now = datetime.datetime.now()
    timestamp = datetime.datetime.ctime(now)
    node['timestamp'] = timestamp
    node['action'] = 'pending'
    node['ip'] = "-"
    node['cpus'] = str(node['cpus'])
    lock = FileLock(nodesfile)
    lock.acquire()
    try:
        wh = open(nodesfile,'a')
        print >>wh, "\t".join(map(node.get,["ip","action","timestamp","awsname","cpus"]))
        wh.close()
    finally:
        lock.release()

def start_pulsar_node(tooldatapath,**node):
    nodesfile = os.path.join(tooldatapath,'pulsar_nodes.loc.nodes')
    now = datetime.datetime.now()
    timestamp = datetime.datetime.ctime(now)
    node['timestamp'] = timestamp
    node['action'] = 'start'
    node['cpus'] = str(node['cpus'])
    lock = FileLock(nodesfile)
    lock.acquire()
    try:
        wh = open(nodesfile,'a')
        print >>wh, "\t".join(map(node.get,["ip","action","timestamp","awsname","cpus"]))
        wh.close()
    finally:
        lock.release()

def stop_pulsar_node(tooldatapath,**node):
    nodesfile = os.path.join(tooldatapath,'pulsar_nodes.loc.nodes')
    now = datetime.datetime.now()
    timestamp = datetime.datetime.ctime(now)
    node['timestamp'] = timestamp
    node['action'] = 'stop'
    node['cpus'] = '-1'
    lock = FileLock(nodesfile)
    lock.acquire()
    try:
        wh = open(nodesfile,'a')
        print >>wh, "\t".join(map(node.get,["ip","action","timestamp","awsname","cpus"]))
        wh.close()
    finally:
        lock.release()

from galaxy.jobs.rule_helper import RuleHelper
from galaxy import model

RUNNING = model.Job.states.RUNNING
QUEUED = model.Job.states.QUEUED
WAITING = model.Job.states.WAITING
NEW = model.Job.states.NEW
OK = model.Job.states.OK
ERROR = model.Job.states.ERROR
DELETED = model.Job.states.DELETED
DELETED_NEW = model.Job.states.DELETED_NEW
PAUSED = model.Job.states.PAUSED

def jobstate(app,jobid):
    if app:
        helper = RuleHelper(app)
        return helper.query(model.Job).filter(model.Job.id == jobid).first().state
    return None

def lock_jobs(tooldatapath):
    jobfile = os.path.join(tooldatapath,'pulsar_nodes.loc.jobs')
    lock = FileLock(jobfile)
    lock.acquire()
    return jobfile,lock

def read_jobs(statefile,app=None):

    jobdata = dict()

    if os.path.exists(statefile):
      h = open(statefile)
      for i,sl in enumerate(csv.reader(h,dialect='excel-tab')):
        ip = sl[0]
        timestamp = datetime.datetime.strptime(sl[1],"%a %b %d %H:%M:%S %Y")
        action = sl[2]
        jobid = int(sl[3])
        if action == 'dispatch':
            jobdata[jobid] = dict(state='running',ip=ip,lasttime=timestamp)
        elif action == 'remove':
            if jobid in jobdata:
                del jobdata[jobid]
        elif action == 'waiting':
            jobdata[jobid] = dict(state='waiting')
      h.close()

    for jobid in jobdata:
        js = jobstate(app,jobid)
        if js in (OK,DELETED,DELETED_NEW,ERROR,PAUSED):
            jobdata[jobid]['state'] = 'toremove'

    return jobdata

def running(jobs):
    running = defaultdict(int)
    for jobid in jobs:
        if jobs[jobid]['state'] == 'running':
            ip = jobs[jobid]['ip']
            running[ip] += 1
    return running

def waiting(jobs):
    joblist = []
    for jobid in jobs:
        if jobs[jobid]['state'] == 'waiting':
            joblist.append(jobid)
    return joblist

def toremove(jobs):
    joblist = []
    for jobid in jobs:
        if jobs[jobid]['state'] == 'toremove':
            joblist.append(jobid)
    return joblist

def update_jobs(statefile,waiting=None,dispatch=None,toremove=[]):
    
    wh = open(statefile,'a')
    if waiting != None:
        print >>wh, "\t".join(["-",datetime.datetime.ctime(datetime.datetime.now()),'waiting',str(waiting)])

    for jobid in toremove:
        print >>wh, "\t".join(["-",datetime.datetime.ctime(datetime.datetime.now()),'remove',str(jobid)])

    if dispatch != None:
        print >>wh, "\t".join([dispatch[1],datetime.datetime.ctime(datetime.datetime.now()),'dispatch',str(dispatch[0])])
    wh.close()
            
        
        


