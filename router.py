#! /usr/bin/python3

'''
 Copyright 2020-present SK Telecom
 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at
     http://www.apache.org/licenses/LICENSE-2.0
 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
'''

import os
import shlex
import sys
import time
import docker
import subprocess

CONTAINER_IMAGE = "opensona/router-docker"
FLOATING_CIDR = "172.40.0.1/24"
EXTERNAL_PEER_MAC = "fa:00:00:00:00:01"
BRIDGE_PREFIX = "kbr-"
PRIMARY_INTF = "eth0"
SECONDARY_INTF = "eth1"

def call_popen(cmd):
    '''
    Executes a shell command.
    :param    cmd: shell command to be executed
    :return    standard output of the executed result
    '''
    child = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output = child.communicate()
    if child.returncode:
        raise RuntimeError("Fatal error executing %s" % (cmd))
    if len(output) == 0 or output[0] is None:
        output = ""
    else:
        output = output[0].decode("utf8").strip()
    return output

def call_prog(prog, args_list):
    '''
    Executes shell command along with a set of arguments.
    :param    prog:      program binary path
                args_list: arguments of the program
    :return    standard output of the executed result
    '''
    cmd = ["sudo", prog, "--timeout=5", "-vconsole:off"] + args_list
    return call_popen(cmd)

def call_prog2(prog, args_list):
    '''
    Executes shell command along with a set of arguments.
    :param    prog:      program binary path
                args_list: arguments of the program
    :return    standard output of the executed result
    '''
    cmd = ["sudo", prog] + args_list + ["--timeout=5", "-vconsole:off"]
    return call_popen(cmd)

def ovs_vsctl(*args):
    '''
    A helper method to execute ovs-vsctl.
    :param    args:     arguments pointer
    :return    executed result of ovs-vsctl
    '''
    return call_prog("ovs-vsctl", list(args))

def ovs_ofctl(*args):
    '''
    A helper method to execute ovs-ofctl.
    :param    args:    arguments pointer
    :return    executed result of ovs-ofctl
    '''
    return call_prog("ovs-ofctl", list(args))

def pipework(*args):
    '''
    A helper method to execute pipework.
    :param    args:     arguments pointer
    :return    executed result of pipework
    '''
    return call_prog2("pipework", list(args))

def run_router(name):
    '''
    Spawns a new docker container which mimics router behavior.
    :param    name:     name of router
    '''
    client = docker.from_env()
    containers = client.containers.list(all=True)
    for container in containers:
        if container.name == name:
            print ("The given container " + name +" already exists!")
            return

    kernel_cap = ['NET_ADMIN', 'NET_RAW']
    container = client.containers.run(CONTAINER_IMAGE, name=name, detach=True, privileged=True, cap_add=kernel_cap)
    print ("The container was created with ID "+container.id+".")

def stop_router(name):
    '''
    Terminates a docker container.
    :param    name:     name of router
    '''
    client = docker.from_env()
    containers = client.containers.list(all=True)
    for container in containers:
        if container.name == name:
            container.stop()
            container.remove(force=True)
            print ("The container " + name +" was terminated!")
            return

    print ("The given container " + name +" is not found!")

def create_bridge(name):
    '''
    Creates a OVS bridge used for processing routing traffic.
    :param    name:     name of router
    '''
    bridge_name = BRIDGE_PREFIX + name
    bridges = ovs_vsctl('list-br')
    if bridge_name in bridges.splitlines():
        print ("The given bridge " + bridge_name +" already exists!")
        return

    ovs_vsctl("add-br", bridge_name)
    print ("The router bridge " + bridge_name +" was created!")

def delete_bridge(name):
    '''
    Deletes a OVS bridge used for processing routing traffic.
    :param    name:     name of router
    '''
    bridge_name = BRIDGE_PREFIX + name
    bridges = ovs_vsctl('list-br')
    if bridge_name not in bridges.splitlines():
        print ("The given bridge " + bridge_name +" is not found!")
        return

    ovs_vsctl("del-br", bridge_name)
    print ("The router bridge " + bridge_name +" was removed!")

def config_pipework(name):
    '''
    Attaches the router container's interface to OVS router bridge.
    :param    name:     name of router
    '''
    bridge_name = BRIDGE_PREFIX + name
    ports = ovs_vsctl('list-ports', bridge_name)
    if name in  ports.splitlines():
        print ("The given bridge " + bridge_name +" already contains port " + name + "!")
        return

    bridge_name = BRIDGE_PREFIX + name
    pipework(bridge_name, "-i", SECONDARY_INTF, "-l", name, name, FLOATING_CIDR, EXTERNAL_PEER_MAC)
    print ("The pipework configuration was enforced to " + name +"!")

def config_nat(name):
    '''
    Configures the router to SNAT/DNAT the outbound/inbound traffic.
    :param    name:     name of router
    '''
    client = docker.from_env()
    try:
        container = client.containers.get(name)
    except docker.errors.NotFound:
        print ("The given container "+name+" is not found!")
        return

    container = client.containers.get(name)
    container.exec_run("iptables -t nat -A POSTROUTING -o "+PRIMARY_INTF+" -j MASQUERADE", detach=True)
    print ("The NAT configuration was enforced to " + name +"!")

def main():
    router_name = "router-200"
    #create_bridge(router_name)
    #run_router(router_name)
    #config_pipework(router_name)
    #config_nat(router_name)
    #delete_bridge(router_name)
    #stop_router(router_name)

if __name__ == '__main__':
    main()
