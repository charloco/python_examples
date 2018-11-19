from __future__ import print_function
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
import os
import paramiko
from subprocess import Popen,PIPE
import time
import sys
import socket
import threading
import select

ovsdb_socket = '/var/run/openvswitch/db.sock'
def get_ssh_conn_setting():
    return dict(hostname='localhost',
                username='root',
                password='password'
               )
def ssh_connect_client():
    conn_info = get_ssh_conn_setting()
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(**conn_info)
    return ssh_client
class OvsdbForward(LineReceiver):
    def __init__(self):
        self.delimiter= '\n' 
        self.setRawMode()
        self.client = None
        self.stdin = None
        self.stdout = None
        self.worker = threading.Thread(target=self.run)
        self.worker.setDaemon(True)
        self.stopped = False
    def connectionMade(self):
        print("connected")
        self.client = ssh_connect_client()
        stdin,stdout,stderr=self.client.exec_command("nc -U %s"%ovsdb_socket)
        self.stdin = stdin
        self.stdout = stdout
        self.stdout_fd = stdout.channel.fileno()
        stdout.channel.settimeout(0.2)
        self.worker.start()

    def run(self):
        while not self.stopped:
            line = self.stdout_read()
            if line != '':
                line+='\n'
                self.sendLine(line)

    def stdout_read(self):
        out = ''

        while not self.stopped:
            rfds,wfds,efds = select.select([self.stdout_fd],[],[],10)
            if len(rfds)>0:
                length= len(self.stdout.channel.in_buffer)
                if length >0:
                    out += self.stdout.read(length)
                    break

        return out


    def rawDataReceived(self,data):
        self.stdin.write(data+'\n')
        self.stdin.flush()

    def connectionLost(self,reason):
        self.stopped = True
        print("closed")
        if self.client is not None:
            self.client.close()
def start_twisted_unix_server():
    serverFactory = Factory()
    serverFactory.protocol = OvsdbForward
    port = reactor.listenUNIX(ovsdb_socket,serverFactory)
    reactor.run()

start_twisted_unix_server()
