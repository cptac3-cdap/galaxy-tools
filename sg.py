#!/usr/bin/env python
import cm.app, sys
app = cm.app.UniverseApplication()
sgid = app.cloud_interface.get_instance_object().groups[0].id
conn = app.cloud_interface.get_ec2_connection()
sg = conn.get_all_security_groups(group_ids=[sgid]).pop()
for r in sg.rules:
    if r.ip_protocol == 'tcp' and int(r.from_port) in (22,80,443):
        continue
    if r.groups:
        continue
    for grants in r.grants:
        if grants.cidr_ip:
            print "revoking ingress rule with source as cidr_ip"
            print sg.name, r.ip_protocol, r.from_port, r.to_port, grants.cidr_ip
            conn.revoke_security_group(group_name=sg.name, ip_protocol=r.ip_protocol, from_port=r.from_port, to_port=r.to_port, cidr_ip=grants.cidr_ip)
        else:
            print "revoking ingress rule with source as security group"
            print sg.name, r.ip_protocol, r.from_port, r.to_port, grants.name
            if grants.name == 'amazon-elb-sg':
                print "revoking ingress rule with ELB as security group"
                conn.revoke_security_group(group_name=sg.name, ip_protocol=r.ip_protocol, from_port=r.from_port, to_port=r.to_port, src_security_group_group_id=grants.group_id,src_security_group_owner_id='amazon-elb')
            else:
                conn.revoke_security_group(group_name=sg.name, ip_protocol=r.ip_protocol, from_port=r.from_port, to_port=r.to_port, src_security_group_name=grants.name)
