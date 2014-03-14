# -----------------------------------------------------------------------
# XenMagic
#
# Copyright (C) 2009 Alberto Gonzalez Rodriguez alberto@pesadilla.org
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MER-
# CHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# -----------------------------------------------------------------------
import xmlrpclib, urllib
import asyncore, socket
import select
from os import chdir
import platform
import sys, shutil
import datetime
from threading import Thread
from configobj import ConfigObj
import xml.dom.minidom 
from operator import itemgetter
import pdb
import rrdinfo
import time
from messages import messages, messages_header

class addserver:
   def thread_event_next(self):
        Thread(target=self.event_next, args=()).start()
        return True

   def fill_alerts(self):
        #FIXME priority: 1 info 5 alert
        list = []
        relacion = {}
        for ref in self.all_messages.keys():
            relacion[self.get_seconds(str(self.all_messages[ref]['timestamp']))] = ref
        rkeys = relacion.keys()
        rkeys.sort(reverse=True)
        for ref in rkeys:
            message = self.all_messages[relacion[ref]]
            self.add_alert(message, relacion[ref], list)
        return list

   def fill_tree_with_vms(self, treestore, get_data=True):
        # Get all vm records
        if get_data:
            self.all_vms = self.connection.VM.get_all_records\
                      (self.session_uuid)['Value']
            result = self.connection.VM.get_all_records\
                      (self.session_uuid)
            if "Value" in result:
                self.all_vms = result['Value']
            else:
                self.wine.finish_progressconnect(False)
                if "HOST_IS_SLAVE" in result["ErrorDescription"]:
                    return "HOST IS SLAVE, please connect to: %s" % (result["ErrorDescription"][1])
                else:
                    print result
                #self.wine.show_error_dlg(str(result["ErrorDescription"]))
                return

            # Get all
            self.all_tasks = self.connection.task.get_all_records(
                      self.session_uuid)['Value']

            
            for task in self.all_tasks.keys():
                self.tasks[task] = self.all_tasks[task]
            self.all_vbd = self.connection.VBD.get_all_records(self.session_uuid)['Value']
            self.all_vbd_metrics = self.connection.VBD_metrics.get_all_records(self.session_uuid)['Value']
            self.all_vdi = self.connection.VDI.get_all_records(self.session_uuid)['Value']
            
            self.all_network = self.connection.network.get_all_records(self.session_uuid)['Value']
            self.all_pif = self.connection.PIF.get_all_records(self.session_uuid)['Value']
            self.all_pif_metrics= self.connection.PIF_metrics.get_all_records(self.session_uuid)['Value']
            self.all_pbd = self.connection.PBD.get_all_records(self.session_uuid)['Value']
            self.all_vif = self.connection.VIF.get_all_records(self.session_uuid)['Value']
            self.all_vif_metrics = self.connection.VIF_metrics.get_all_records(self.session_uuid)['Value']
            self.all_vlan = self.connection.VIF_metrics.get_all_records(self.session_uuid)['Value']

            self.all_vm_guest_metrics = self.connection.VM_guest_metrics.get_all_records(self.session_uuid)['Value']
            self.all_vm_metrics = self.connection.VM_metrics.get_all_records(self.session_uuid)['Value']
            self.all_host_metrics = self.connection.host_metrics.get_all_records(self.session_uuid)['Value']
            self.all_host_cpu = self.connection.host_cpu.get_all_records(self.session_uuid)['Value']
            self.all_bond = self.connection.Bond.get_all_records(self.session_uuid)['Value']

            self.all_pool_patch = self.connection.pool_patch.get_all_records(self.session_uuid)['Value']
            self.all_host_patch = self.connection.host_patch.get_all_records(self.session_uuid)['Value']
            self.all_console = self.connection.console.get_all_records(self.session_uuid)['Value']

            # Get all host records
            self.all_hosts = self.connection.host.get_all_records(self.session_uuid)['Value']
            # Get all pool records
            self.all_pools = self.connection.pool.get_all_records(self.session_uuid)['Value']
            self.all_storage = self.connection.SR.get_all_records(self.session_uuid)['Value']
            self.all_messages = self.connection.message.get_all_records(
                  self.session_uuid)['Value']
            self.all_console = self.connection.console.get_all_records(self.session_uuid)['Value']

        poolroot = None 
        hostroot = {}
        root = ""
        self.treestore = treestore
        self.default_sr = ""
        for pool in self.all_pools.keys():
            self.default_sr = self.all_pools[pool]['default_SR']
            if self.all_pools[pool]['name_label']:
                poolroot = pool
                treestore[pool] =  { 
                    "image" : "images/poolconnected_16.png",
                    "name" : self.all_pools[pool]['name_label'], 
                    "uuid" : pool, 
                    "type" : "pool", 
                    "state" : "Running", 
                    "host" : self.host, 
                    "ref" : pool, 
                    "actions" : ['newvm', 'importvm', 'newstorage', 'disconnect', 'properties'], 
                    "ip" : self.host,
                    "children" : []
                    }
                if pool not in treestore["home"]["children"]:
                    treestore["home"]["children"].append(pool)
                

        if poolroot:
            relacion = {}
            for ref in self.all_hosts.keys():
                relacion[str(unicode(self.all_hosts[ref]['name_label'] + "_" + ref))] = ref
            self.all_hosts_keys = []
            rkeys = relacion.keys()
            rkeys.sort(key=str.lower)
            for ref in rkeys:
                self.all_hosts_keys.append(relacion[ref])
            for h in self.all_hosts_keys:
                host_uuid = self.all_hosts[h]['uuid']
                host = self.all_hosts[h]['name_label']
                host_enabled = self.all_hosts[h]['enabled']
                host_address = self.all_hosts[h]['address']
                hostroot[h] = h     
                if host_enabled:
                    treestore[h] = {
                                "image" : "images/tree_connected_16.png",
                                "name" : host, 
                                "uuid" : host_uuid, 
                                "type" : "host", 
                                "state" : "Running",
                                "host" :  self.host, 
                                "ref" : h,
                                "actions" : ['newvm', 'importvm', 'newstorage', 'clean_reboot', 'shutdown', 'disable', 'properties'], 
                                "ip" : host_address,
                                "children": []
                            }
                    if poolroot and h not in treestore[poolroot]["children"]:
                        treestore[poolroot]["children"].append(h)
                else:
                    treestore[h] = {
                                "image" : "images/tree_disabled_16.png",
                                "name": host, 
                                "uuid": host_uuid, 
                                "type" : "host", 
                                "state" : "Disconnected", 
                                "host" : self.host,
                                "ref" :  h, 
                                "actions" : ['enable', 'properties'], 
                                "ip" : host_address,
                                "children": []
                            }
                    if poolroot and h not in treestore[poolroot]["children"]:
                        treestore[poolroot]["children"].append(h)
            root = poolroot
        else:
           host_uuid = self.all_hosts[self.all_hosts.keys()[0]]['uuid']
           host = self.all_hosts[self.all_hosts.keys()[0]]['name_label']
           host_address = self.all_hosts[self.all_hosts.keys()[0]]['address']
           ref = self.all_hosts.keys()[0]
           host_enabled = self.all_hosts[self.all_hosts.keys()[0]]['enabled']
           if host_enabled:
               treestore[ref] = {
                            "image" : "images/tree_connected_16.png",
                            "name" : host, 
                            "uuid" : host_uuid, 
                            "type" : "host", 
                            "state" : "Running", 
                            "host" : self.host, 
                            "ref" : ref,
                            "actions" : ['newvm', 'importvm', 'newstorage', 'clean_reboot', 'shutdown', 'disconnect', 'disable', 'properties'], 
                            "ip" : host_address,
                            "children" : []
                            }
           else:
               treestore[ref] = {
                            "image" : "images/tree_disabled_16.png",
                            "name" : host, 
                            "uuid" : host_uuid, 
                            "type" : "host", 
                            "state" : "Running", 
                            "host" : self.host, 
                            "ref" : ref,
                            "actions" : ['clean_reboot', 'shutdown', 'disconnect', 'enable', 'properties'], 
                            "ip" : host_address,
                            "children" : []
                            }
           hostroot[self.all_hosts.keys()[0]] = ref
           if ref not in treestore["home"]["children"]:
               treestore["home"]["children"].append(ref)
           root = ref
        self.hostname = host
        self.hostroot = hostroot
        self.poolroot = poolroot
        relacion = {}
        for ref in self.all_vms.keys():
            if isinstance(self.all_vms[ref]['name_label'] + "_" + ref, str):
                relacion[str(unicode(self.all_vms[ref]['name_label'] + "_" + ref)).lower()] = ref
            else:
                relacion[self.all_vms[ref]['name_label'].lower() + "_" + ref] = ref
        self.all_vms_keys = []
        rkeys = relacion.keys()
        rkeys.sort()
        rkeys.reverse()
        for ref in rkeys:
            self.all_vms_keys.insert(0,relacion[ref])


        for vm in self.all_vms_keys:
            if not self.all_vms[vm]['is_a_template']:
                if not self.all_vms[vm]['is_control_domain']:
                  self.add_vm_to_tree(vm, treestore)
                  for operation in self.all_vms[vm]["current_operations"]:
                    self.track_tasks[operation] = vm
                else:
                  self.host_vm[self.all_vms[vm]['resident_on']] = [vm,  self.all_vms[vm]['uuid']]
  
        # Get all storage record 
        for sr in self.all_storage.keys():
            if "name_label" in self.all_storage[sr] and self.all_storage[sr]['name_label'] != "XenServer Tools":
                if len(self.all_storage[sr]['PBDs']) == 0:
                    treestore[sr] = {
                            "image" : "images/storage_detached_16.png",
                            "name" : self.all_storage[sr]['name_label'], 
                            "uuid" : self.all_storage[sr]['uuid'],
                            "type" : "storage", 
                            "state" : "local", 
                            "host" : self.host, 
                            "ref" : sr, 
                            "actions": self.all_storage[sr]['allowed_operations'] + ['properties'], 
                            "ip" : self.host,
                            "children": []
                            }
                    if root and sr not in treestore[root]["children"]:
                        treestore[root]["children"].append(sr)
                        continue
                    if self.all_storage[sr]['shared']:
                        treestore[sr]["state"] = "shared"
                broken = False
                for pbd_ref in self.all_storage[sr]['PBDs']:
                    if not self.all_pbd[pbd_ref]['currently_attached']:
                        broken = True
                        treestore[sr] = {
                               "image" : "images/storage_broken_16.png",
                               "name" : self.all_storage[sr]['name_label'],
                                "uuid" : self.all_storage[sr]['uuid'],
                                "type" : "storage",
                                "state" : "local",
                                "host" : self.host,
                                "ref" : sr,
                                "actions": self.all_storage[sr]['allowed_operations'] + ['properties'],
                                "ip" : self.host,
                                "children": []
                            }
                        if self.all_storage[sr]['shared']:
                            treestore[sr]["state"] = "shared"
                        if root and sr not in treestore[root]["children"]:
                            treestore[root]["children"].append(sr)
                if not broken:
                    if self.all_storage[sr]['shared']:
                        if sr == self.default_sr:
                            image = "images/storage_default_16.png"
                        else:
                            image = "images/storage_shaped_16.png"
                        treestore[sr] = {
                               "image" : image,
                               "name" : self.all_storage[sr]['name_label'],
                                "uuid" : self.all_storage[sr]['uuid'],
                                "type" : "storage",
                                "state" : "shared",
                                "host" : self.host,
                                "ref" : sr,
                                "actions": self.all_storage[sr]['allowed_operations'] + ['properties'],
                                "ip" : self.host,
                                "children": []
                            }
                        if root and sr not in treestore[root]["children"]:
                            treestore[root]["children"].append(sr)

                    else:
                        for pbd in self.all_storage[sr]['PBDs']:
                            if sr == self.default_sr:
                                if self.all_pbd[pbd]['host'] in hostroot:
                                    image = "images/storage_default_16.png"
                                    parent = self.all_pbd[pbd]['host']
                                else:
                                    image = "images/storage_shaped_16.png"
                                    parent = root
                            else:
                                if self.all_pbd[pbd]['host'] in hostroot:
                                    image = "images/storage_shaped_16.png"
                                    parent = self.all_pbd[pbd]['host']
                                else:
                                    image = "images/storage_shaped_16.png"
                                    parent = root

                            treestore[sr] = {
                                   "image" : image,
                                   "name" : self.all_storage[sr]['name_label'],
                                    "uuid" : self.all_storage[sr]['uuid'],
                                    "type" : "storage",
                                    "state" : "local",
                                    "host" : self.host,
                                    "ref" : sr,
                                    "actions": self.all_storage[sr]['allowed_operations'] + ['properties'],
                                    "ip" : self.host,
                                    "children": []
                                }
                            if parent and sr not in treestore[parent]["children"]:
                                treestore[parent]["children"].append(sr)

                    
        for tpl in self.all_vms_keys:
            if self.all_vms[tpl]['is_a_template'] and not self.all_vms[tpl]['is_a_snapshot']: 
                if self.all_vms[tpl]['last_booted_record'] == "":
                        treestore[tpl] = {
                                   "image" : "images/template_16.png",
                                   "name" : self.all_vms[tpl]['name_label'],
                                   "uuid" : self.all_vms[tpl]['uuid'],
                                   "type" : "template",
                                   "state" : None,
                                   "host" : self.host,
                                   "ref" : tpl,
                                   "actions": self.all_vms[tpl]['allowed_operations'] + ['properties'],
                                   "ip" : self.host,
                                   "children": []
                                }
                        if root and tpl not in treestore[root]["children"]:
                            treestore[root]["children"].append(tpl)

                else:
                     tpl_affinity = self.all_vms[tpl]['affinity']
                    
                     if tpl_affinity in hostroot: 
                            treestore[tpl] = {
                                   "image" : "images/user_template_16.png",
                                   "name" : self.all_vms[tpl]['name_label'],
                                   "uuid" : self.all_vms[tpl]['uuid'],
                                   "type" : "custom_template",
                                   "state" : None,
                                   "host" : self.host,
                                   "ref" : tpl,
                                   "actions": self.all_vms[tpl]['allowed_operations'] + ['properties'],
                                   "ip" : self.host,
                                   "children": []
                                }
                            if tpl not in treestore[tpl_affinity]["children"]:
                                treestore[tpl_affinity]["children"].append(tpl)
                     else:
                            treestore[tpl] = {
                                   "image" : "images/user_template_16.png",
                                   "name" : self.all_vms[tpl]['name_label'],
                                   "uuid" : self.all_vms[tpl]['uuid'],
                                   "type" : "custom_template",
                                   "state" : None,
                                   "host" : self.host,
                                   "ref" : tpl,
                                   "actions": self.all_vms[tpl]['allowed_operations'] + ['properties'],
                                   "ip" : self.host,
                                   "children": []
                                }
                            if tpl not in treestore[root]["children"]:
                                treestore[root]["children"].append(tpl)
        return "OK"

