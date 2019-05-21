#!/usr/bin/env python

import sys
import os, os.path, csv
import tempfile
import shutil
import optparse
from urllib import urlencode
import urllib2
import datetime
import tarfile
import zipfile
import gzip
import zlib
import bz2
import time
import traceback
import subprocess
from operator import itemgetter
from lockfile import FileLock
import urllib
import util

from galaxy.util.json import from_json_string, to_json_string

# Otherwise we can't find aws?
os.environ['PATH'] += (os.pathsep + os.path.expanduser('~/bin'))
counter = 0

def add_data_table_entry( data_manager_dict, table_name, data_table_entry ):
    data_manager_dict['data_tables'] = data_manager_dict.get( 'data_tables', {} )
    data_manager_dict['data_tables'][table_name] = data_manager_dict['data_tables'].get( 'pulsar_node_events', [] )
    data_manager_dict['data_tables'][table_name].append( data_table_entry )
    return data_manager_dict

def cmdexec(args):
    print " ".join(map(lambda s: '"%s"'%s if ' ' in s else s,args))
    p = subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    data = p.stdout.read()
    # print data
    try:
	if data:
            return from_json_string(data)
    except Exception, e:
	print >>sys.stderr, "Response: %r"%(data,)
	raise
    return data

def getimage(desc):
    cmd = [ "aws", "ec2", "describe-images", "--filters" ]
    cmd.append("Name=description,Values="+desc)
    response = cmdexec(cmd)
    matches = []
    for image in response['Images']:
	matches.append((image['ImageId'],image['ImageLocation']))
    return sorted(matches,key=itemgetter(1))[-1][0]

def createstack(image,instance,az,keyname,clname,tooldir,amqpurl,dlurl):
    return createstack_(image,instance,az,None,None,keyname,clname,amqpurl,dlurl,
	                os.path.join(tooldir,'winpulsar.template'))

def createstackvpc(image,instance,vpc,subnet,keyname,clname,tooldir,amqpurl,dlurl):
    return createstack_(image,instance,None,vpc,subnet,keyname,clname,amqpurl,dlurl,
	                os.path.join(tooldir,'winpulsarvpc.template'))

def createstackstandalone(image,instance,keyname,clname,tooldir,amqpurl,dlurl):
    return createstack_(image,instance,None,None,None,keyname,clname,amqpurl,dlurl,
	                os.path.join(tooldir,'winpulsarsolo.template'))

def createstackstandalone1(image,instance,keyname,subnet,clname,tooldir,amqpurl,dlurl):
    return createstack_(image,instance,None,getvpcfromsubnet(subnet),subnet,keyname,clname,amqpurl,dlurl,
	                os.path.join(tooldir,'winpulsarsolo1.template'))

def createstack_(image,instance,az,vpc,subnet,keyname,clname,amqpurl,dlurl,template):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
    # print timestamp
    global counter
    if clname:
        stackname = "-".join(["WinPulsar",clname,str(counter),timestamp])
    else:
        stackname = "-".join(["WinPulsar",clname,str(counter),timestamp])
    counter += 1
    cmd = [ "aws", "cloudformation", "create-stack", "--stack-name",
            stackname, "--disable-rollback", "--template-body",
            "file://"+os.path.abspath(template).replace('/','//'), "--parameters" ]
    cmd.append("ParameterKey=InstanceType,ParameterValue="+instance)
    cmd.append("ParameterKey=ImageId,ParameterValue="+image)
    cmd.append("ParameterKey=AMQPURL,ParameterValue="+amqpurl)
    if subnet:
        cmd.append("ParameterKey=SubnetId,ParameterValue="+subnet)
    if vpc:
        cmd.append("ParameterKey=VpcId,ParameterValue="+vpc)
    if az:
        cmd.append("ParameterKey=AvailabilityZone,ParameterValue="+az)
    cmd.append("ParameterKey=KeyName,ParameterValue="+keyname)
    if clname:
        cmd.append("ParameterKey=ClusterName,ParameterValue="+clname)
    if dlurl:
	cmd.append("ParameterKey=DownloadURL,ParameterValue="+dlurl)
    response = cmdexec(cmd)
    return stackname

