# -----------------------------------------------------------------------
# XenWebManager 
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
import os
import platform
import sys, shutil
import datetime
import xml.dom.minidom 
import pdb
import rrdinfo
import time
from rrd import RRD, XPORT
import xml.sax.saxutils as saxutils
import traceback
import put

from threading import Thread
from configobj import ConfigObj
from operator import itemgetter
from messages import messages, messages_header

from vm import *
from host import *
from properties import *
from storage import *
from alerts import *
from addserver import *
from newvm import *
from menuitem import *
from capabilities import capabilities_text
import httplib

class backend(vm,host,properties,storage,alerts,addserver,newvm,menuitem):
    session_uuid = None
    error_connecting = ""
    is_connected = False 
    host_vm = {}
    set_descriptions = {}
    halt = False
    halt_search = False
    halt_import = False
    track_tasks = {}
    tasks = {}
    vboxchildcancel = {}
    vboxchildprogressbar = {}
    vboxchildprogress = {}
    autostart = {}
    vif_plug = []
    flag_vif_plug = False
    found_iter = ""
    import_ref = None
    import_start = False
    import_make_into_template = False
    poolroot = None
    hostroot = {}
    last_storage_iter = None
    pbdcreate = []
    connecting = False
    export_snap = None
    def __init__(self, host, user, password, ssl = False, connect = True):
        self.host = host
        self.hostname = host
        self.user = user
        self.password = password
        self.ssl = ssl 
        self.updates = []
        self.alert = ""
        if connect:
            self.connect(host, user, password, ssl)
            self.connecting = True

    def update_connect_status(self):
        while self.connecting:
            self.wine.builder.get_object("progressconnect").pulse()
            time.sleep(1)
        gtk.gdk.threads_enter()
        self.wine.finish_add_server(self.host, self.user, self.password, None, ssl=self.ssl)
        gtk.gdk.threads_leave()

    def reconnect(self):
        self.connect(self.host, self.user, self.password, self.ssl)

    def connect(self, host, user, password, ssl):
        if ssl:
            self.connection = xmlrpclib.Server("https://%s" % host)
        else:
            self.connection = xmlrpclib.Server("http://%s" % host)
        try:
            self.session = \
                    self.connection.session.login_with_password(user, password) 
            if self.session['Status']  == "Success":
                self.is_connected = True
                self.host = host
                self.hostname = host
                self.session_uuid = self.session['Value']
                self.connection.event.register(self.session_uuid, ["*"])
            else:
                self.error_connecting = self.session['ErrorDescription'][2]
        except:
            self.error_connecting = sys.exc_info()[1]
        self.connecting = False 

    def logout(self):
        self.halt_search = True
        self.halt = True
        if self.is_connected:
            self.connection.event.unregister(self.session_uuid, ["*"])
            self.connection.session.logout(self.session_uuid) 
            self.is_connected = False

    def file2Generator(self, f):
        while True:
            data = f.read(1024 * 8) # Read blocks of 8KB at a time
            if self.export_snap:                
                self.connection.VM.set_is_a_template(self.session_uuid, self.export_snap, True)
                self.export_snap = None
            if not data: 
                break
            yield data

    def get_network_relation(self, ref, show_halted_vms):
        # Get network -> VM relation
        relation = {}
        for network in self.all_network:
            network_name = self.all_network[network]['name_label'].replace('Pool-wide network associated with eth','Network ')
            vms = []
            for vif in self.all_network[network]['VIFs']:
                vm = self.all_vif[vif]['VM']
                if not vms.count(vm + "_" +  self.all_vms[vm]['name_label']):
                    if show_halted_vms or  self.all_vms[vm]['power_state'] == "Running":
                        vms.append(vm + "_" +  self.all_vms[vm]['name_label'])
            relation[network + "_" + network_name] = vms

        return relation

    def get_storage_relation(self, ref, show_halted_vms):
        # Get network -> VM relation
        relation = {}
        for storage in self.all_storage:
            storage_name = self.all_storage[storage]['name_label']
            vms = []
            for vdi in self.all_storage[storage]['VDIs']:
                vbds = self.all_vdi[vdi]['VBDs']
                for vbd in vbds:
                    vm = self.all_vbd[vbd]['VM']
                    if not vms.count(vm + "_" +  self.all_vms[vm]['name_label']):
                        if show_halted_vms or  self.all_vms[vm]['power_state'] == "Running":
                            vms.append(vm + "_" +  self.all_vms[vm]['name_label'])
            relation[storage+ "_" + storage_name] = vms

        return relation

    def prueba(self):
        networks = self.connection.network.get_all_records(self.session_uuid)['Value']
        for network in networks:
            print networks[network]['name_label']
            vms = []
            for vif in networks[network]['VIFs']:
                vms.append(self.connection.VIF.get_record(self.session_uuid, vif)['Value']['VM'])
            # Remove duplicates
            set = {}
            map(set.__setitem__, vms, [])
            for vm in set.keys():
                print "\t" + self.connection.VM.get_record(self.session_uuid, vm)['Value']['name_label']

        storages = self.connection.SR.get_all_records(self.session_uuid)['Value']
        for storage in storages:
            vms = []
            print storages[storage]['name_label']
            for vdi in storages[storage]['VDIs']:
                vbds = self.connection.VDI.get_record(self.session_uuid, vdi)['Value']['VBDs']
                for vbd in vbds:
                    vms.append(self.connection.VBD.get_record(self.session_uuid, vbd)['Value']['VM'])
            set = {}
            map(set.__setitem__, vms, [])
            for vm in set.keys():
                print "\t" + self.connection.VM.get_record(self.session_uuid, vm)['Value']['name_label']

    def export_vm(self, uuid):
        vm_uuid = self.connection.VM.get_by_uuid(self.session_uuid, uuid)['Value']
        print "GET /export?ref=%s&session_id=%s HTTP/1.1\r\n\r\n" % (vm_uuid,self.session_uuid)
    def get_seconds(self, toconvert):
        converted = time.strptime(str(toconvert), "%Y%m%dT%H:%M:%SZ")
        totime = time.mktime(converted)
        #FIXME
        return totime
    def format_date(self, toconvert):
        #converted = time.strptime(str(toconvert), "%Y%m%dT%H:%M:%SZ")
        converted = datetime.datetime(*time.strptime(str(toconvert), "%Y%m%dT%H:%M:%SZ")[0:5])
        #totime = time.mktime(converted.timetuple())
        return str(converted)
    #FIXME
    def get_seconds_difference_reverse(self, toconvert):
        converted = time.strptime(str(toconvert), "%Y%m%dT%H:%M:%SZ")
        totime = time.mktime(converted)
        #FIXME
        return totime-time.time()-3600
    def get_seconds_difference(self, toconvert):
        converted = time.strptime(str(toconvert), "%Y%m%dT%H:%M:%SZ")
        totime = time.mktime(converted)
        #FIXME
        return time.time()-totime-3600
    def get_dmesg(self, ref):
        return self.connection.host.dmesg(self.session_uuid, ref)["Value"]

    def restore_server(self, host, ref, myfile, name):
        import httplib
        task_uuid = self.connection.task.create(self.session_uuid, "Restoring Server", "Restoring Server %s from %s " % (name,myfile.filename))
        self.track_tasks[task_uuid['Value']] = "Restore.Server"
        fp = myfile.file
        put.putfile(fp, 'http://' + host + '/host_restore?session_id=%s&task_id=%s&dry_run=true' % (self.session_uuid, task_uuid['Value']))
        return
        conn = httplib.HTTP(host)
        conn.putrequest('PUT', '/pool/xmldbdump?session_id=%s&task_id=%s&dry_run=true' % (self.session_uuid, task_uuid['Value']))
        conn.putheader('Content-Type', 'text/plain')
        conn.endheaders()
        fp = myfile.file
        blocknum=0
        uploaded=0
        blocksize=4096
        while not self.halt_import:
            bodypart=fp.read(blocksize)
            blocknum+=1
            if blocknum % 10 == 0:
                uploaded+=len(bodypart)

            if not bodypart: break
            conn.send(bodypart)
        fp.close()

    def save_screenshot(self, host, ref):
        console_ref = self.all_vms[ref]["consoles"][0]
        location = self.all_console[console_ref]["location"]

        #url = "http://" + host + '/vncsnapshot?session_id=%s&ref=%s' % (self.session_uuid, ref)
        url = location.replace("console","vncsnapshot") + "&session_id=" + self.session_uuid
        return urllib.urlopen(url)


    def pool_backup_database(self, host, ref,  name):
        task_uuid = self.connection.task.create(self.session_uuid, "Backup Pool database", "Backing up database pool " + name)
        self.track_tasks[task_uuid['Value']] = "Backup.Pool"
        url = "http://" + host + '/pool/xmldbdump?session_id=%s&task_id=%s' % (self.session_uuid, task_uuid['Value'])
        return urllib.urlopen(url)

    def pool_restore_database(self, host, ref, myfile, name, dry_run="true"):
        import httplib
        task_uuid = self.connection.task.create(self.session_uuid, "Restore Pool database", "Restoring database pool " + myfile.filename)
        self.track_tasks[task_uuid['Value']] = "Restore.Pool"
        fp = myfile.file
        put.putfile(fp, 'http://' + host + '/pool/xmldbdump?session_id=%s&task_id=%s&dry_run=%s' % (self.session_uuid, task_uuid['Value'], dry_run))
        return
        conn = httplib.HTTP(host)
        conn.putrequest('PUT', '/pool/xmldbdump?session_id=%s&task_id=%s&dry_run=%s' % (self.session_uuid, task_uuid['Value'], dry_run))
        conn.endheaders()
        total = 0
        while True:
            leido = fp.read(16384)
            if leido:
                total += len(leido)
                time.sleep(0.1) 
                conn.send(leido) 
            else:
                break
        fp.close()

    def host_download_logs(self, host, ref, name):
        task_uuid = self.connection.task.create(self.session_uuid, "Downloading host logs", "Downloading logs from host " + name)
        self.track_tasks[task_uuid['Value']] = "Download.Logs"
        url = "http://" + host + '/host_logs_download?session_id=%s&sr_id=%s&task_id=%s' % (self.session_uuid, ref, task_uuid['Value'])
        return urllib.urlopen(url)

    def host_download_status_report(self, host, ref, refs, name):
        task_uuid = self.connection.task.create(self.session_uuid, "Downloading status report", "Downloading status report from host " + name)
        self.track_tasks[task_uuid['Value']] =  self.host_vm[ref][0]
        url = "https://" + host + '/system-status?session_id=%s&entries=%s&task_id=%s&output=tar' % (self.session_uuid, refs, task_uuid['Value'])
        return urllib.urlopen(url)

    def backup_server(self,host, ref, name):
        task_uuid = self.connection.task.create(self.session_uuid, "Backup Server", "Backing up server " + name)
        self.track_tasks[task_uuid['Value']] = "Backup.Server"
        url = "http://" + host + '/host_backup?session_id=%s&sr_id=%s&task_id=%s' % (self.session_uuid, ref, task_uuid['Value'])
        return urllib.urlopen(url)


    def import_vm(self, host, ref):
        import httplib
        task_uuid = self.connection.task.create(self.session_uuid, "Importing VM", "Importing VM ")
        self.track_tasks[task_uuid['Value']] = "Import.VM"
        importhost = host
        importpath = '/import?session_id=%s&sr_id=%s&task_id=%s' % (self.session_uuid, ref, task_uuid['Value'])
        return (importhost, importpath)
        put.putfile(fp, 'http://' + host + '/import?session_id=%s&sr_id=%s&task_id=%s' % (self.session_uuid, ref, task_uuid['Value']))


        conn = httplib.HTTP(host)
        conn.putrequest('PUT', '/import?session_id=%s&sr_id=%s&task_id=%s' % (self.session_uuid, ref, task_uuid['Value']))
        conn.putheader('Content-Type', 'text/plain')
        conn.endheaders()
        blocknum=0
        uploaded=0
        blocksize=4096
        fp = myfile.file
        while not self.halt_import:
            bodypart=fp.read(blocksize)
            blocknum+=1
            if blocknum % 10 == 0:
                uploaded+=len(bodypart)
            if blocknum % 1000 == 0:
                time.sleep(0.1) 

            if not bodypart: break
            conn.send(bodypart)
        fp.close()

    def add_alert(self, message, ref, list):
        if message['cls'] == "Host":
            if message['name'] in messages:
                parent = list.append(["images/info.png", 
                    self.hostname, messages_header[message['name']], self.format_date(str(message['timestamp'])),
                    ref, self.host])
                list.append([None, "", messages[message['name']] % (self.hostname), "",
                    ref, self.host])
            else:
                parent = list.append(["images/info.png", 
                    self.hostname, message['name'], self.format_date(str(message['timestamp'])),
                    ref, self.host])
                list.append([None, "", message['name'], "",
                    ref, self.host])
        elif message['name'] == "ALARM":
            self.filter_uuid = message['obj_uuid']
            if self.vm_filter_uuid() not in self.all_vms:
                return None
            if not self.all_vms[self.vm_filter_uuid()]['is_control_domain']:
                value = message['body'].split("\n")[0].split(" ")[1]
                dom = xml.dom.minidom.parseString(message['body'].split("config:")[1][1:])
                nodes = dom.getElementsByTagName("name")
                #alert = message['body'].split('value="')[1].split('"')[0]
                alert = nodes[0].attributes.getNamedItem("value").value
                nodes = dom.getElementsByTagName("alarm_trigger_level")
                level = nodes[0].attributes.getNamedItem("value").value
                nodes = dom.getElementsByTagName("alarm_trigger_period")
                period = nodes[0].attributes.getNamedItem("value").value

                if "alert_" + alert in messages:
                    parent = list.append(["images/warn.png",
                        self.hostname, messages_header["alert_" + alert],
                        self.format_date(str(message['timestamp'])), ref, self.host])
                    list.append([None, "", messages["alert_" + alert] % \
                            (self.all_vms[self.vm_filter_uuid()]['name_label'], float(value)*100, int(period), float(level)*100), "",
                            ref, self.host])
                else:
                    print message['name']
                    print message['body']
            else:
                value = message['body'].split("\n")[0].split(" ")[1]
                alert = message['body'].split('value="')[1].split('"')[0]
                if "host_alert_" + alert in messages:
                    parent = list.append(["images/warn.png",
                        self.hostname, messages_header["host_alert_" + alert] % ("Control Domain"),
                        self.format_date(str(message['timestamp'])), ref, self.host])
                    list.append([None, "", messages["host_alert_" + alert] % \
                            ("Control Domain", self.hostname, float(value)), "",
                            ref, self.host])
                else:
                    print message['name']
                    print message['body']

    def add_vm_to_tree(self, vm, treestore):
        if  self.all_vms[vm]['resident_on'] != "OpaqueRef:NULL" and self.all_vms[vm]['resident_on'] in treestore:
            parent = self.all_vms[vm]['resident_on']
            ip = self.all_hosts[parent]['address']
        elif self.all_vms[vm]['affinity'] != "OpaqueRef:NULL" and self.all_vms[vm]['affinity'] in self.all_vms:
            parent = self.all_vms[vm]['affinity']
            ip = self.all_hosts[parent]['address']
        else:
            if self.poolroot:
                parent = self.poolroot
                ip = self.host
            else:
                parent = self.all_hosts.keys()[0]
                ip = self.host
        if self.all_vms[vm]["current_operations"]:
            image = "images/tree_starting_16.png"
        else:
            image = "images/tree_%s_16.png" % self.all_vms[vm]['power_state'].lower()
        self.treestore[vm] = {
                   "image" : image,
                   "name" : self.all_vms[vm]['name_label'],
                   "uuid" : self.all_vms[vm]['uuid'],
                   "type" : "vm",
                   "state" : self.all_vms[vm]['power_state'],
                   "host" : self.host,
                   "ref" : vm,
                   "actions": self.all_vms[vm]['allowed_operations'] + ['properties'],
                   "ip" : ip,
                   "HideFromXenCenter": "false",
                   "children": []
                }
        if str(self.all_vms[vm]["other_config"].get("HideFromXenCenter")).lower() == "true":
             self.treestore[vm]["HideFromXenCenter"] = "true"
        if vm not in treestore[parent]["children"]:
            treestore[parent]["children"].append(vm)

    def fill_allowed_operations(self, ref):
        actions = self.connection.VM.get_allowed_operations(self.session_uuid, ref)['Value']
        self.all_vms[ref]['allowed_operations'] = actions
        return actions

    def fill_vm_network(self, ref):
        list = []
        if ref in self.all_vms:
            guest_metrics = self.all_vms[ref]['guest_metrics']

            for vif_ref in self.all_vms[ref]['VIFs']:
                vif = self.all_vif[vif_ref]
                if "kbps" in vif['qos_algorithm_params']:
                    limit =  vif['qos_algorithm_params']['kbps']
                else:
                    limit = ""
                ip = ""
                if guest_metrics in self.all_vm_guest_metrics and vif['device'] + "/ip" in self.all_vm_guest_metrics[guest_metrics]['networks']:
                    ip = self.all_vm_guest_metrics[guest_metrics]['networks'][vif['device'] + "/ip"]
                else:
                    ip = ""

                #FIXME
                if vif['network'] in self.all_network:
                    network =  self.all_network[vif['network']]['name_label'].replace('Pool-wide network associated with eth','Network ')
                else:
                    network = ""
                list.append((vif['device'], \
                        vif['MAC'], \
                        limit, \
                        network, \
                        ip, \
                        str(vif['currently_attached']), vif_ref, vif['allowed_operations'].count("attach")))
        else:
            print "VM not found %s" % ref 

        return list

    def set_vif_limit(self, ref, limit, vm_ref):
      qos_algorithm_params = {
        'kbps': str(limit)
      }
      res = self.connection.VIF.set_qos_algorithm_params(self.session_uuid, ref, qos_algorithm_params)
      if "Value" in res:
          self.track_tasks[res['Value']] = vm_ref
      else:
          print res
    def set_vif_to_manual(self, ref, vm_ref):
      res = self.connection.VIF.set_MAC_autogenerated(self.session_uuid, ref, False)
      if "Value" in res:
          self.track_tasks[res['Value']] = vm_ref
      else:
          print res


    def fill_vm_snapshots(self, ref, name):
        list = [] 
        if ref in self.all_vms:
            all_snapshots = self.all_vms[ref]['snapshots']
            print all_snapshots
            for snapshot_ref in all_snapshots:
                snapshot_name = self.all_vms[snapshot_ref]['name_label']
                snapshot_time = self.format_date(self.all_vms[snapshot_ref]['snapshot_time'])
                snapshot_of = self.all_vms[snapshot_ref]['snapshot_of']
                snapshot_ops = self.all_vms[snapshot_ref]['allowed_operations']
                snapshot_size = 0 
                for vbd in self.all_vms[snapshot_ref]['VBDs']:
                    vbd_data = self.all_vbd[vbd]
                    if vbd_data['type'] == 'Disk':
                        snapshot_size += int(self.all_vdi[vbd_data['VDI']]['physical_utilisation'])
                list.append([snapshot_ref, "<b>" + snapshot_name + "</b><br><br>Taken on: " + str(snapshot_time) + "<br><br>Size: " + \
                        self.convert_bytes(snapshot_size) + "<br><br>" + "Used by: " + name + "<br>", snapshot_name, "revert" in snapshot_ops])
        return list

    def get_performance_data(self, uuid, ref, ip, host=False, period=5):

        if host:
            data_sources = self.connection.host.get_data_sources(self.session_uuid, ref)
        else:
            data_sources = self.connection.VM.get_data_sources(self.session_uuid, ref)
        if not "Value" in data_sources:
            return
        data_sources = data_sources['Value']
        ds = {}
        for data_source in data_sources:
            if data_source['enabled']:
                name = data_source['name_label']
                desc = data_source['name_description']
                if not name[:3] in ds.keys():
                    ds[name[:3]] = []
            if ds[name[:3]].count([name, desc]) == 0:
                if name not in ("memory_internal_free", "xapi_free_memory_kib", "xapi_memory_usage_kib",  "xapi_live_memory_kib") \
                        and name[:6] != "pif___":
                            ds[name[:3]].append([name, desc])
        if host:
            if os.path.exists("/var/lib/xenmagic/host_rrds.rrd"):
                os.unlink("/var/lib/xenmagic/host_rrds.rrd")
            urllib.urlretrieve("http://%s/host_rrds?session_id=%s" % (ip, self.session_uuid), "/var/lib/xenmagic/host_rrds.rrd")
            rrd = RRD("/var/lib/xenmagic/host_rrds.rrd")
        else:
            if os.path.exists("/var/lib/xenmagic/vm_rrds.rrd"):
                os.unlink("/var/lib/xenmagic/vm_rrds.rrd")
            urllib.urlretrieve("http://%s/vm_rrds?session_id=%s&uuid=%s" % (ip, self.session_uuid, uuid), "/var/lib/xenmagic/vm_rrds.rrd")
            rrd = RRD("/var/lib/xenmagic/vm_rrds.rrd")
        rrdinfo = rrd.get_data(int(period))

        # Chart
        chart = {}
        # CPU Graph
        for key in rrdinfo.keys():
            if key[:3] == "cpu":
                data = rrdinfo[key]["values"]
                for i in range(len(data)):
                    data[i][1] = data[i][1]*100
                chart[key] = data
                
        
        # Memory
        if "memory_internal_free" in rrdinfo and "memory" in rrdinfo:
            data = rrdinfo["memory"]["values"]
            data2 = rrdinfo["memory_internal_free"]["values"]
            for i in range(len(data2)):
                data[i][1] = (data[i][1] - data2[i][1]*1024)/1024/1024
            chart["mem"] = data
            chart["mem_free"] = data2

        elif "memory_total_kib" in rrdinfo and "xapi_free_memory_kib" in rrdinfo:
            data = rrdinfo["memory_total_kib"]["values"]
            data2 = rrdinfo["xapi_free_memory_kib"]["values"]
            for i in range(len(data2)):
                data[i][1] = (data[i][1] - data2[i][1]*1024)/1024/1024
            chart["mem"] = data
            chart["mem_free"] = data2
        
        else:
            chart["mem"] = "<b>No data availaible</b>"
            chart["mem_free"] = "<b>No data availaible</b>"
        
        # Network
        max_value = 0
        data = None
        for key in rrdinfo.keys():
            if key[:3] == "vif" or  key[:3] == "pif":
                data = rrdinfo[key]["values"]
                for i in range(len(data)):
                    data[i][1] = data[i][1]/1024
                    if data[i][1] > max_value:
                        max_value = data[i][1]
                chart[key] = data 
        if not data:
            chart["vif"] = "<b>No data availaible</b>"
 
        # Disk
        if not host:
            max_value = 0
            data = None
            for key in rrdinfo.keys():
                if key[:3] == "vbd":
                    data = rrdinfo[key]["values"]
                    for i in range(len(data)):
                        data[i][1] = data[i][1]/1024
                    chart[key] = data
                    if rrdinfo[key]['max_value']/1024 > max_value:
                        max_value = rrdinfo[key]['max_value']/1024

            
        if max_value == 0: max_value = 1
       
        return chart 
       
    def get_performance_data_update(self, uuid, ref, ip):
        if os.path.exists("/var/lib/xenmagic/update.rrd"):
            os.unlink("/var/lib/xenmagic/update.rrd")
        urllib.urlretrieve("http://%s/rrd_updates?session_id=%s&start=%s&cf=AVERAGE&interval=5&vm_uuid=%s" % (ip, self.session_uuid, int(time.time())-10, uuid), "/var/lib/xenmagic/update.rrd")
        rrd = XPORT("update.rrd")
        rrdinfo = rrd.get_data()
        chart = {} 
        for key in rrdinfo:
            if rrdinfo[key]['values']:
                if key[:3] == "cpu":
                   data = rrdinfo[key]["values"]
                   for i in range(len(data)):
                       data[i][1] = data[i][1]*100
                   chart[key] = data
                elif key[:3] == "vif":
                   data = rrdinfo[key]["values"]
                   for i in range(len(data)):
                        data[i][1] = data[i][1]/1024
                   chart[key] = data
                elif key[:3] == "vbd":
                   data = rrdinfo[key]["values"]
                   for i in range(len(data)):
                        data[i][1] = data[i][1]/1024
                   chart[key] = data
        if "memory_internal_free" in rrdinfo:
            data = rrdinfo["memory"]["values"]
            data2 = rrdinfo["memory_internal_free"]["values"]
            for i in range(len(data2)):
                data[i][1] = (data[i][1] - data2[i][1]*1024)/1024/1024
            chart["mem"] = data
        
        return chart

    def fill_log(self, ref, uuid):
        self.filter_uuid = uuid
        self.filter_ref = ref
        i = 0
        logs = {}
        for task_ref in filter(self.task_filter_uuid, self.tasks):
            task = self.all_tasks[task_ref]
            if "snapshot" in task:
               logs[str(task['snapshot']['created'])] = (task['snapshot']['name_label'], self.format_date(task['snapshot']['created']), "%s %s" % (task["snapshot"]["name_label"], self.all_vms[self.track_tasks[task["ref"]]]["name_label"]), self.format_date(task['snapshot']['created']), task['ref'], task, float(task['snapshot']['progress']), i%2)
            else:
               if "ref" in task:
                   logs[str(task['created'])] = (task['name_label'], self.format_date(task['created']), "%s %s" % (task["name_label"], self.all_vms[self.track_tasks[task["ref"]]]["name_label"]), self.format_date(task['created']), self.get_task_ref_by_uuid(task['uuid']), task, float(task['progress']),i%2)
               else:
                   logs[str(task['created'])] = (task['name_label'], self.format_date(task['created']), "%s %s" % (task["name_label"], task["name_description"]), self.format_date(task['created']), task_ref, task, float(task['progress']),i%2)
               i = i + 1
        for log in sorted(filter(self.log_filter_uuid, self.all_messages.values()),  key=itemgetter("timestamp"), reverse=True):
            timestamp = str(log['timestamp'])
            logs[timestamp] = (log['name'], self.format_date(timestamp), log['body'], self.format_date(timestamp), None, None, 0, i%2)
            i = i + 1
        return logs

    def add_box_log(self, title, date, description, time, id=None, task=None, progress=0, alt=0):
        date = self.format_date(date)
        vboxframe = gtk.Frame()
        vboxframe.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#d5e5f7"))
        if task:
            vboxframe.set_size_request(700,100)
        else:
            vboxframe.set_size_request(700,80)
        vboxchild = gtk.Fixed()
        vboxevent = gtk.EventBox()
        vboxevent.add(vboxchild)
        vboxframe.add(vboxevent)
        vboxchildlabel1 = gtk.Label()
        vboxchildlabel1.set_selectable(True)
        vboxchildlabel2 = gtk.Label()
        vboxchildlabel2.set_selectable(True)
        vboxchildlabel3 = gtk.Label()
        vboxchildlabel3.set_selectable(True)
        vboxchildlabel4 = gtk.Label()
        vboxchildlabel4.set_selectable(True)
        #FIXME
        #vboxchildprogressbar.set_style(1)
        vboxchildlabel2.set_label(date)
        if title in messages_header:
            vboxchildlabel1.set_label(messages_header[title])
        else:
            vboxchildlabel1.set_label(title)
        if title in messages:
            vboxchildlabel3.set_label(messages[title] % (self.wine.selected_name))
        else:
            vboxchildlabel3.set_label(description)
        vboxchildlabel1.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("blue"))
        #vboxchildlabel4.set_label(time)
        vboxchild.put(vboxchildlabel1, 25, 12)
        vboxchild.put(vboxchildlabel2, 500, 12)
        vboxchild.put(vboxchildlabel3, 25, 32)
        vboxchild.put(vboxchildlabel4, 25, 52)

        # Active task 
        if task:
            self.vboxchildcancel[id] = gtk.Button()
            self.vboxchildcancel[id].connect("clicked", self.cancel_task)
            self.vboxchildcancel[id].set_name(id)
            self.vboxchildprogressbar[id] = gtk.ProgressBar()
            self.vboxchildprogress[id] = gtk.Label()
            self.vboxchildprogress[id].set_selectable(True)
            self.vboxchildprogressbar[id].set_size_request(500,20)
            self.vboxchildprogressbar[id].set_fraction(progress)
            if ("snapshot" in task and (task["snapshot"]["status"] != "failure" and task["snapshot"]["status"] != "success")) or \
                    (task["status"] != "failure" and task["status"] != "success"):
                vboxchild.put(self.vboxchildcancel[id], 500, 32)
                self.vboxchildcancel[id].set_label("Cancel")
                self.vboxchildprogress[id].set_label("Progress: ")
                vboxchild.put(self.vboxchildprogressbar[id], 100, 72)
            elif ("snapshot" in task and task["snapshot"]["status"] == "failure") or task["status"] == "failure":
                self.vboxchildcancel[id].hide()
                self.vboxchildprogressbar[id].hide()
                self.vboxchildprogress[id].modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#FF0000'))
                if "snapshot" in task:
                    self.vboxchildprogress[id].set_label("Error: %s" % task["snapshot"]["error_info"])
                else:
                    self.vboxchildprogress[id].set_label("Error: %s" % task["error_info"])
            else:
                if ("snapshot" in task and task["snapshot"]["finished"]) or task["finished"]:
                    vboxchildlabel4.set_label("Finished: %s"  % self.format_date(str(task["finished"])))


            vboxchild.put(self.vboxchildprogress[id], 25, 72)
            if ("snapshot" in task and task["snapshot"]["status"] == "success"):
                self.vboxchildcancel[id].hide()
                self.vboxchildprogressbar[id].hide()
            if task["status"] == "success":
                self.vboxchildcancel[id].hide()
                self.vboxchildprogressbar[id].hide()

        if alt: 
            vboxevent.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#d5e5f7"))
        else:
            vboxevent.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#BAE5D3"))
        self.wine.builder.get_object("vmtablelog").add(vboxframe)
        self.wine.builder.get_object("vmtablelog").show_all()        

    def cancel_task(self, task_ref):
        res = self.connection.task.cancel(self.session_uuid, task_ref)
        if "Value" in res:
            return "OK"
        else:
            return res["ErrorDescription"][0]

    def fill_host_storage(self, ref):
        list = []
        for storage in self.all_storage.values():
            on_host = False
            for pbd in storage['PBDs']:
                if self.all_pbd[pbd]['host'] == ref:
                    on_host = True
            #if storage['type'] != "iso":
            if on_host:
                if "physical_size" in storage:
                    if int(storage['physical_size']) > 0:
                        usage = "%d%% (%s used)" % \
                                (((float(storage['physical_utilisation'])/1073741824)  / \
                                (float(storage['physical_size'])/1073741824) * 100), \
                                self.convert_bytes(storage['physical_utilisation']))
                    else:
                        usage = "0% (0B Used)"      
                    if storage['name_label'] != "XenServer Tools":
                        list.append((storage['name_label'],
                            storage['name_description'],
                            storage['type'],
                            str(storage['shared']),
                            usage,
                            self.convert_bytes(storage['physical_size']),
                            self.convert_bytes(storage['virtual_allocation'])))
        return list

    def fill_host_search(self, ref):
        parents = {}
        children = {}
        #while not self.halt_search:
        hosts = {}
        #FIXME: what happen when a pool exists?
        for host in self.all_hosts.keys():
            metrics = self.all_hosts[host]['metrics']
            memory_free = int(self.all_host_metrics[metrics]['memory_free'])
            memory_total = int(self.all_host_metrics[metrics]['memory_total'])
            if memory_total == 0:
                memory = ""
                memory_img = 0
            else:
                memory = str(((memory_total-memory_free)*100)/memory_total) + "% used of " + self.convert_bytes(memory_total)
                memory_img = int((((memory_total-memory_free)*100)/memory_total)/10)
            start_time = self.all_hosts[host]['other_config']['boot_time'][:-1]
            uptime = self.humanize_time(time.time() - int(start_time))
            parents[host] = ["images/tree_connected_16.png", self.all_hosts[host]['name_label'], self.all_hosts[host]['name_description'], "images/usagebar_5.png", "","images/usagebar_%s.png" % str(memory_img), memory, "-", "", self.all_hosts[host]['address'], uptime, host]
        return parents
        threads = {}
        for host in self.all_hosts.keys():
            threads[host] = Thread(target=self.fill_vm_search, args=(host, children, hosts, parents))
            threads[host].start()
        for host in threads:
            threads[host].join()
        print children
        """
        for i in range(0,60):
            if not self.halt_search:
                time.sleep(1)
        """
        return parents, children
    def fill_vm_search(self, host):
        rrd_updates = rrdinfo.RRDUpdates("http://%s/rrd_updates?session_id=%s&start=%d&cf=AVERAGE&interval=5&host=true" % (self.all_hosts[host]["address"], self.session_uuid, time.time()-600))
        rrd_updates.refresh()
        list = []
        list2 = []
        for uuid in rrd_updates.get_vm_list():
            for vm in self.all_vms:
                if self.all_vms[vm]["uuid"] == uuid:
                    break
            guest_metrics = self.all_vms[vm]['guest_metrics']
            ips = []
            with_tools = True
            if guest_metrics != "OpaqueRef:NULL":
                for vif in self.all_vms[vm]['VIFs']:
                    if "networks" in self.all_vm_guest_metrics[guest_metrics]:
                        if self.all_vif[vif]['device'] + "/ip" in self.all_vm_guest_metrics[guest_metrics]['networks']:
                            if self.all_vm_guest_metrics[guest_metrics]['networks'][self.all_vif[vif]['device'] + "/ip"]:
                                ips.append(self.all_vm_guest_metrics[guest_metrics]['networks'][self.all_vif[vif]['device'] + "/ip"])
            else:
                with_tools = False
            cpu = 0
            cpu_pct = 0
            vbd_write_avg = 0
            vbd_write_max = 0
            vbd_read_avg = 0
            vbd_read_max = 0
            vif_write_avg = 0
            vif_write_max = 0
            vif_read_avg = 0
            vif_read_max = 0
            memory = 0
            memory_total = 0
            for param in rrd_updates.get_vm_param_list(uuid):
                    data=[0]
                    media=0.0
                    i = 0
                    row = None
                    for row in range(rrd_updates.get_nrows()):
                           value1 = rrd_updates.get_vm_data(uuid,param,row)
                           if value1 != "NaN":
                                data.append(value1)
                                media += value1
                                i += 1
                    if i == 0: i=1
                    if row:
                        if param.count("cpu") > 0:
                            cpu = cpu + 1
                            cpu_pct = cpu_pct + int(rrd_updates.get_vm_data(uuid,param,row)*100)
                        elif param.count("vbd") > 0 and param.count("write"):
                            try:
                                vbd_write_avg += int((media/i)/1024)
                                vbd_write_max += int(max(data)/1024)
                            except:
                                vbd_write_avg += 0
                                vbd_write_max += 0
                        elif param.count("vbd") > 0 and param.count("read"):
                            try:
                                vbd_read_avg += int((media/i)/1024)
                                vbd_read_max += int(max(data)/1024)
                            except:
                                vbd_read_avg += 0
                                vbd_read_max += 0
                        elif param.count("vif") > 0 and param.count("tx"):
                            try:
                                vif_write_avg += int((media/i)/1024)
                                vif_write_max += int(max(data)/1024)
                            except:
                                vif_write_avg += 0
                                vif_write_max += 0
                        elif param.count("vif") > 0 and param.count("rx"):
                            try:
                                vif_read_avg += int((media/i)/1024)
                                vif_read_max += int(max(data)/1024)
                            except:
                                vif_read_avg += 0
                                vif_read_max += 0
                        elif param.count("memory_internal_free") > 0:
                            memory =  int(rrd_updates.get_vm_data(uuid,param,row))*1024
                            memory_total = int(self.all_vms[vm]['memory_dynamic_max'])
                        else:
                            #print str(media/i) + "/" + str(max(data))
                            #print "last: " + str(rrd_updates.get_vm_data(uuid,param,row))
                            
                            pass

                        if cpu:
                            load = str(cpu_pct/cpu)
                            load_img = str(int((cpu_pct/cpu)/10))
                        else:
                            load = "0"
                            load_img = "0"
                        if memory:
                            memory_used = str(((memory_total-memory)*100)/memory_total)
                            memory_img = str(int(((memory_total-memory)*100)/memory_total)/10)
                        else:
                            memory_used = "0"
                            memory_img = "0"
            if row:
                parent = self.all_vms[vm]['resident_on']
                if parent == "OpaqueRef:NULL": 
                    parent = self.all_vms[vm]['affinity']
                if not self.all_vms[vm]['is_control_domain']:
                    if self.all_vms[vm]['metrics'] not in  self.all_vm_metrics:
                        self.all_vm_metrics[self.all_vms[vm]['metrics']] = self.connection.VM_metrics.get_record(self.session_uuid, self.all_vms[vm]['metrics'])['Value']
                    start_time = self.all_vm_metrics[self.all_vms[vm]['metrics']]['start_time']
                    uptime = self.humanize_time(self.get_seconds_difference(start_time))
                    if parent != "OpaqueRef:NULL":
                        if with_tools:
                          if int(load_img) > 10:
                            load_img = "10"
                          elif int(load_img) < 0:
                            load_img = "0"
                          if int(memory_img) > 10:
                            memory_img = "10"
                          elif int(memory_img) < 0:
                            memory_img = "0"

                          list.append(["images/tree_running_16.png", 
                                  self.all_vms[vm]['name_label'], self.all_vms[vm]['name_description'], 
                                  "images/usagebar_%s.png" % load_img, 
                                  load + "% of " + str(cpu) + " cpus",
                                  "images/usagebar_%s.png" % abs(int(memory_img)),
                                  memory_used + "% of " + self.convert_bytes(memory_total),
                                  str(vbd_write_avg) + "/" + str(vbd_write_max) + " | " +  str(vbd_read_avg) + "/" + str(vbd_read_max),
                                  str(vif_write_avg) + "/" + str(vif_write_max) + " | " +  str(vif_read_avg) + "/" + str(vif_read_max),
                                  "\n".join(ips),
                                  uptime
                              ])
                        else:
                          list.append(["images/tree_running_16.png", 
                                  self.all_vms[vm]['name_label'], self.all_vms[vm]['name_description'], 
                                  "images/usagebar_%s.png" % load_img, 
                                  load + "% of " + str(cpu) + " cpus",
                                  "images/usagebar_0.png",
                                  "",
                                  "<span foreground='red'><b>XenServer tools</b></span>",
                                  "<span foreground='red'><b>not installed</b></span>",
                                  "-",
                                  uptime
                               ])
                    else:
                        pass
                        """
                        list.append(None,  
                          ([gtk.gdk.pixbuf_new_from_file("images/tree_running_16.png"), 
                            self.all_vms[vm]['name_label'] + "\n<i>" + self.all_vms[vm]['name_description'] + "</i>", 
                            gtk.gdk.pixbuf_new_from_file("images/usagebar_%s.png" % load_img), 
                            load + "% of " + str(cpu) + " cpus",
                            gtk.gdk.pixbuf_new_from_file("images/usagebar_0.png"),
                            "",
                            "<span foreground='red'><b>XenServer tools</b></span>",
                            "<span foreground='red'><b>not installed</b></span>",
                            "-",
                            uptime,
                            color[rcolor % 2] 
                         ]))
                        rcolor = rcolor + 1
                        """
                        #print  self.all_vms[vm]
                else:
                    list2.append(["images/usagebar_%s.png" % load_img,
                        load + "% of " + str(cpu) + " cpus",
                        str(vif_write_avg) + "/" + str(vif_write_max) + " | " +  str(vif_read_avg) + "/" + str(vif_read_max)])
        return list, list2

    def fill_local_storage(self, ref):
        list = []
        if ref in self.all_storage:
            for vdi in self.all_storage[ref]['VDIs']:
                pct = (int(self.all_vdi[vdi]['physical_utilisation'])/int(self.all_vdi[vdi]['virtual_size']))*100
                if self.all_vdi[vdi]['VBDs']:
                    vbd = self.all_vbd[self.all_vdi[vdi]['VBDs'][0]]
                    vm = self.all_vms[vbd['VM']]['name_label']
                else:
                    vm = ""
                if self.all_vdi[vdi]['is_a_snapshot']:
                    vm += " (snapshot)"
                #FIXME
                if self.all_vdi[vdi]['name_label'] != "base copy":
                    list.append([vdi, self.all_vdi[vdi]['name_label'], self.all_vdi[vdi]['name_description'], \
                            self.convert_bytes(self.all_vdi[vdi]['virtual_size']) + " (" + str(pct) + "% on disk)", vm, \
                            self.all_vdi[vdi]['is_a_snapshot']])
        return list

    def fill_vm_storage(self, ref):
        list = []
        self.filter_ref = ref
        all_vbds = filter(self.filter_vbd_ref, self.all_vbd.values())
        if ref not in self.all_vms:
            return
        for vbd_ref in self.all_vms[ref]['VBDs']:
            vbd = self.all_vbd[vbd_ref]
            if vbd['VDI'] != "OpaqueRef:NULL" and vbd['type'] != "CD":
                if vbd['mode'] == "RW":
                    ro = "False" 
                else:
                    ro = "True" 
                if vbd['VDI']:
                    self.filter_vdi = vbd['VDI']
                    vdi = self.all_vdi[self.filter_vdi_ref()]
                    vdi_name_label = vdi['name_label'] 
                    vdi_name_description =  vdi['name_description']
                    vdi_virtual_size =  vdi['virtual_size']
                    vdi_sr = vdi['SR'] 
                    sr_name = self.all_storage[vdi_sr]['name_label']
                    list.append((vdi_name_label, \
                         vdi_name_description, \
                         sr_name, \
                         vbd['userdevice'], \
                         self.convert_bytes(vdi_virtual_size), \
                         ro, \
                         "0 (Highest) ", \
                         str(vbd['currently_attached']), \
                         "/dev/" + vbd['device'], vbd['VDI'], vbd_ref, vbd['bootable'], vdi['type'], vdi['allowed_operations'].count("destroy") > 0))
        return list

    def fill_vm_storage_dvd(self, ref):
        list = []
        i = 0
        active = 0
        self.filter_ref = ref
        all_vbds = filter(self.filter_vbd_ref, self.all_vbd.values())
        vmvdi = ""
        for vbd in all_vbds:
            if vbd['type'] == "CD":
               vmvdi = vbd['VDI']
        list.append(["(empty)", "empty", True, True])
        list.append(["DVD drives", "", False, True])
        for sr in self.all_storage:
            if self.all_storage[sr]['type'] == "udev" and self.all_storage[sr]['sm_config']["type"] == "cd":
                if len(self.all_storage[sr]['VDIs']):
                    i = i + 1
                    if self.all_storage[sr]['VDIs'][0] == vmvdi:
                            active = i  
                    if self.all_storage[sr]['VDIs'][0] in self.all_vdi:
                        info = self.all_vdi[self.all_storage[sr]['VDIs'][0]]
                        list.append(["\tDVD Drive " + info['location'][-1:],  self.all_storage[sr]['VDIs'][0], True, False])
                    else:
                        list.append(["\tDVD Drive",  self.all_storage[sr]['VDIs'][0], True, False])

        for sr in self.all_storage:
            if self.all_storage[sr]['type'] == "iso":
                list.append([self.all_storage[sr]['name_label'], sr, False, True])
                i = i + 1
                isos = {}
                for vdi in self.all_storage[sr]['VDIs']:
                    isos[str(self.all_vdi[vdi]['name_label'])] = vdi
                for vdi_ref in sorted(isos):
                    vdi = isos[vdi_ref]
                    list.append(["\t" + self.all_vdi[vdi]['name_label'], vdi, True, False])
                    i = i + 1
                    if vdi == vmvdi:
                        active = i

        if active == 0:
            return (active, list)
        else:
            return (active+1, list)

    def update_tab_stg_general(self, ref):
        labels = {}
        labels['lblstgname'] = self.all_storage[ref]['name_label']
        labels['lblstgdescription'] = self.all_storage[ref]['name_description']
        labels['lblstgtags'] = ", ".join(self.all_storage[ref]['tags'])
        stg_other_config = self.all_storage[ref]['other_config']
        if "folder" in stg_other_config:
            labels['lblstgfolder'] = stg_other_config['folder']
        else:
            labels['lblstgfolder'] = ""
        labels['lblstgtype'] = self.all_storage[ref]['type'].upper()
        labels['lblstgsize'] = "%s used of %s total (%s allocated)" % \
                (self.convert_bytes(self.all_storage[ref]['physical_utilisation']),
                 self.convert_bytes(self.all_storage[ref]['physical_size']),
                 self.convert_bytes(self.all_storage[ref]['virtual_allocation'])
                )
        if "devserial" in self.all_storage[ref]['sm_config']:
            devserial =  self.all_storage[ref]['sm_config']['devserial'].split("-",2)
            labels['lblstgserial'] =  devserial[0].upper() + " ID:"
	    if len(devserial) > 1:
                labels['lblstgscsi'] = devserial[1]
	    else:
		labels['lblstgscsi'] = devserial[0]
        else:
            labels['lblstgscsi'] = ""
      
        broken = False
        # Fix using PBD and "currently_attached"
        if len(self.all_storage[ref]['PBDs']) == 0:
            broken = True
            labels['lblstgstate'] = "<span foreground='red'><b>Detached</b></span>"
            labels['lblstghostcon'] = "<span foreground='red'><b>Connection Missing</b></span>"
        else:
            broken = False
            for pbd_ref in self.all_storage[ref]['PBDs']:
                if not self.all_pbd[pbd_ref]['currently_attached']:
                    labels['lblstgstate'] = "<span foreground='red'><b>Broken</b></span>"
                    labels['lblstghostcon'] = "<span foreground='red'><b>Unplugged</b></span>"
                    broken = True
        if not broken:
            if len(self.all_storage[ref]['PBDs']) > 0:
                labels['lblstgstate'] = "<span foreground='green'><b>OK</b></span>"
                labels['lblstghostcon'] = "Connected"
            """
            elif len(self.all_storage[ref]['PBDs']) > 0:
                labels['lblstgstate'] = "<span foreground='red'><b>Dettached</b></span>"
                labels['lblstghostcon'] = "<span foreground='red'><b>Connection Missing</b></span>"
            """
        labels['lblstghost'] = self.hostname
        if len(self.all_storage[ref]['PBDs']) == 0:
            labels['lblstgmultipath'] = "No"
        else:
            pbd = self.all_pbd[self.all_storage[ref]['PBDs'][0]]
            if "multipathed" in pbd['other_config'] and  pbd['other_config']["multipathed"] == "true":
                if "SCSIid" in pbd['device_config']:
                    #{'uuid': '232b7d15-d8cb-e183-3838-dfd33f6bd597', 'SR': 'OpaqueRef:1832f6e1-73fa-b43d-fcd2-bac969abf867', 'other_config': {'mpath-3600a0b8000294d50000045784b85e36f': '[1, 1, -1, -1]', 'multipathed': 'true'}, 'host': 'OpaqueRef:5c0a69d1-7719-946b-7f3c-683a7058338d', 'currently_attached': True, 'device_config': {'SCSIid': '3600a0b8000294d50000045784b85e36f'}}
                    scsiid = pbd['device_config']["SCSIid"] 
                    paths = eval(pbd["other_config"]["mpath-" + scsiid])
                    if paths[0] == paths[1]:
                        labels['lblstgmultipath'] = "<span foreground='green'>%s of %s paths active</span>" % (paths[0], paths[1])
                    else:
                        labels['lblstgmultipath'] = "<span foreground='red'>%s of %s paths active</span>" % (paths[0], paths[1])
                else:
                    labels['lblstgmultipath'] = "Yes"
            else:
                labels['lblstgmultipath'] = "No"
        return labels

    def is_storage_broken(self, ref):
        for pbd_ref in self.all_storage[ref]['PBDs']:
            if not self.all_pbd[pbd_ref]['currently_attached']:
                return True
        return False
         
    def update_tab_tpl_general(self, ref):
        labels = {}
        labels['lbltplname'] = self.all_vms[ref]['name_label']
        labels['lbltpldescription'] = self.all_vms[ref]['name_description']
        if not self.all_vms[ref]['HVM_boot_policy']:
            labels['lbltplboot'] = "Boot order:"
            labels["lbltplparameters"] = self.all_vms[ref]['PV_args']
        else:
            labels['lbltplboot'] = "OS boot parameters:"
            labels['lbltplparameters'] = ""
            for param in list(self.all_vms[ref]['HVM_boot_params']['order']):
                    if param == 'c':
                        labels['lbltplparameters'] += "Hard Disk\n"
                    elif param == 'd':
                        labels['lbltplparameters'] += "DVD-Drive\n"
                    elif param == 'n':
                        labels['lbltplparameters'] += "Network\n"

        other_config = self.all_vms[ref]['other_config']
        if "folder" in other_config:
            labels['lbltplfolder'] = other_config['folder']
        else:
            labels['lbltplfolder'] = ""

        labels["lbltplmemory"] = self.convert_bytes(self.all_vms[ref]['memory_dynamic_max'])

        if self.all_vms[ref]['tags']:
            labels["lbltpltags"] = ", ".join(self.all_vms[ref]['tags'])
        else:
            labels["lbltpltags"] = "" 

        labels["lbltplcpu"] = self.all_vms[ref]['VCPUs_at_startup']
        if "auto_poweron" in other_config and other_config["auto_poweron"] == "true":
            labels["lbltplautoboot"] = "Yes"
        else:
            labels["lbltplautoboot"] = "No"


        priority = self.all_vms[ref]["VCPUs_params"]
        if "weight" in priority:
            #labels["lbltplpriority"] = priority['weight']
            weight = priority['weight']
            if weight == 1:
                labels["lbltplpriority"] = "Lowest"
            elif weight <= 4:
                labels["lbltplpriority"] = "Very Low"
            elif weight <= 32:
                labels["lbltplpriority"] = "Low"
            elif weight <= 129:
                labels["lbltplpriority"] = "Below Normal"
            elif weight <= 512:
                labels["lbltplpriority"] = "Normal"
            elif weight <= 2048:
                labels["lbltplpriority"] = "Above Normal"
            elif weight <= 4096:
                labels["lbltplpriority"] = "High"
            elif weight <= 16384:
                labels["lbltplpriority"] = "Very High"
            else:
                labels["lbltplpriority"] = "Highest"
        else:
            labels["lbltplpriority"] = "Normal"
       
        #FIXME 
        #labels["lblvmstartup"] =  str(self.connection.VM_metrics.get_start_time(self.session_uuid,metric)['Value'])
        metric = self.all_vms[ref]['metrics']
        if metric not in self.all_vm_metrics:
           res = self.connection.VM_metrics.get_record(self.session_uuid, ref)
           if "Value" in res:
               self.all_vm_metrics[ref] = res["Value"]
        return labels 

    def update_tab_host_general(self, ref):
        labels = {}
        software_version = self.all_hosts[ref]['software_version']
        license_params = self.all_hosts[ref]['license_params']
        labels['lblhostname'] = self.all_hosts[ref]['name_label']
        labels['lblhostdescription'] = self.all_hosts[ref]['name_description']
        labels['lblhosttags'] = ", ".join(self.all_hosts[ref]['tags'])
        host_other_config = self.all_hosts[ref]['other_config']
        if "folder" in host_other_config:
            labels['lblhostfolder'] = host_other_config['folder']
        else:
            labels['lblhostfolder'] = "" 
        # FIXME
        if "iscsi_iqn" in host_other_config:
            labels['lblhostiscsi'] = host_other_config['iscsi_iqn'] 
        else:
            labels['lblhostiscsi'] = ""
        #FIXME
        labels['lblhostpool'] = ""
        #str(self.connection.session.get_pool(
        #             self.session_uuid, self.session['Value'])['Value'])
        logging =  self.all_hosts[ref]['logging']
        if "syslog_destination" in logging:
            labels['lblhostlog'] = logging['syslog_destination']
        else:
            labels['lblhostlog'] = "Local" 

        boot_time = self.humanize_time(time.time() - int(host_other_config['boot_time'][:-1]))
        tool_boot_time = self.humanize_time(time.time() - int(host_other_config['agent_start_time'][:-1]))
        labels['lblhostuptime'] = boot_time
        labels['lblhosttooluptime'] = tool_boot_time
        labels['lblhostdns'] =  self.all_hosts[ref]['hostname']
        labels['lblhostprimary'] =  self.all_hosts[ref]['address']
        resident_vms = self.all_hosts[ref]['resident_VMs']
        host_vms_memory = ""
        for resident_vm_uuid in resident_vms:
            if self.all_vms[resident_vm_uuid]['is_control_domain']:
               host_memory =  self.all_vms[resident_vm_uuid]['memory_target']
            else:
               host_vms_memory += self.all_vms[resident_vm_uuid]['name_label'] \
                    + ": using " + \
                    self.convert_bytes(self.all_vms[resident_vm_uuid]['memory_dynamic_max']) + "<br>"
        host_metrics_uuid = self.all_hosts[ref]['metrics']
        host_metrics = self.all_host_metrics[host_metrics_uuid]
        labels['lblhostmemserver'] = "%s free of %s available (%s total)"  % \
                (self.convert_bytes(host_metrics['memory_free']), \
                self.convert_bytes(int(host_metrics['memory_total']) - int(host_memory)), \
                self.convert_bytes(host_metrics['memory_total']))
        labels['lblhostmemoryvms'] = host_vms_memory
        labels['lblhostmemory'] = self.convert_bytes(host_memory)
        labels['lblhostversiondate'] = software_version['date']
        labels['lblhostversionbuildnumber'] = software_version['build_number']
        labels['lblhostversionbuildversion'] = software_version['product_version']
        expiry = self.humanize_time(self.get_seconds_difference_reverse(license_params['expiry']))
        labels['lblhostlicexpire'] = expiry
        labels['lblhostlicserver'] = license_params['sku_marketing_name']
        labels['lblhostliccode'] = license_params['productcode']
        labels['lblhostlicserial'] = license_params['serialnumber']
        host_cpus = self.all_hosts[ref]['host_CPUs']
        cpus = ""
        for host_cpu_uuid in host_cpus:
            cpus += "Vendor: %s<br>Model: %s<br>Speed: %s<br>" % \
                (self.all_host_cpu[host_cpu_uuid]['vendor'],
                self.all_host_cpu[host_cpu_uuid]['modelname'],
                self.all_host_cpu[host_cpu_uuid]['speed'])
                 
        labels['lblhostcpus'] = cpus

        host_patchs = self.all_hosts[ref]['patches']
        patchs = ""
        for host_cpu_patch in host_patchs:
            pool_patch = self.all_host_patch[host_cpu_patch]['pool_patch']
            patchs += self.all_pool_patch[pool_patch]['name_label'] + "\n"

        labels['lblhostpatchs'] = patchs

        return labels

    def update_tab_pool_general(self, ref):
        labels = {}
        if ref not in  self.all_pools: 
            return
        labels["lblpoolname"] = self.all_pools[ref]['name_label']
        labels["lblpooldescription"] = self.all_pools[ref]['name_description']
        other_config = self.all_pools[ref]['other_config']
        if self.all_pools[ref]['tags']:
            labels["lblpooltags"] = ", ".join(self.all_pools[ref]['tags'])
        else:
            labels["lblpooltags"] = "" 
        if "folder" in other_config:
            labels["lblpoolfolder"] = other_config['folder']
        else:
            labels["lblpoolfolder"] = ""

        fullpatchs = ""
        partialpatchs = ""
        for patch in self.all_pool_patch:
            hosts = {}
            for host_patch in self.all_pool_patch[patch]["host_patches"]:
                host = self.all_host_patch[host_patch]["host"]
                hosts[host] = self.all_pool_patch[patch]["host_patches"][0]
            if hosts.keys() == self.all_hosts.keys():
                fullpatchs += self.all_pool_patch[patch]["name_label"] + "\n"
            else:
                partialpatchs += self.all_pool_patch[patch]["name_label"] + "\n"

        labels["lblpoolfullpatchs"] = fullpatchs
        labels["lblpoolpartialpatchs"] = partialpatchs
        return labels

        """
        for label in labels.keys():
            builder.get_object(label).set_label(labels[label])
        if partialpatchs == "":
            builder.get_object("label365").hide()
            builder.get_object("lblpoolpartialpatchs").hide()
        if fullpatchs == "":
            builder.get_object("label363").hide()
            builder.get_object("lblpoolfullpatchs").hide()
        """

    def update_tab_vm_general(self, ref):
        labels = {}

        metric = self.all_vms[ref]['metrics']
        metric_guest = self.all_vms[ref]['guest_metrics']
        labels["lblvmname"] = self.all_vms[ref]['name_label']
        labels["lblvmdescription"] = self.all_vms[ref]['name_description']
        labels["lblvmuuid"] = self.all_vms[ref]['uuid']
        labels["lblvmmemory"] = self.convert_bytes(self.all_vms[ref]['memory_dynamic_max'])
        if self.all_vms[ref]['tags']:
            labels["lblvmtags"] = ", ".join(self.all_vms[ref]['tags'])
        else:
            labels["lblvmtags"] = "" 
        labels["lblvmcpu"] = self.all_vms[ref]['VCPUs_at_startup']
        other_config = self.all_vms[ref]['other_config']
        if "auto_poweron" in other_config and other_config["auto_poweron"] == "true":
            labels["lblvmautoboot"] = "Yes"
        else:
            labels["lblvmautoboot"] = "No"

        if not self.all_vms[ref]['HVM_boot_policy']:
            labels['lblvmboot'] = "Boot order:"
            labels["lblvmparameters"] = self.all_vms[ref]['PV_args']
        else:
            labels['lblvmboot'] = "OS boot parameters:"
            labels['lblvmparameters'] = ""
            for param in list(self.all_vms[ref]['HVM_boot_params']['order']):
                    if param == 'c':
                        labels['lblvmparameters'] += "Hard Disk\n"
                    elif param == 'd':
                        labels['lblvmparameters'] += "DVD-Drive\n"
                    elif param == 'n':
                        labels['lblvmparameters'] += "Network\n"

        priority = self.all_vms[ref]["VCPUs_params"]
        if "weight" in priority:
            weight = int(priority['weight'])
            if weight == 1:
                labels["lblvmpriority"] = "Lowest"
            elif weight <= 4:
                labels["lblvmpriority"] = "Very Low"
            elif weight <= 32:
                labels["lblvmpriority"] = "Low"
            elif weight <= 129:
                labels["lblvmpriority"] = "Below Normal"
            elif weight <= 512:
                labels["lblvmpriority"] = "Normal"
            elif weight <= 2048:
                labels["lblvmpriority"] = "Above normal"
            elif weight <= 4096:
                labels["lblvmpriority"] = "High"
            elif weight <= 16384:
                labels["lblvmpriority"] = "Very High"
            else:
                labels["lblvmpriority"] = "Highest"
        else:
            labels["lblvmpriority"] = "Normal"
       
        #FIXME 
        #labels["lblvmstartup"] =  str(self.connection.VM_metrics.get_start_time(self.session_uuid,metric)['Value'])
        metric = self.all_vms[ref]['metrics']
        if metric not in self.all_vm_metrics:
           res = self.connection.VM_metrics.get_record(self.session_uuid, ref)
           if "Value" in res:
               self.all_vm_metrics[ref] = res["Value"]
        
        if metric in self.all_vm_metrics:
            startup = self.humanize_time(self.get_seconds_difference(self.all_vm_metrics[metric]['start_time']))
            labels["lblvmstartup"] = startup
        else:
            labels["lblvmstartup"] =  "" 
        labels['lblvmdistro'] = ""
        if metric_guest != "OpaqueRef:NULL":
            guest_metrics = self.all_vm_guest_metrics[metric_guest]
            if "PV_drivers_up_to_date" in guest_metrics and guest_metrics['PV_drivers_up_to_date']:
                state = "Optimized"
            else:
                state = "Not optimized"
            if "PV_drivers_up_to_date" in guest_metrics and "major" in guest_metrics["PV_drivers_version"]:
                state = state + " (version " + guest_metrics['PV_drivers_version']['major'] + "."\
                    + guest_metrics['PV_drivers_version']['minor'] + " build "\
                    + guest_metrics['PV_drivers_version']['build'] + ")"
            else:
                state = "<font style='color: red;'><b>Tools not installed</b></font>"
            labels["lblvmvirtstate"] = state
            if "name" in guest_metrics["os_version"]:
                labels["lblvmdistro"] = guest_metrics["os_version"]["name"]
        else:
            state = "<font style='color: red;'><b>Tools not installed</b></font>"
        labels["lblvmvirtstate"] = state
        if "folder" in other_config:
            labels["lblvmfolder"] = other_config['folder']
        else:
            labels["lblvmfolder"] = ""
        return labels
        
    def export_vm(self, host, ref, name, ref2=None, as_vm=False):
        if ref2:
            task_uuid = self.connection.task.create(self.session_uuid, "Exporting snapshot", "Exporting snapshot " + name)
        else:
            task_uuid = self.connection.task.create(self.session_uuid, "Exporting VM", "Exporting VM " + name)
        if ref2:
            self.track_tasks[task_uuid['Value']] = ref2
        else:
            self.track_tasks[task_uuid['Value']] = ref

        url = "http://%s/export?ref=%s&session_id=%s&task_id=%s" % (host,  
                               ref, self.session_uuid, task_uuid['Value'])
        if as_vm:
            self.export_snap = ref
            self.connection.VM.set_is_a_template(self.session_uuid, ref, False)
        f = urllib.urlopen(url)
        return f
    
    def get_actions(self, ref):
        return self.all_vms[ref]['allowed_operations'] 
    def get_connect_string(self, ref):
        #FIXME
        """
        vm_uuid  = self.connection.VM.get_by_uuid(self.session_uuid,uuid)
        consoles = self.connection.VM.get_consoles(self.session_uuid, vm_uuid['Value'])
        console  = self.connection.console.get_record(self.session_uuid,consoles['Value'][0])
        """
        return "CONNECT /console?ref=%s&session_id=%s HTTP/1.1\r\n\r\n" % (ref,self.session_uuid)
    def get_connect_parameters(self, ref, host):
        """
        vm_uuid  = self.connection.VM.get_by_uuid(self.session_uuid,uuid)
        consoles = self.connection.VM.get_consoles(self.session_uuid, vm_uuid['Value'])
        console  = self.connection.console.get_record(self.session_uuid,consoles['Value'][0])
        """
        return "%s %s %s" % (host, ref, self.session_uuid)
        
    def dump(self, obj):
      for attr in dir(obj):
        print "obj.%s = %s" % (attr, getattr(obj, attr))
    def humanize_time(self, secs):
        string = ""
        mins, secs = divmod(secs, 60)
        hours, mins = divmod(mins, 60)
        days, hours = divmod(hours, 24)
        if days:
            string += "%02d days " % (days)
        if hours:
            string += "%02d hours " % (hours)
        if mins:
            string += "%02d minutes " % (mins)
        if secs:
            string += "%02d seconds " % (secs)
        return string

    def convert_bytes(self, n):
        """
        http://www.5dollarwhitebox.org/drupal/node/84
        """
        n = float(n)
        K, M, G, T = 1 << 10, 1 << 20, 1 << 30, 1 << 40
        if   n >= T:
            return '%.2fT' % (float(n) / T)
        elif n >= G:
            return '%.2fG' % (float(n) / G)
        elif n >= M:
            return '%.2fM' % (float(n) / M)
        elif n >= K:
            return '%.2fK' % (float(n) / K)
        else:
            return '%d' % n

    def thread_host_search(self, ref, list):
        Thread(target=self.fill_host_search, args=(ref, list)).start()
        return True
    def search_ref(self, model, path, iter_ref, user_data):
        if self.treestore.get_value(iter_ref, 6) == user_data:
            self.found_iter = iter_ref
    def event_next(self):
        eventn = {}
        while not self.halt:
            try:
                eventn = self.connection.event.next(self.session_uuid)
                if "Value" in eventn:
                    for event in eventn["Value"]:
                           if event['class'] == "vm":
                                if event['operation'] == "add":
                                    self.all_vms[event["ref"]] =  event['snapshot']
                                    if not self.all_vms[event["ref"]]["is_a_snapshot"]:
                                        self.updates.append("update_vmtree")
                                    else:
                                        self.updates.append("update_snapshots")

                                    for track in self.track_tasks:
                                        if self.track_tasks[track] == "Import.VM":
                                            self.track_tasks[track] = event["ref"]
                                        if self.track_tasks[track] == "Backup.Server":
                                            self.track_tasks[track] = event["ref"]
                                        if self.track_tasks[track] == "Restore.Server":
                                            self.track_tasks[track] = event["ref"]
                                        if self.track_tasks[track] == "Backup.Pool":
                                            self.track_tasks[track] = event["ref"]
                                        if self.track_tasks[track] == "Restore.Pool":
                                            self.track_tasks[track] = event["ref"]
                                        if self.track_tasks[track] == "Upload.Patch":
                                            self.track_tasks[track] = event["ref"]
                                    # Perfect -> set now import_ref to event["ref"]
                                    self.import_ref = event["ref"]
                                elif event['operation'] == "del":
                                    if not self.all_vms[event["ref"]]["is_a_snapshot"]:
                                        self.updates.append("update_vmtree")
                                        del self.all_vms[event["ref"]]
                                    else:
                                        self.updates.append("update_snapshots")
                                        del self.all_vms[event["ref"]]

                                else:
                                    self.filter_uuid = event['snapshot']['uuid']
                                    if self.vm_filter_uuid():
                                        self.all_vms[self.vm_filter_uuid()] =  event['snapshot']
                                    else:
                                        if event["ref"] in self.track_tasks:
                                            self.all_vms[self.track_tasks[event["ref"]]] =  event['snapshot']

                                        else:
                                            self.all_vms[event["ref"]] =  event['snapshot']
                                    self.all_vms[event["ref"]] =  event['snapshot']
                                    self.updates.append("update_vmtree")
                           else:
                                if event['class'] == "vm_guest_metrics":
                                    self.all_vm_guest_metrics[event['ref']] = self.connection.VM_guest_metrics.get_record(self.session_uuid, event['ref'])
                                if event['class'] == "task":
                                    if event["operation"] == "del":
                                        del self.all_tasks[event["ref"]]
                                    else:
                                        self.all_tasks[event["ref"]] = event["snapshot"]
                                    if event["ref"] not in self.track_tasks:
                                        pass
                                    if event["snapshot"]["status"] == "success":
                                       self.updates.append("update_logs")
                                    if event["snapshot"]["error_info"]:
                                        if event["ref"] in self.track_tasks:
                                            if self.track_tasks[event["ref"]] in self.all_vms:
                                                self.alert = "<font color=red>%s %s %s</font>" % (event["snapshot"]["name_label"], self.all_vms[self.track_tasks[event["ref"]]]["name_label"], event["snapshot"]["error_info"])
                                            else:
                                                self.alert = "<font color=red>%s: %s</font>" % (event["snapshot"]["name_description"], event["snapshot"]["error_info"])
                                            self.updates.append("update_logs")
                                    else:
                                        if event["ref"] in self.track_tasks:
                                            if self.track_tasks[event["ref"]] in self.all_vms:
                                                if event["snapshot"]["status"] == "success":
                                                    self.alert = "%s %s completed" % (event["snapshot"]["name_label"], self.all_vms[self.track_tasks[event["ref"]]]["name_label"])
                                                else:
                                                    self.alert = "%s %s %s" % (event["snapshot"]["name_label"], self.all_vms[self.track_tasks[event["ref"]]]["name_label"], (" %.2f%%" % (float(event["snapshot"]["progress"])*100)))
                                            else:
                                                vm = self.connection.VM.get_record(self.session_uuid, self.track_tasks[event["ref"]])
                                                if "Value" in vm:
                                                    self.all_vms[self.track_tasks[event["ref"]]] = vm['Value']
                                                    self.alert = "%s %s %s" % (event["snapshot"]["name_label"], self.all_vms[self.track_tasks[event["ref"]]]["name_label"], (" %.2f%%" % (float(event["snapshot"]["progress"])*100)))
                                                else:
                                                    self.alert = "%s: %s %s" % (event["snapshot"]["name_label"], event["snapshot"]["name_description"],  (" %.2f%%" % (float(event["snapshot"]["progress"])*100)))
                                        else:
                                             #self.alert = "error en task = ", event["ref"], self.track_tasks
                                             pass  #FIXME?
                                             #self.wine.push_alert(event["snapshot"]["name_label"] + (" %.2f%%" % (float(event["snapshot"]["progress"])*100)))
                                    if event["snapshot"]["status"] == "success" and event["snapshot"]["name_label"] == "Async.VIF.create":
                                        self.updates.append("update_vm_network")
                                    if event["snapshot"]["status"] == "success" and event["snapshot"]["name_label"] == "Async.VM.revert":
                                        self.start_vm(self.track_tasks[event["ref"]])

                                    if event["snapshot"]["status"] == "success" and \
                                            (event["snapshot"]["name_label"] == "Async.VM.clone" or event["snapshot"]["name_label"] == "Async.VM.copy"):
                                        dom = xml.dom.minidom.parseString(event['snapshot']['result'])
                                        nodes = dom.getElementsByTagName("value")
                                        vm_ref = nodes[0].childNodes[0].data
                                        if event["ref"] in self.set_descriptions:
                                            self.connection.VM.set_name_description(self.session_uuid, vm_ref, self.set_descriptions[event["ref"]])
                                    if event["snapshot"]["status"] == "success" and (event["snapshot"]["name_label"] == "Async.VM.provision" or event["snapshot"]["name_label"] == "VM.provision" or \
                                            event["snapshot"]["name_label"] == "Async.VM.clone" or event["snapshot"]["name_label"] == "Async.VM.copy"):
                                        self.filter_uuid = event['snapshot']['uuid']
                                        # TODO
                                        # Detect VM with event["ref"]
                                        if event["ref"] in self.track_tasks and self.track_tasks[event["ref"]] in self.all_vms:
                                            for vbd in self.all_vms[self.track_tasks[event["ref"]]]['VBDs']:
                                                self.all_storage[vbd] = self.connection.VBD.get_record(self.session_uuid, vbd)['Value']
                                            for vif in self.all_vms[self.track_tasks[event["ref"]]]['VIFs']:
                                                self.all_vif[vif] = self.connection.VIF.get_record(self.session_uuid, vif)['Value']
                                        if self.vm_filter_uuid() != None:
                                            self.all_vms[self.vm_filter_uuid()]['allowed_operations'] = \
                                                self.connection.VM.get_allowed_operations(self.session_uuid, self.vm_filter_uuid())['Value']
                                        else:
                                            if event["ref"] in self.track_tasks:
                                                self.all_vms[self.track_tasks[event["ref"]]]['allowed_operations'] = \
                                                    self.connection.VM.get_allowed_operations(self.session_uuid, self.track_tasks[event["ref"]])['Value']
                                                if self.all_vms[self.track_tasks[event["ref"]]]['allowed_operations'].count("start"):
                                                    if self.track_tasks[event["ref"]] in self.autostart:
                                                        host_start = self.autostart[self.track_tasks[event["ref"]]]
                                                        res = self.connection.Async.VM.start_on(self.session_uuid, self.track_tasks[event["ref"]], host_start, False, False)
                                                        if "Value" in res:
                                                            self.track_tasks[res['Value']] = self.track_tasks[event["ref"]]
                                                        else:
                                                            print res
                                    if event["snapshot"]["status"] == "success" and event["snapshot"]["name_label"] == "Async.VM.snapshot": 
                                        self.filter_uuid = event['snapshot']['uuid']
                                        if self.track_tasks[event["ref"]] in self.all_vms:
                                            vm_uuid = self.track_tasks[event["ref"]]
                                            dom = xml.dom.minidom.parseString(event['snapshot']['result'])
                                            nodes = dom.getElementsByTagName("value")
                                            snapshot_ref = nodes[0].childNodes[0].data
                                            #self.all_vms[vm_uuid]['snapshots'].append(snapshot_ref)
                                            self.all_vms[snapshot_ref] = self.connection.VM.get_record(self.session_uuid, snapshot_ref)['Value']
                                            for vbd in self.all_vms[snapshot_ref]['VBDs']:
                                                #FIXME
                                                self.all_vbd[vbd] = self.connection.VBD.get_record(self.session_uuid, vbd)['Value']

                                            self.updates.append("update_vm_snapshots")
                                    if event["snapshot"]["status"] == "success" and event["snapshot"]["name_label"] == "VM.Async.snapshot": 
                                            self.updates.append("update_vm_snapshots")
                                    if event["snapshot"]["status"] == "success" and event["snapshot"]["name_label"] == "Importing VM": 
                                            if self.import_start:
                                                self.start_vm(self.track_tasks[event["ref"]])
                                            if self.import_make_into_template:
                                                self.make_into_template(self.track_tasks[event["ref"]])
                                    if event["snapshot"]["status"] == "success" and event["snapshot"]["name_label"] == "VM.destroy": 
                                            self.updates.append("update_vm_snapshots")
                                    if event["snapshot"]["status"] == "success" and event["snapshot"]["name_label"] == "VIF.destroy": 
                                            self.updates.append("update_vm_network")
                                    if event["snapshot"]["status"] == "success" and event["snapshot"]["name_label"] == "VIF.plug": 
                                            self.updates.append("update_vm_network")

                                    if event["snapshot"]["status"] == "success" and \
                                            (event["snapshot"]["name_label"] == "VBD.create" or \
                                            event["snapshot"]["name_label"] == "VBD.destroy"): 
                                            self.updates.append("update_vm_storage")

                                    if event["snapshot"]["status"] == "success" and \
                                            (event["snapshot"]["name_label"] == "VDI.create" or \
                                            event["snapshot"]["name_label"] == "VDI.destroy"): 
                                            self.updates.append("update_local_storage")

                                    if event["snapshot"]["status"] == "success" and \
                                            (event["snapshot"]["name_label"] == "network.create" or \
                                            event["snapshot"]["name_label"] == "network.destroy"): 
                                            self.updates.append("update_host_networks")

                                    if event["snapshot"]["status"] == "success" and \
                                            (event["snapshot"]["name_label"] == "Async.Bond.create" or  \
                                             event["snapshot"]["name_label"] == "Bond.create" or  \
                                             event["snapshot"]["name_label"] == "Async.Bond.destroy" or  \
                                             event["snapshot"]["name_label"] == "Bond.destroy"): 
                                            self.updates.append("update_host_nics")

                                    if event["ref"] in self.track_tasks:
                                        self.tasks[event["ref"]] = event
                                    if event["ref"] in self.vboxchildprogressbar:
                                         self.updates.append("update_logs")
                                                
                                    else:
                                       if event["ref"] in self.track_tasks:
                                            self.tasks[event["ref"]] = event
                                            self.updates.append("update_logs")
                                       else:
                                           if event["snapshot"]["name_label"] == "Exporting VM" and event["ref"] not in self.vboxchildprogressbar:
                                               self.updates.append("update_logs")
                                           else:
                                                #print event
                                               pass


                                else:
                                    #print event
                                    if event["class"] == "vdi":
                                        self.all_vdi[event["ref"]] = event["snapshot"]
                                        self.updates.append("update_local_storage")
                                        self.updates.append("update_vm_storage")

                                    elif event["class"] == "vbd":
                                        self.all_vbd[event["ref"]] = event["snapshot"]
                                        """
                                        if event["snapshot"]["allowed_operations"].count("attach") == 1:
                                            self.last_vbd = event["ref"]
                                        """  
                                    elif event["class"] == "pif":
                                       self.all_pif[event["ref"]]  = event["snapshot"]
                                       self.updates.append("update_host_nics")

                                    elif event["class"] == "bond":
                                       if event["operation"] == "del":
                                           del self.all_bond[event["ref"]]
                                       else:
                                           self.all_bond[event["ref"]]  = event["snapshot"]
                                           self.updates.append("update_host_nics")

                                    elif event["class"] == "vif":
                                        if event["operation"] == "del":
                                            del self.all_vif[event["ref"]]
                                        else:
                                            if event["operation"] == "add":
                                                print self.connection.VIF.plug(self.session_uuid, event["ref"])
                                            self.all_vif[event["ref"]]  = event["snapshot"]
                                    elif event["class"] == "sr":
                                        self.filter_uuid = event['snapshot']['uuid']
                                        self.all_storage[event["ref"]]  = event["snapshot"]
                                        self.updates.append("update_local_storage")
                                        if event["operation"] == "del":
                                            del self.all_storage[event["ref"]]
                                            self.updates.append("update_vmtree")
                                        if event["operation"] == "add":
                                            self.updates.append("update_vmtree")

                                    elif event["class"] == "pool":
                                        if event["operation"] == "del":
                                            del self.all_pools[event["ref"]]
                                        else:
                                            self.all_pools[event["ref"]]  = event["snapshot"]
                                        self.updates.append("update_vmtree")
                                        self.updates.append("update_tab_pool_general")
                                    elif event["class"] == "message":
                                       if event["operation"] == "del":
                                           del self.all_messages[event["ref"]]
                                           self.updates.append("update_alerts")
                                       elif event["operation"] == "add":
                                           self.all_messages[event["ref"]] = event["snapshot"]
                                           self.updates.append("update_alerts")
                                       else:
                                           print event
                                    elif event["class"] == "vm_guest_metrics":
                                        self.all_vm_guest_metrics[event["ref"]] = event["snapshot"] 
                                    elif event["class"] == "network":
                                        if event["operation"] == "del":
                                            del self.all_network[event["ref"]]
                                            self.updates.append("update_host_networks")
                                        else:
                                            self.all_network[event["ref"]] = event["snapshot"] 
                                            self.updates.append("update_host_networks")
                                    elif event["class"] == "vlan":
                                       if event["operation"] == "del":
                                           if event["ref"] in self.all_vlan:
                                               del self.all_vlan[event["ref"]]
                                       self.all_vlan[event["ref"]] = event["snapshot"] 

                                    elif event["class"] == "host":
                                       if event["operation"] == "del":
                                           self.updates.append("update_vmtree")
                                           del self.all_hosts[event["ref"]]

                                       elif event["operation"] == "add":
                                           self.all_hosts[event["ref"]] = event["snapshot"] 
                                           self.updates.append("show_reconnect_alert")
                                           #self.wine.show_error_dlg("Host added, please reconnect for sync all info")
                                       else:
                                           self.filter_uuid = event['snapshot']['uuid']
                                           self.all_hosts[event["ref"]] = event["snapshot"] 
                                           self.updates.append("update_vmtree")
                                    elif event["class"] == "pif_metrics":
                                        self.all_pif_metrics[event["ref"]] = event["snapshot"] 
                                    elif event["class"] == "host_metrics":
                                        self.all_host_metrics[event["ref"]] = event["snapshot"]
                                    elif event["class"] == "vbd_metrics":
                                        self.all_vbd_metrics[event["ref"]] = event["snapshot"]
                                    elif event["class"] == "vif_metrics":
                                        self.all_vif_metrics[event["ref"]] = event["snapshot"]
                                    elif event["class"] == "vm_metrics":
                                        self.all_vm_metrics[event["ref"]] = event["snapshot"]
                                    elif event["class"] == "console":
                                        self.all_console[event["ref"]] = event["snapshot"]
                                    elif event["class"] == "host_patch":
                                        if event["operation"] == "del":
                                           del self.all_host_patch[event["ref"]]
                                        else:
                                           self.all_host_patch[event["ref"]] = event["snapshot"]
                                    elif event["class"] == "pool_patch":
                                        if event["operation"] == "del":
                                           del self.all_pool_patch[event["ref"]]
                                        else:
                                           self.all_pool_patch[event["ref"]] = event["snapshot"]
                                    elif event["class"] == "pbd":
                                        self.all_pbd[event["ref"]] = event["snapshot"]
                                        if event["operation"] == "add":
                                            sr = event["snapshot"]["SR"]
                                            host = event["snapshot"]["host"]
                                            self.updates.append("update_vmtree")
                                    elif event["class"] == "host_cpu":
                                        self.all_host_cpu[event["ref"]] = event["snapshot"]
                                    else:
                                        print event["class"] + " => ",event
            except socket, msg:
              print "error socket"
              self.halt = True
             # FIXME TODO
             # Disconnect
            except:
              print "Unexpected error:", sys.exc_info()
              print traceback.print_exc()

    def update_default_sr(self, model, path, iter_ref, user_data):
        """
        user_data contains:
        [0] -> old default sr
        [1] -> new default sr
        """
        gtk.gdk.threads_enter()
        sr = self.treestore.get_value(iter_ref, 6)
        if sr == user_data[0]:
            self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file("images/storage_shaped_16.png"))
        if sr == user_data[1]:
            self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file("images/storage_default_16.png"))
            self.default_sr = sr
        if sr == user_data[0] or sr == user_data[1]:
            if len(self.all_storage[sr]['PBDs']) == 0:
                self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file("images/storage_detached_16.png"))
            broken = False
            for pbd_ref in self.all_storage[sr]['PBDs']:
                if not self.all_pbd[pbd_ref]['currently_attached']:
                    broken = True
                    self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file("images/storage_broken_16.png"))
            if not broken:
                self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file("images/storage_shaped_16.png"))
        gtk.gdk.threads_leave()

    def update_vm_status(self, model, path, iter_ref, user_data):
        if self.treestore.get_value(iter_ref, 2) == self.filter_uuid:
            vm =  self.all_vms[self.vm_filter_uuid()]
            if not self.all_vms[self.vm_filter_uuid()]["is_a_template"]:
                gtk.gdk.threads_enter()
                self.treestore.set_value(iter_ref,  1, \
                   vm['name_label'])
                if len(self.all_vms[self.vm_filter_uuid()]["current_operations"]):
                    self.treestore.set_value(iter_ref,  0, \
                       gtk.gdk.pixbuf_new_from_file("images/tree_starting_16.png"))
                else:
                    self.treestore.set_value(iter_ref,  0, \
                       gtk.gdk.pixbuf_new_from_file("images/tree_%s_16.png" % \
                       vm['power_state'].lower()))
                self.treestore.set_value(iter_ref,  4, \
                   vm['power_state']
                   )
                self.wine.selected_state = vm['power_state']
                self.wine.selected_actions = vm['allowed_operations']
                gtk.gdk.threads_leave()
            else:
                gtk.gdk.threads_enter()
                self.treestore.set_value(iter_ref,  1, \
                   vm['name_label'])
                gtk.gdk.threads_leave()
                   
            if self.wine.selected_ref == self.treestore.get_value(iter_ref, 6):
                gtk.gdk.threads_enter()
                self.wine.update_tabs()
                self.wine.builder.get_object("headimage").set_from_pixbuf(self.treestore.get_value(iter_ref, 0))
                self.wine.builder.get_object("headlabel").set_label(self.treestore.get_value(iter_ref,  1))
                gtk.gdk.threads_leave()
    def update_storage_status(self, model, path, iter_ref, user_data):
        if self.treestore.get_value(iter_ref, 2) == self.filter_uuid:
            storage = self.all_storage[self.storage_filter_uuid()]
            gtk.gdk.threads_enter()
            self.treestore.set_value(iter_ref,  1, \
               storage['name_label']
               )
            gtk.gdk.threads_leave()
            if self.wine.selected_ref == self.treestore.get_value(iter_ref, 6):
                self.wine.update_tabs()
                self.wine.builder.get_object("headimage").set_from_pixbuf(self.treestore.get_value(iter_ref, 0))
                self.wine.builder.get_object("headlabel").set_label(self.treestore.get_value(iter_ref,  1))
                gtk.gdk.threads_leave()
            sr = self.treestore.get_value(iter_ref, 6)
            if len(self.all_storage[sr]['PBDs']) == 0:
                gtk.gdk.threads_enter()
                self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file("images/storage_detached_16.png"))
                gtk.gdk.threads_leave()
            broken = False
            for pbd_ref in self.all_storage[sr]['PBDs']:
                if not self.all_pbd[pbd_ref]['currently_attached']:
                    broken = True
                    gtk.gdk.threads_enter()
                    self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file("images/storage_broken_16.png"))
                    gtk.gdk.threads_leave()
            if not broken:
                gtk.gdk.threads_enter()
                self.treestore.set_value(iter_ref,  0, gtk.gdk.pixbuf_new_from_file("images/storage_shaped_16.png"))
                gtk.gdk.threads_leave()

    def delete_storage(self, model, path, iter_ref, user_data):
        if self.treestore.get_value(iter_ref, 2) == self.filter_uuid:
            self.treestore.remove(iter_ref)

    def destroy_storage(self, ref):
        res = self.connection.SR.destroy(self.session_uuid, ref)
        if "Value" in res:
            return "OK"
        else:
            return res["ErrorDescription"][0]

    def forget_storage(self, ref):
        res = self.connection.SR.forget(self.session_uuid, ref)
        if "Value" in res:
            return "OK"
        else:
            return res["ErrorDescription"][0]
            
    def unplug_storage(self, ref):
        for pbd in self.all_storage[ref]['PBDs']:
            res = self.connection.PBD.unplug(self.session_uuid, pbd)
            if not "Value" in res:
                return res["ErrorDescription"][0]
        return "OK"

    def update_host_status(self, model, path, iter_ref, user_data):
        if self.treestore.get_value(iter_ref, 2) == self.filter_uuid:
            gtk.gdk.threads_enter()
            host = self.all_hosts[self.host_filter_uuid()]
            self.treestore.set_value(iter_ref,  1, \
               host['name_label']
               )
            self.wine.update_tabs()
            self.wine.builder.get_object("headimage").set_from_pixbuf(self.treestore.get_value(iter_ref, 0))
            self.wine.builder.get_object("headlabel").set_label(self.treestore.get_value(iter_ref,  1))
            gtk.gdk.threads_leave()

    def delete_host(self, model, path, iter_ref, user_data):
        if self.treestore.get_value(iter_ref, 2) == self.filter_uuid:
            gtk.gdk.threads_enter()
            self.treestore.remove(iter_ref)
            self.wine.update_tabs()
            gtk.gdk.threads_leave()

    def log_filter_uuid(self, item):
        return item["obj_uuid"] == self.filter_uuid   

    def task_filter_uuid(self, item_ref):
        if item_ref in self.all_tasks:
            item = self.all_tasks[item_ref]
            if item_ref in self.track_tasks:
                if self.track_tasks[item_ref] in self.all_vms:
                    return self.all_vms[self.track_tasks[item_ref]]["uuid"] == self.filter_uuid   
                    #return True
            if "ref" in item and item["ref"] in self.track_tasks and self.track_tasks[item["ref"]] in self.all_vms:
                return self.all_vms[self.track_tasks[item["ref"]]]["uuid"] == self.filter_uuid   
            else:
                if "resident_on" in item:
                    return item["resident_on"] == self.filter_ref
                if "uuid" in item:
                    self.get_task_ref_by_uuid(item["uuid"])
            return False
        
    def get_task_ref_by_uuid(self, uuid):
            for task in self.tasks.keys():
                if "uuid" in self.tasks[task]:
                    if uuid == self.tasks[task]["uuid"]:
                        return task
                else:
                    print self.tasks[task]

    def filter_vif_ref(self, item):
        return item["VM"] == self.filter_ref

    def filter_vbd_ref(self, item):
        return item["VM"] == self.filter_ref

    def filter_vbd_uuid(self, uuid):
        for vbd in self.all_vbd:    
            if self.all_vbd[vbd]["uuid"] == uuid:
                return vbd 
        return None

    def filter_vm_uuid(self, item):
        return item["uuid"] == self.filter_uuid   

    def vm_filter_uuid(self):
        for vm in self.all_vms:
           if self.all_vms[vm]["uuid"] == self.filter_uuid:
               return vm   
        return None

    def storage_filter_uuid(self):
        for stg in self.all_storage:
           if self.all_storage[stg]["uuid"] == self.filter_uuid:
               return stg   
        return None

    def host_filter_uuid(self):
        for host in self.all_hosts:
           if self.all_hosts[host]["uuid"] == self.filter_uuid:
               return host
        return None

    def filter_custom_template(self, item):
        if not item["is_a_template"]:
            return False
        if  item["name_label"][:7] == "__gui__":
            return False
        if item["last_booted_record"] != "":
            return True 
        return False
    def filter_normal_template(self, item):
        if not item["is_a_template"]:
            return False
        elif  item["name_label"][:7] == "__gui__":
            return False
        elif item["last_booted_record"] == "":
            return True 
        return False
    def filter_vdi_ref(self):
        for vdi in self.all_vdi.keys():
            if vdi == self.filter_vdi:
                return vdi
    def search_in_liststore(self, list, ref, field):
        """
        Function retrns iter of element found or None
        """
        print list.__len__()
        for i in range(0, list.__len__()):
            iter_ref = list.get_iter((i,))
            print list.get_value(iter_ref, field)
            if ref == list.get_value(iter_ref, field):
                return iter_ref 
        return None
