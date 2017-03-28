#! /usr/bin/env python

from paramiko import SSHClient
from scp import SCPClient

ssh = SSHClient()
ssh.load_system_host_keys()
ssh.connect('10.1.10.157')
scp = SCPClient(ssh.get_transport())
scp.put('BIGIP-11.6.1.0.0.317.iso.md5',remote_path='/shared/images')
scp.put('BIGIP-11.6.1.0.0.317.iso',remote_path='/shared/images')
scp.close()