def geturl():
    try:
	for l in open(os.path.expanduser('~/.urls')):
	    sl = l.replace('=',' ').split()
	    if sl[1] == 'DOWNLOADURL':
		return sl[2].strip() + '/WinPulsar'
    except IOError:
	pass
    return None

def isaws():
    return os.path.exists(os.path.expanduser('~/.awsmd'))

def getclname():
    try:
	for l in open(os.path.expanduser('~/.awsmd')):
	    sl = l.split(None,1)
	    if sl[0] == 'cluster_name:':
		return sl[1].strip()
    except IOError:
	pass
    return None

def getaz():
    try:
	for l in open(os.path.expanduser('~/.awsmd')):
	    sl = l.split(None,1)
	    if sl[0] == 'availability-zone:':
		return sl[1].strip()
    except IOError:
	pass
    return None

def getit():
    try:
	for l in open(os.path.expanduser('~/.awsmd')):
	    sl = l.split(None,1)
	    if sl[0] == 'instance-type:':
		return sl[1].strip()
    except IOError:
	pass
    return None

def getinstid():
    try:
	for l in open(os.path.expanduser('~/.awsmd')):
	    sl = l.split(None,1)
	    if sl[0] == 'instance-id:':
		return sl[1].strip()
    except IOError:
	pass
    return None

def getlocalip():
    try:
	for l in open(os.path.expanduser('~/.awsmd')):
	    sl = l.split(None,1)
	    if sl[0] == 'local-ipv4:':
		return sl[1].strip()
    except IOError:
	pass
    return None

def getkeyname():
    cmd = ["aws","ec2","describe-instances","--instance-ids",getinstid()]
    response = cmdexec(cmd)
    return response["Reservations"][0]["Instances"][0]["KeyName"]

def getsubnet():
    cmd = ["aws","ec2","describe-instances","--instance-ids",getinstid()]
    response = cmdexec(cmd)
    return response["Reservations"][0]["Instances"][0].get("SubnetId")

def getvpcfromsubnet(subnetid):
    cmd = ["aws","ec2","describe-subnets","--subnetids-ids",subnetid]
    response = cmdexec(cmd)
    return response["Subnets"][0].get("VpcId")

def getvpc():
    cmd = ["aws","ec2","describe-instances","--instance-ids",getinstid()]
    response = cmdexec(cmd)
    return response["Reservations"][0]["Instances"][0].get("VpcId")

def getsgid():
    cmd = ["aws","ec2","describe-instances","--instance-ids",getinstid()]
    response = cmdexec(cmd)
    return response["Reservations"][0]["Instances"][0]["SecurityGroups"][0]["GroupId"]

def openamqpport(ipaddress):
    sgid = getsgid()
    cmd = ["aws","ec2","authorize-security-group-ingress","--group-id",sgid,
	   "--protocol","tcp","--port","5672","--cidr",ipaddress+"/32"]
    response = cmdexec(cmd)
    # assert response["return"] == "true" 

def closeamqpport(ipaddress):
    sgid = getsgid()
    cmd = ["aws","ec2","revoke-security-group-ingress","--group-id",sgid,
	   "--protocol","tcp","--port","5672","--cidr",ipaddress+"/32"]
    response = cmdexec(cmd)
    # assert response["return"] == "true" 

def describestack(stackid):
    cmd = ["aws", "cloudformation", "describe-stacks",
           "--stack-name", stackid ]
    response = cmdexec(cmd)
    stacks = response["Stacks"]
    if len(stacks) == 0:
	return None
    stack = stacks[0]
    pubip = None
    privip = None
    for output in stack.get("Outputs",[]):
	if output["OutputKey"] == "PublicIP":
	    pubip = output["OutputValue"]
	elif output["OutputKey"] == "PrivateIP":
	    privip = output["OutputValue"]
    if not pubip:
	return None
    if isaws():
	return privip
    return pubip

def deletestack(stackid):
    cmd = ["aws", "cloudformation", "delete-stack",
           "--stack-name", stackid ]
    response = cmdexec(cmd)
    return

cpus = {
           'large':2,
          'xlarge':4,
         '2xlarge':8,
         '4xlarge':16,
	'10xlarge':40,
	'12xlarge':48,
	'16xlarge':64,
	'24xlarge':96,
}

def getcpus(it):
    sit = it.split('.')
    if sit[1] in cpus:
	return cpus[sit[1]]
    return cpus[it]

def main():
    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()
    operation = args[0]
    filename = args[1]
    stackid = ""
    ipaddress = ""
    data_table_entries = []
    count = 1
    if filename:
        params = from_json_string( open( filename ).read() )['param_dict']
    
        tooldir = params['__tool_directory__']
        tooldata = params['GALAXY_DATA_INDEX_DIR']
	if 'cond' in params:
          type = params['cond']['type']
	  if type == 'manual':
            ipaddress = params['cond']['ipaddress']
	  elif type == 'aws' and operation == 'stop':
            stackid = params['cond']['stack']
	  elif type == 'aws' and operation == 'start':
	    count = int(params['cond'].get('count'))
	    awsinstancetype = params['cond'].get('instancetype')
	    awskeyname = params['cond'].get('keyname')
	    awssubnet = params['cond'].get('subnet')
	    awscluster = params['cond'].get('clustername',"")
	    awswinver = params['cond'].get('winver',"2016")
    else:
	type = args[2]
	if type == 'manual':
	  ipaddress = args[3]
	elif type == 'aws' and operation == 'stop':
	  stackid = args[3]
	tooldir = args[4]
	tooldata = args[5]

    now = datetime.datetime.now()

    try:
        amqpurl = open(os.path.join(tooldata,'amqp_url.loc')).read().splitlines()[-1].strip()
    except IndexError:
	amqpurl = "amqp:://guest:guest@%s:5672//"%(getlocalip(),)

    manualips = os.path.join(tooldata,'pulsar_nodes.ip.loc')
    awsstacks = os.path.join(tooldata,'pulsar_nodes.aws.loc')

    if operation == 'start':

      # Determine the IP address...
      ipaddresses = dict()
      if type == 'manual':

          stack = ""
	  ipaddresses[stack] = ipaddress

          lock = FileLock(manualips)
          lock.acquire()
          try:
              wh = open(manualips,'a+')
              print >>wh, ipaddress
              wh.close()
          finally:
              lock.release()

      elif type == 'aws':

          descriptions = dict()
	  descriptions['2016'] = "Microsoft Windows Server 2016 with Desktop Experience Locale English AMI provided by Amazon"
	  descriptions['2012R2'] = "Microsoft Windows Server 2012 R2 RTM 64-bit Locale English AMI provided by Amazon"
	  descriptions['2008R2'] = "Microsoft Windows Server 2008 R2 SP1 Datacenter 64-bit Locale English Base AMI provided by Amazon"
	  imageid = getimage(descriptions[awswinver])
	  vpc = None
	  availzone = None
	  if isaws():
	    availzone = getaz()
	    instancetype = getit()
            clustername = getclname()
            subnet = getsubnet()
            vpc = getvpc()
            keyname = getkeyname()
          else:
	    keyname = awskeyname
	    instancetype = awsinstancetype
	    subnet = awssubnet
	    clustername = awscluster
	  cpus = getcpus(instancetype)
	  dlurl = geturl()
	  stackids = set()
	  for i in range(count):
	    if isaws():
	      if vpc:
                stackid = createstackvpc(imageid, instancetype, vpc, subnet, keyname, clustername, tooldir, amqpurl,dlurl)
	      else:
                stackid = createstack(imageid, instancetype, availzone, keyname, clustername, tooldir, amqpurl,dlurl)
	    else:
	      if subnet:
	        stackid = createstackstandalone1(imageid, instancetype, keyname, subnet, clustername, tooldir, amqpurl,dlurl)
	      else:
	        stackid = createstackstandalone(imageid, instancetype, keyname, clustername, tooldir, amqpurl, dlurl)

            util.pending_pulsar_node(tooldata,awsname=stackid,cpus=cpus)
            
	    stackids.add(stackid)
            

          while True:
              time.sleep(60)
	      for stackid in stackids:
		if stackid not in ipaddresses:
                  ipaddress = describestack(stackid)
		  if ipaddress:
		    ipaddresses[stackid] = ipaddress
              if len(ipaddresses) == len(stackids):
                  break

          if isaws():
	      # openamqpport(ipaddress)
	      pass

          lock = FileLock(awsstacks)
          lock.acquire()
          try:
              wh = open(awsstacks,'a+')
	      for stackid in stackids:
                print >>wh, stackid
              wh.close()
          finally:
              lock.release()

          lock = FileLock(manualips)
          lock.acquire()
          try:
              wh = open(manualips,'a+')
	      for ipaddress in ipaddresses.values():
                print >>wh, ipaddress
              wh.close()
          finally:
              lock.release()

      else:
          raise RuntimeError("Operation start: Bad node type: %s"%type)

      for stackid,ipaddress in ipaddresses.items():
        data_table_entries.append(dict(value=ipaddress,state='start',
                                       timestamp=datetime.datetime.ctime(now),
                                       stack=stackid,cpus=str(cpus)))
        util.start_pulsar_node(tooldata,awsname=stackid,cpus=cpus,ip=ipaddress)

    elif operation == 'stop':

      if type == 'manual':

          stackid = ""

          lock = FileLock(manualips)
          lock.acquire()
          try:
              allips = open(manualips).read().split()
              wh = open(manualips,'w')
              for ip in allips:
                  if ip != ipaddress:
                      print >>wh, ip
              wh.close()
          finally:
              lock.release()

      elif type == 'aws':

          h = open(os.path.join(tooldata,'pulsar_nodes.loc'))
          ipaddress = None
          for r in csv.reader(h,dialect='excel-tab'):
              if len(r) >= 4 and r[3] == stackid and r[1] == 'start':
                  ipaddress = r[0]
          h.close()
          
          deletestack(stackid)

          lock = FileLock(awsstacks)
          lock.acquire()
          try:
              allstacks = open(awsstacks).read().split()
              wh = open(awsstacks,'w')
              for stack in allstacks:
                  if stack != stackid:
                      print >>wh, stack
              wh.close()
          finally:
              lock.release()

          lock = FileLock(manualips)
          lock.acquire()
          try:
              allips = open(manualips).read().split()
              wh = open(manualips,'w')
              for ip in allips:
                  if ip != ipaddress:
                      print >>wh, ip
              wh.close()
          finally:
              lock.release()

      if ipaddress:
        data_table_entries.append(dict(value=ipaddress,state='stop',
                                       timestamp=datetime.datetime.ctime(now),
                                       stack=stackid,cpus='-1'))
        util.stop_pulsar_node(tooldata,awsname=stackid,ip=ipaddress)
 
    elif operation == 'shutdown':

        h = open(os.path.join(tooldata,'pulsar_nodes.loc'))
        ipaddresses = {}
        for r in csv.reader(h,dialect='excel-tab'):
              if len(r) >= 4 and r[1] == 'start':
                  ipaddresses[r[3]] = r[0]
        h.close()

        stackips = set()

        for l in open(awsstacks):
	    stackid = l.strip()
            deletestack(stackid)
	    if stackid not in ipaddresses:
		continue
	    stackips.add(ipaddresses[stackid])
	    data_table_entries.append(dict(value=ipaddresses[stackid],state='stop',
                                           timestamp=datetime.datetime.ctime(now),
                                           stack=stackid,cpus='-1'))
            util.stop_pulsar_node(tooldata,awsname=stackid,ip=ipaddresses[stackid])


        lock = FileLock(awsstacks)
        lock.acquire()
        try:
            wh = open(awsstacks,'w')
            wh.close()
        finally:
            lock.release()

        lock = FileLock(manualips)
        lock.acquire()
        try:
            allips = open(manualips).read().split()
            wh = open(manualips,'w')
            for ip in allips:
                if ip in stackips:
                    print >>wh, ip
            wh.close()
        finally:
            lock.release()

    if filename:
	data_manager_dict = {}
	for data_table_entry in data_table_entries:
          data_manager_dict = add_data_table_entry( data_manager_dict, 'pulsar_node_events', data_table_entry )
        open( filename, 'wb' ).write( to_json_string( data_manager_dict ) )
    else:
        wh = open(os.path.join(tooldata,'pulsar_nodes.loc'),'w')
	for data_table_entry in data_table_entries:
	  print >>wh, "\t".join(map(data_table_entry.get,('value','state','timestamp','stack','cpus')))
	wh.close()
        
if __name__ == "__main__":
    main()
