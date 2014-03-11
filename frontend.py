#!/usr/bin/python
import cherrypy
from cherrypy.lib.static import serve_file
from daemonize import Daemonizer
import os
from mako.template import Template
from mako.lookup import TemplateLookup
from configobj import ConfigObj
import backend
try:
    import simplejson as json
except ImportError:
    import json

import time
import xml.dom.minidom
import sys

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

import xtea


from memstorage import MemoryStorage

if not os.path.exists("/var/log/xenmagic"):
    print "You should create /var/log/xenmagic"
    os._exit(1)


if len(sys.argv) > 1 and sys.argv[1] == "-daemon":
    if not os.path.exists("/usr/share/xenmagic"):
        print "For daemon, you need copy all files to /usr/share/xenmagic/"
        os._exit(1)

    os.chdir("/usr/share/xenmagic")
    mylookup = TemplateLookup(directories=['/usr/share/xenmagic/templates'])
else:
    mylookup = TemplateLookup(directories=['templates'])
treestore = {}
# Read the configuration from oxc.conf file
if os.path.exists("/etc/xenmagic/frontend.conf"):
    config = ConfigObj("/etc/xenmagic/frontend.conf")
else:
    config = ConfigObj("frontend.conf")
# Read from configuration saved servers
if config['servers']['hosts']:
    config_hosts = config['servers']['hosts']
else:
    config_hosts = {}
treestores = {}
xc_servers = {}
tunnels = {} 

masterpasswords = {}
iv = "OXCENTER"

class frontend:
    @cherrypy.expose
    def index(self):
        global treestores
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        if sessid not in treestores or "home" not in treestores[sessid]:
            treestores[sessid] = {}
            treestores[sessid]["home"] = {
                    "image" : "images/xen.png",
                    "name" : "XenMagic",
                    "uuid" : "home",
                    "type" : "home",
                    "state" : "home",
                    "host" : None,
                    "ref" : "Home",
                    "actions" : ["addserver","connectall","disconnectall"],
                    "ip" : None,
                    "children" : []
            }
            for host in config_hosts.keys():
                treestores[sessid][host] = {
                    "image" : "images/tree_disconnected_16.png",
                    "name" : host,
                    "uuid" : None,
                    "type" : "server",
                    "state" : "Disconnected",
                    "host" : host,
                    "ref" : None,
                    "actions" : ["connect", "forgetpw", "remove"],
                    "ip" : None,
                    "children" : []
                }
                treestores[sessid]["home"]["children"].append(host)

        treestore = treestores[sessid]
        update_hosts = []
        for host in treestore:
            if treestore[host]["state"] == "Running" and treestore[host]["type"] != "vm":
                if treestore[host]["host"] not in update_hosts and treestore[host]["host"] in xc_servers[sessid]:
                    update_hosts.append(treestore[host]["host"])
        index = mylookup.get_template("index.html")
        menubar = mylookup.get_template("menubar.html").render_unicode(config = config["gui"])
        toolbar = mylookup.get_template("toolbar.html").render_unicode()
        head = mylookup.get_template("head.html").render_unicode()
        vmtree = mylookup.get_template("vmtree.html").render_unicode(treestore=treestore, config = config["gui"], filter = None, config_hosts = config_hosts)
        tabs = mylookup.get_template("tabs.html").render_unicode(tabs=["framehome"], titles=["Home"])
        framehome = mylookup.get_template("framehome.html").render_unicode()
        statusbar = mylookup.get_template("statusbar.html").render_unicode()
        contextmenu = mylookup.get_template("contextmenu.html").render_unicode()
        cherrypy.session['sourceip'] = cherrypy.request.remote.ip

        options = {"save_password" : config["gui"]["save_password"]}
        return index.render_unicode(menubar=menubar, toolbar=toolbar, head=head, vmtree=vmtree, tabs=tabs, data=framehome, statusbar=statusbar, update_hosts=update_hosts, show_toolbar = config["gui"]["show_toolbar"], options = options, masterpassword = (masterpasswords.get(sessid) != None), contextmenu = contextmenu)

    @cherrypy.expose
    def vmtree(self, filter = None):
        global treestores, xc_servers
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        treestore = treestores[sessid]
        if sessid in xc_servers:
            for hostname in xc_servers[sessid]:
                if hostname in xc_servers[sessid]:
                    treestore = treestores[sessid]
                    res = xc_servers[sessid][hostname].fill_tree_with_vms(treestore, False)
                    if res != "OK":
                        return "<script>alert('"  + res + "');</script>"

        return mylookup.get_template("vmtree.html").render_unicode(treestore=treestore, config = config["gui"], filter = filter, config_hosts = config_hosts)

    @cherrypy.expose
    def tabs(self, type, state):
        showframes = {
            "pool" : ["framepoolgeneral", "framesearch", "framemaps", "framelogs"],
            "home" : ["framehome"],
            "vm"   : ["framevmgeneral", "framevmstorage", "framevmnetwork", "framesnapshots","frameperformance", "framelogs"],
            "host" : ["framesearch","framehostgeneral", "framehostnetwork", "framehoststorage", "frameconsole", "framehostnics", "frameperformance", "framemaps", "framelogs"], 
            "template" : ["frametplgeneral","framevmnetwork","framelogs"],
            "custom_template" : ["frametplgeneral","framevmnetwork", "framevmstorage", "framelogs"],
            "storage" :  ["framestggeneral","framestgdisks", "framelogs"],
        }
        tabstitle = {
            "pool" : ["General", "Search", "Maps", "Logs"],
            "home" : ["Home"],
            "vm"   : ["General", "Storage", "Network", "Snapshots","Performance", "Logs"],
            "host" : ["Search", "General", "Network", "Storage", "Console", "Nics", "Performance", "Maps", "Logs"], 
            "template" : ["General", "Network", "Logs"],
            "custom_template" : ["General","Network", "Storage", "Logs"],
            "storage" :  ["General","Storage", "Logs"],
        }
        if type == "vm" and state == "Running":
            showframes[type].insert(3, "frameconsole")
            tabstitle[type].insert(3, "Console")
        if type in showframes:
            return mylookup.get_template("tabs.html").render_unicode(tabs=showframes[type], titles=tabstitle[type])

    @cherrypy.expose
    def about(self):
        return mylookup.get_template("about.html").render_unicode()
    @cherrypy.expose
    def checkforupdates(self):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        pool = []
        hotfix = []
        # Get pool and patch info
        for server in  xc_servers[sessid].values():
            for host in server.all_hosts:
                pool.append("pool_" + server.all_hosts[host]["software_version"]["product_version"] + "=1")
                for patch in server.all_hosts[host]["patches"]:
                    host_patch = server.all_host_patch[patch]
                    if  host_patch["applied"]:
                        hotfix.append("hotfix_" + server.all_pool_patch[host_patch["pool_patch"]]["uuid"] + "=1")
                    else:
                        hotfix.append("hotfix_" + server.all_pool_patch[host_patch["pool_patch"]]["uuid"] + "=0")

        url = "http://updates.xensource.com/XenServer/5.5.2/XenCenter?%s;%s" % (";".join(pool), ";".join(hotfix))
        return "<script>window.open('" + url  + "'); parent.hidePopWin(false);</script>"

    @cherrypy.expose
    def options(self):
        options = {"save_password" : config["gui"]["save_password"], "master_password" : config["gui"]["master_password"]}
        return mylookup.get_template("options.html").render_unicode(options=options)

    @cherrypy.expose
    def addserver(self, host="", username="", password="", ssl="true"):
        sessid = cherrypy.session.id
        return mylookup.get_template("addserver.html").render_unicode(host=host, username=username, password=password, masterpassword = (masterpasswords.get(sessid) != None), ssl = (ssl == "true"))

    @cherrypy.expose
    def changepassword(self, hostname):
        return mylookup.get_template("changepassword.html").render_unicode(server=hostname)

    @cherrypy.expose
    def masterpassword(self):
        return mylookup.get_template("masterpassword.html").render_unicode()


    @cherrypy.expose
    def newstorage(self, host, ref=None):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        name = "" 
        stgtype = None
        if ref:
            name = xc_servers[sessid][host].all_storage[ref]['name_label']
            desc = xc_servers[sessid][host].all_storage[ref]['name_description']
            stgtype = xc_servers[sessid][host].all_storage[ref]['type']
            if stgtype == "iso":
                if name.lower().count("nfs") or desc.lower().count("nfs"):
                    stgtype = "radionewstgnfsiso"
                else:
                    stgtype = "radionewstgcifs"
            elif stgtype == "lvmoiscsi":
                stgtype = "radionewstgiscsi"
            elif stgtype == "nfs":
                stgtype = "radionewstgnfsvhd"
            else:
                stgtype = ""
        return mylookup.get_template("newstorage.html").render_unicode(name = name, stgtype = stgtype)

    @cherrypy.expose
    def scan_nfs_vhd(self, host, ref, share, options):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        server, path = share.split(":", 2)
        listnfs, result, error = xc_servers[sessid][host].scan_nfs_vhd(ref, server, path, options)
        return json.dumps([listnfs, result, error])

    @cherrypy.expose
    def create_nfs_vhd(self, host, ref, name, share, options):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        server, path = share.split(":", 2)
        error = xc_servers[sessid][host].create_nfs_vhd(ref, name, server, path, options)
        if error:
            return error
        else:
            return "OK"

    @cherrypy.expose
    def reattach_nfs_vhd(self, host, ref, name, share, options, uuid):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        server, path = share.split(":", 2)
        error = xc_servers[sessid][host].reattach_nfs_vhd(ref, name, server, path, options, uuid)
        if error:
            return error
        else:
            return "OK"
    
    @cherrypy.expose
    def create_cifs_iso(self, host, ref, name, sharename, options, username, password):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].create_cifs_iso(ref, name, \
                                        sharename, options, username,password) 
        if res == 0:
            return "OK"
        else:
            return res

    @cherrypy.expose
    def reattach_cifs_iso(self, host, ref, name, sharename, options, username, password):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].reattach_cifs_iso(ref, name, \
                                        sharename, options, username,password) 
        if res == 0:
            return "OK"
        else:
            return res


    @cherrypy.expose
    def create_nfs_iso(self, host, ref, name, sharename, options):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].create_nfs_iso(ref, name, \
                                        sharename, options) 
        if res == 0:
            return "OK"
        else:
            return res

    @cherrypy.expose
    def reattach_nfs_iso(self, host, ref, name, sharename, options):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].reattach_nfs_iso(ref, name, \
                                        sharename, options) 
        if res == 0:
            return "OK"
        else:
            return res

    @cherrypy.expose
    def fill_hw_hba(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].fill_hw_hba(ref)
        if res == "ERROR":
            return res
        else:
            return mylookup.get_template("hbadisks.html").render_unicode(listhba = res)

    @cherrypy.expose
    def format_hardware_hba(self, host, ref, uuid, name, path):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return xc_servers[sessid][host].format_hardware_hba(ref, uuid, name, path)

    @cherrypy.expose
    def reattach_hardware_hba(self, host, ref, uuid, name, path):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return xc_servers[sessid][host].reattach_hardware_hba(ref, uuid, name, path)

    @cherrypy.expose
    def reattach_and_introduce_hardware_hba(self, host, ref, uuid, name, path):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return xc_servers[sessid][host].reattach_and_introduce_hardware_hba(ref, uuid, name, path)
            
    @cherrypy.expose
    def check_hardware_hba(self, host, ref, uuid, text):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return json.dumps(xc_servers[sessid][host].check_hardware_hba(ref, uuid, text))


    @cherrypy.expose
    def fill_iscsi_target_iqn(self, host, ref, target, iscsiport, user, password):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return json.dumps(xc_servers[sessid][host].fill_iscsi_target_iqn(ref, target, iscsiport, user, password))

    @cherrypy.expose
    def fill_iscsi_target_lun(self, host, ref, target, iscsiport, user, password, targetiqn):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return json.dumps(xc_servers[sessid][host].fill_iscsi_target_lun(ref, target, targetiqn, iscsiport, user, password))

    @cherrypy.expose
    def check_iscsi(self, host, ref, name, target, iscsiport, user, password, targetiqn, targetlun):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return json.dumps(xc_servers[sessid][host].check_iscsi(ref, name, target, iscsiport, targetlun, targetiqn, user, password))

    @cherrypy.expose
    def create_iscsi(self, host, ref, name, target, iscsiport, user, password, targetiqn, targetlun):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return json.dumps(xc_servers[sessid][host].create_iscsi(ref, name, target, iscsiport, targetlun, targetiqn, user, password))
        
    @cherrypy.expose
    def reattach_iscsi(self, host, ref, name, target, iscsiport, user, password, targetiqn, targetlun, reattach_ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return json.dumps(xc_servers[sessid][host].reattach_iscsi(ref, name, target, iscsiport, targetlun, targetiqn, user, password, reattach_ref))
    @cherrypy.expose
    def importvm(self, host):
        global xc_servers, treestores
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        networks, networkcolumn = xc_servers[sessid][host].fill_list_networks()
        listhosts, selhost = xc_servers[sessid][host].fill_listnewvmhosts()

        return mylookup.get_template("importvm.html").render_unicode( hosts=listhosts, selhost = selhost, vifs = networks,  networkcolumn=networkcolumn, host = host)

    @cherrypy.expose
    def pre_import_vm(self, host, ref, stg):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        imports = xc_servers[sessid][host].import_vm(host, stg)
        MemoryStorage.importhost = imports[0]
        MemoryStorage.importpath = imports[1]
        cherrypy._cpcgifs.FieldStorage = MemoryStorage
        
        
    @cherrypy.expose
    def do_import_vm(self, host, filechooserimportvm, stg, disks, vifs):
        cherrypy.response.timeout = 3600
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        cherrypy.response.stream = True
        #xc_servers[sessid][host].import_vm(stg, filechooserimportvm)

    @cherrypy.expose
    def newvm(self, host, tpl=""):
        global xc_servers, treestores
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        templates = xc_servers[sessid][host].fill_list_templates()
        listisoimages = xc_servers[sessid][host].fill_list_isoimages()
        listphydvd = xc_servers[sessid][host].fill_list_phydvd()
        networks, networkcolumn = xc_servers[sessid][host].fill_list_networks()
        listhosts, selhost = xc_servers[sessid][host].fill_listnewvmhosts()
        return mylookup.get_template("newvm.html").render_unicode(templates=templates, hosts=listhosts, selhost = selhost, vifs = networks, dvd=listphydvd, isos=listisoimages, networkcolumn=networkcolumn, host = host, tpl = tpl)

    @cherrypy.expose
    def newvmstorage(self, host, vm, host_ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        default_sr =  xc_servers[sessid][host].default_sr
        listnewvmstorage  =  xc_servers[sessid][host].fill_listnewvmstorage(vm, host_ref, default_sr)
        return mylookup.get_template("newvmstorage.html").render_unicode(storages = listnewvmstorage)
        
    @cherrypy.expose
    def importvmstorage(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        default_sr =  xc_servers[sessid][host].default_sr
        listhoststorage = xc_servers[sessid][host].fill_importstg(ref) 
        return mylookup.get_template("importvmstorage.html").render_unicode(storages = listhoststorage, default_sr = default_sr)

    @cherrypy.expose
    def add_disk_to_vm(self, host, vm, name, desc, size, ref, vmuuid):
        virtual_size = int(float(size)*1024*1024*1024)
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].add_disk_to_vm(
           name, desc, ref, virtual_size, vmuuid, vm)
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return res

    @cherrypy.expose
    def add_disk_to_stg(self, host, name, desc, size, ref):
        virtual_size = int(float(size)*1024*1024*1024)
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].add_disk_to_stg(
           name, desc, ref, virtual_size)
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return res
        
    @cherrypy.expose
    def attach_disk_to_vm(self, host, vm, disk, ro):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].attach_disk_to_stg(vm, disk, ro) 
        if res == "OK": 
            return "OK"
        else:
            return res 

    @cherrypy.expose
    def vm_storagedetach(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].vm_storagedetach(ref) 
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return res

    @cherrypy.expose
    def vm_storageplug(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].vm_storageplug(ref) 
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return res

    @cherrypy.expose
    def vm_storageunplug(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].vm_storageunplug(ref) 
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return res

    @cherrypy.expose
    def delete_vdi(self, host, ref, vm):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].delete_vdi(ref, vm) 
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return res

    @cherrypy.expose
    def delete_snapshot(self, host, ref, vm):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].delete_snapshot(ref, vm) 
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return res

    @cherrypy.expose
    def vm_remove_interface(self, host, ref, vm):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].vm_remove_interface(vm, ref) 
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return res

    @cherrypy.expose
    def vm_add_interface(self, host, ref, networkref, mac, limit):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        res = xc_servers[sessid][host].vm_add_interface(ref, networkref, mac, limit) 
        return res

    @cherrypy.expose
    def vm_edit_interface(self, host, ref, networkref, mac, limit, vm):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        # modify is a flag variable
        vif = xc_servers[sessid][host].all_vif[ref]
        network_vif = xc_servers[sessid][host].all_vif[ref]['network']
        modify = False
        if "kbps" in vif['qos_algorithm_params']:
            if str(limit) != str(vif['qos_algorithm_params']["kbps"]):
                modify = True
        else:
                modify = True
        if "MAC_autogenerated" in vif and vif['MAC_autogenerated']:
            if mac:
                modify = True
                self.xc_servers[self.selected_host].vm_add_interface(self.selected_ref, network_ref, mac, limit)
        else:
            if mac == "":
                modify = True

            if vif['MAC'] != mac:
                modify = True
        if network_vif != networkref:
           modify = True

        if modify:
            res = xc_servers[sessid][host].vm_remove_interface(vm, ref)
            if res != "OK": 
                return res
            res = xc_servers[sessid][host].vm_add_interface(vm, networkref, mac, limit)
            return res
    @cherrypy.expose
    def take_snapshot(self, host, ref, name):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].take_snapshot(ref, name)
        return res

    @cherrypy.expose
    def revert_to_snapshot(self, host, ref, snapref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].revert_to_snapshot(ref, snapref)
        return res

    @cherrypy.expose
    def create_template_from_snap(self, host, ref, name):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].create_template_from_snap(ref, name)
        return res


    @cherrypy.expose
    def connect_server(self, hostname, username, password, ssl, decrypt="false"):
        global xc_servers, treestores
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        treestore = treestores[sessid]
        if sessid not in xc_servers:
            xc_servers[sessid] = {}
        if decrypt == "true":
            password = xtea.crypt("X" * (16-len(masterpasswords[sessid])) + masterpasswords[sessid], \
                                           password.decode("hex"), iv)

        xc_servers[sessid][hostname] = backend.backend(hostname, username, password,  ssl)
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        if xc_servers[sessid][hostname].is_connected:
           xc_servers[sessid][hostname].fill_tree_with_vms(treestore)
           xc_servers[sessid][hostname].thread_event_next()
           if hostname in  treestores[sessid]["home"]["children"]:
               treestores[sessid]["home"]["children"].remove(hostname) 
           if hostname in treestores[sessid]:
               del treestores[sessid][hostname] 

           if masterpasswords.get(sessid):
               z = xtea.crypt("X" * (16-len(masterpasswords.get(sessid))) + masterpasswords.get(sessid), password, iv)
               config_hosts[hostname] = [username, z.encode("hex"), ssl]
           else:
               config_hosts[hostname] = [username, "", ssl]
           config['servers']['hosts']  = config_hosts
           config.write()
           return "OK"
        else:
           if xc_servers[sessid][hostname].error_connecting:
               return xc_servers[sessid][hostname].error_connecting
           else:
               return "Error connecting to server" 


    @cherrypy.expose
    def get_update(self, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        if ref in xc_servers[sessid]:
            updates = xc_servers[sessid][ref].updates
            alert = xc_servers[sessid][ref].alert
            """
            while not updates and not alert:
                time.sleep(1)
                updates = xc_servers[sessid][ref].updates
                alert = xc_servers[sessid][ref].alert
            """
            xc_servers[sessid][ref].updates = []
            xc_servers[sessid][ref].alert = ""
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            return json.dumps([updates, alert])
        else:
            return json.dumps([[], None])

    @cherrypy.expose
    def do_action(self, action, ref, host, **kwargs):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        if host in xc_servers[sessid]:
            if hasattr(xc_servers[sessid][host], action):
                if not kwargs:
                    getattr(xc_servers[sessid][host], action)(ref)
                else:
                    getattr(xc_servers[sessid][host], action)(ref, **kwargs)
                return "OK"
            else:
                return "Function doesn't exist"

        else:
            return "Server doesn't exist"

    @cherrypy.expose
    def do_action_newvm(self, server, **kwargs):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return xc_servers[sessid][server].create_newvm(**kwargs)

    @cherrypy.expose
    def do_action_no_ref(self, action, host, **kwargs):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        if host in xc_servers[sessid]:
            if hasattr(xc_servers[sessid][host], action):
                getattr(xc_servers[sessid][host], action)(**kwargs)
                return "OK"
            else:
                return "Function doesn't exist"

        else:
            return "Server doesn't exist"

    @cherrypy.expose
    def get_alerts_count(self):
        global xc_servers
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        alerts = 0
        if sessid in xc_servers:
            for host in xc_servers[sessid]:
                alerts += len(xc_servers[sessid][host].fill_alerts())
            return str(alerts/2)
        else:
            return "0" 

    @cherrypy.expose
    def enter_maintancemode(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return xc_servers[sessid][host].enter_maintancemode(ref)

    @cherrypy.expose
    def set_license_host(self, host, ref, licensehost, licenseport, edition):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return xc_servers[sessid][host].set_license_host(ref, licensehost, licenseport, edition)


    #################### TEMPLATING ################################################

    @cherrypy.expose
    def framehome(self, hostname, ref, ip="", host="", type="", uuid="", name=""):
        return mylookup.get_template("framehome.html").render_unicode()
    
    @cherrypy.expose
    def frameperformance2(self, hostname, ref, ip="", host="", type="", uuid="", name="", interval=5):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        data = xc_servers[sessid][host].get_performance_data(uuid, ref, ip, type=="host", interval)
	if not data:
            data = {"mem": {}}
        return mylookup.get_template("frameperformance2.html").render_unicode(data = data)

    @cherrypy.expose
    def get_performance_data_update(self, host, uuid, ref, ip):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        data = xc_servers[sessid][host].get_performance_data_update(uuid, ref, ip)
        return json.dumps(data)
        
    @cherrypy.expose
    def frameperformance(self, hostname, ref, ip="", host="", type="", uuid="", name=""):
        return mylookup.get_template("frameperformance.html").render_unicode(hostname = hostname, ref = ref, ip = ip, host = host, type = type, uuid = uuid, name = name)

    @cherrypy.expose
    def framemaps(self, hostname, ref, ip="", host="", type="", uuid="", name=""):
        checks = {}
        for option in config["maps"]:
            checks[option] = ""
            if str(config["maps"][option]) == "True":
                checks[option] = "checked"
        return mylookup.get_template("framemaps.html").render_unicode(host = host, ref = ref, checks = checks)
   
    @cherrypy.expose
    def generatemapimage(self, host, ref, v=None):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        dotcode = """
        digraph G {
                  overlap=false;
                  bgcolor=white;
                  node [shape=polygon, sides=6, fontname="Verdana", fontsize="8"];
                  edge [color=deepskyblue3, fontname="Verdana", fontsize="5"];
        """

        show_halted_vms = config["maps"]["check_show_halted_vms"] == "True" 
        if config["maps"]["check_show_network"] == "True":
            relation = xc_servers[sessid][host].get_network_relation(ref, show_halted_vms)
            for network in relation:
                uuid, name = network.split("_", 1)
                safename = name.replace("&","&amp;").replace("<", "&lt;").replace("\"", "&quot;")
                if config["maps"]["check_unused_network"] == "True" or relation[network]:
                    dotcode += '"%s"[shape=plaintext, label=<<table border="0" cellpadding="0" cellspacing="0"><tr><td><img src="images_map/network.png"/></td></tr><tr><td> </td></tr><tr><td>%s</td></tr></table>> tooltip="%s"];' % (uuid, safename, name)
                    dotcode += "\n"
                for vm in relation[network]:
                    uuid2, name2 = vm.split("_", 1)
                    dotcode += '"%s"[shape=plaintext, label=<<table border="0" cellpadding="0" cellspacing="0"><tr><td><img src="images_map/server.png"/></td></tr><tr><td> </td></tr><tr><td>%s</td></tr></table>>URL="%s" tooltip="%s"];' % (uuid2, name2, uuid2, name2)
                    dotcode += "\n"
                    dotcode += '"%s" -> "%s"' % (uuid, uuid2)
                    dotcode += "\n"

        if config["maps"]["check_show_storage"] == "True":
            dotcode += 'edge [color=forestgreen, fontname="Verdana", fontsize="5"];'
            relation = xc_servers[sessid][host].get_storage_relation(ref, show_halted_vms)
            for storage in relation:
                uuid, name = storage.split("_", 1)
                safename = name.replace("&","&amp;").replace("<", "&lt;").replace("\"", "&quot;")
                if config["maps"]["check_unused_storage"] == "True" or relation[storage]:
                    dotcode += '"%s"[shape=plaintext, label=<<table border="0" cellpadding="0" cellspacing="0"><tr><td><img src="images_map/storage.png"/></td></tr><tr><td> </td></tr><tr><td>%s</td></tr></table>>URL="%s" tooltip="%s"];' % (uuid, safename, uuid, name)
                    dotcode += "\n"
                for vm in relation[storage]:
                    uuid2, name2 = vm.split("_", 1)
                    safename2 = name2.replace("&","&amp;").replace("<", "&lt;").replace("\"", "&quot;")
                    dotcode += '"%s"[shape=plaintext, label=<<table border="0" cellpadding="0" cellspacing="0"><tr><td><img src="images_map/server.png"/></td></tr><tr><td> </td></tr><tr><td>%s</td></tr></table>>URL="%s" tooltip="%s"];' % (uuid2, safename2, uuid2, name2)
                    dotcode += "\n"
                    dotcode += '"%s" -> "%s"' % (uuid2, uuid)
                    dotcode += "\n"


        dotcode += "}"
        import subprocess
        if sys.platform != "win32":
            p = subprocess.Popen('/usr/bin/dot -Tpng', shell=True,\
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        else:
            p = subprocess.Popen('dot.exe -Tpng', shell=True,\
            stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        (stdout,stderr) = p.communicate(dotcode.encode('utf-8'))
        cherrypy.response.headers['Content-Type'] = 'image/png'
        return stdout
 
    @cherrypy.expose
    def frameconsole(self, hostname, ref, ip="", host="", type="", uuid="", name=""):
        global tunnels
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        from tunnel import Tunnel
        from threading import Thread
        from time import sleep
        if type == "host":
            if ref in  xc_servers[sessid][host].host_vm:
                ref = xc_servers[sessid][host].host_vm[ref][0]
            elif uuid in xc_servers[sessid][host].host_vm:
                ref = xc_servers[sessid][host].host_vm[uuid][0]
        else:
            ref = ref

        console_ref = xc_servers[sessid][host].all_vms[ref]["consoles"][0]
        location = xc_servers[sessid][host].all_console[console_ref]["location"]
        if sessid in tunnels:
            for tunnel in tunnels[sessid]:
                tunnel.close()
            try:
                websocket.halt = True
            except:
                pass
            tunnel.close()
        tunnel = Tunnel(xc_servers[sessid][host].session_uuid, location)
        port = tunnel.get_free_port()
        Thread(target=tunnel.listen, args=(port,)).start()
        if sessid not in tunnels:
            tunnels[sessid] = []
        tunnels[sessid].append(tunnel) 
        sleep(1)
        print "Listening on %s.." % port
        return mylookup.get_template("frameconsole.html").render_unicode(hostname = hostname, ref = ref, ip = ip, host = host, type = type, uuid = uuid, name = name)

    @cherrypy.expose
    def frameconsole2(self, hostname, ref, ip="", host="", type="", uuid="", name="", java="0"):
        global tunnels
        sessid = cherrypy.session.id
        tunnels[sessid][len(tunnels[sessid])-1].java = True 
        port =  tunnels[sessid][len(tunnels[sessid])-1].port
        if str(java) == "0":
            import websocket, wsproxy
            from threading import Thread
            from tunnel import Tunnel
            if type == "host":
                ref = xc_servers[sessid][host].host_vm[ref][0]
            else:
                ref = ref

            console_ref = xc_servers[sessid][host].all_vms[ref]["consoles"][0]
            location = xc_servers[sessid][host].all_console[console_ref]["location"]

            tunnel = Tunnel(xc_servers[sessid][host].session_uuid, location)
            port = tunnel.get_free_port()
            Thread(target=tunnel.listen, args=(port,)).start()
            if sessid not in tunnels:
                tunnels[sessid] = []
            tunnels[sessid].append(tunnel) 
            wsproxy.target_host = "127.0.0.1"
            wsproxy.target_port = port
            websocket.settings['listen_host'] = "0.0.0.0" 
            websocket.settings['listen_port'] =  8091
            websocket.settings['handler'] = wsproxy.proxy_handler
            websocket.settings['cert'] =  ""
            websocket.settings['ssl_only'] = False 
            websocket.settings['daemon'] = False 
            port = websocket.settings['listen_port']
            tunnels[sessid][len(tunnels[sessid])-1].java = False
            port = 8091
            Thread(target=websocket.start_server, args=()).start()
            ip = cherrypy.request.headers["Host"].split(":")[0]

        return mylookup.get_template("frameconsole2.html").render_unicode(java = java, ip = ip, port = port)

    @cherrypy.expose
    def framevmgeneral(self, hostname, ref, ip="", host="", type="", uuid="", name=""):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        labels = xc_servers[sessid][hostname].update_tab_vm_general(ref)
        return mylookup.get_template("framevmgeneral.html").render_unicode(labels=labels)
    @cherrypy.expose
    def framehostgeneral(self, hostname, ref, ip="", host="", type="", uuid="", name=""):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        labels = xc_servers[sessid][hostname].update_tab_host_general(ref)
        return mylookup.get_template("framehostgeneral.html").render_unicode(labels=labels)
    @cherrypy.expose
    def framestggeneral(self, hostname, ref, ip="", host="", type="", uuid="", name=""):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        labels = xc_servers[sessid][hostname].update_tab_stg_general(ref)
        return mylookup.get_template("framestggeneral.html").render_unicode(labels=labels)
    @cherrypy.expose
    def framepoolgeneral(self, hostname, ref, ip="", host="", type="", uuid="", name=""):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        labels = xc_servers[sessid][hostname].update_tab_pool_general(ref)
        return mylookup.get_template("framepoolgeneral.html").render_unicode(labels=labels)
    @cherrypy.expose
    def frametplgeneral(self, hostname, ref, ip="", host="", type="", uuid="", name=""):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        labels = xc_servers[sessid][hostname].update_tab_tpl_general(ref)
        return mylookup.get_template("frametplgeneral.html").render_unicode(labels=labels)
    @cherrypy.expose
    def framehostnetwork(self, hostname, ref, ip="", host="", type="", uuid="", name=""):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listhostnetwork = xc_servers[sessid][hostname].fill_host_network(ref) 
        return mylookup.get_template("framehostnetwork.html").render_unicode(networks=listhostnetwork)
    @cherrypy.expose
    def framehoststorage(self, hostname, ref, ip="", host="", type="", uuid="", name=""):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listhoststorage = xc_servers[sessid][hostname].fill_host_storage(ref) 
        return mylookup.get_template("framehoststorage.html").render_unicode(storages = listhoststorage)

    @cherrypy.expose
    def framehostnics(self, hostname, ref, ip="", host="", type="", uuid="", name=""):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listhostnics = xc_servers[sessid][hostname].fill_host_nics(ref) 
        return mylookup.get_template("framehostnics.html").render_unicode(nics=listhostnics)
    @cherrypy.expose
    def framevmstorage(self, hostname, ref, ip="", host="", type="", uuid="", name=""):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listvmstorage = xc_servers[sessid][hostname].fill_vm_storage(ref) 
        listvmstoragedvd = xc_servers[sessid][hostname].fill_vm_storage_dvd(ref) 
        return mylookup.get_template("framevmstorage.html").render_unicode(storages = listvmstorage, dvds = listvmstoragedvd[1], active=listvmstoragedvd[0])

    @cherrypy.expose
    def framevmnetwork(self, hostname, ref, ip="", host="", type="", uuid="", name=""):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listvmnetwork = xc_servers[sessid][hostname].fill_vm_network(ref) 
        return mylookup.get_template("framevmnetwork.html").render_unicode(networks = listvmnetwork)

    @cherrypy.expose
    def framesnapshots(self, hostname, ref, ip="", host="", type="", uuid="", name=""):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listsnaps = xc_servers[sessid][hostname].fill_vm_snapshots(ref, name) 
        return mylookup.get_template("framesnapshots.html").render_unicode(snaps = listsnaps)


    @cherrypy.expose
    def framestgdisks(self, hostname, ref, ip="", host="", type="", uuid="", name=""):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        liststgdisks = xc_servers[sessid][hostname].fill_local_storage(ref) 
        return mylookup.get_template("framestgdisks.html").render_unicode(storages = liststgdisks)

    @cherrypy.expose
    def framelogs(self, hostname, ref, ip="", host="", type="", uuid="", name=""):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listlogs = xc_servers[sessid][hostname].fill_log(ref, uuid)
        keys = listlogs.keys()
        keys.sort(reverse=True)
        from messages import messages, messages_header
        return mylookup.get_template("framelogs.html").render_unicode(logs=map(listlogs.get, keys), name = name, messages = messages, messages_header = messages_header)

    @cherrypy.expose
    def framesearch(self, hostname, ref, ip="", host="", type="", uuid="", name=""):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        """
        parents_listsearch, children_listsearch = xc_servers[sessid][hostname].fill_host_search(ref) 
        return mylookup.get_template("framesearch.html").render_unicode(parents = parents_listsearch, children = children_listsearch)
        """
        parents_listsearch = xc_servers[sessid][hostname].fill_host_search(ref) 
        return mylookup.get_template("framesearch.html").render_unicode(parents = parents_listsearch)
        return "Implementing.."
        return mylookup.get_template("loading.html").render_unicode()

    @cherrypy.expose
    def wherecanmigrate(self, host, ref): 
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        hosts = []
        for h in xc_servers[sessid][host].all_hosts:
            host_name = xc_servers[sessid][host].all_hosts[h]['name_label']
            resident_on = xc_servers[sessid][host].all_vms[ref]['resident_on']
            """
            Can start function could return:
            - Empty string means vm can start in that server
            - Not empty string means means vm cannot start in that server (not memory or other error)
            """
            can_start = xc_servers[sessid][host].can_start(ref, h)
            if can_start:
                host_name = host_name + " : " + can_start
            hosts.append([host_name, not (can_start != "" or h == resident_on), h])
        return mylookup.get_template("wherecanmigrate.html").render_unicode(hosts = hosts)

    @cherrypy.expose
    def wherecanstart(self, host, ref): 
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        hosts = []
        if ref not in xc_servers[sessid][host].all_vms:
            return ""
        for h in xc_servers[sessid][host].all_hosts:
            host_name = xc_servers[sessid][host].all_hosts[h]['name_label']
            resident_on = xc_servers[sessid][host].all_vms[ref]['resident_on']
            """
            Can start function could return:
            - Empty string means vm can start in that server
            - Not empty string means means vm cannot start in that server (not memory or other error)
            """
            can_start = xc_servers[sessid][host].can_start(ref, h)
            if can_start:
                host_name = host_name + " : " + can_start
            hosts.append([host_name, not (can_start != "" or h == resident_on), h])
        return mylookup.get_template("wherecanstart.html").render_unicode(hosts = hosts)

    @cherrypy.expose
    def wherecanresume(self, host, ref): 
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        hosts = []
        for h in xc_servers[sessid][host].all_hosts:
            host_name = xc_servers[sessid][host].all_hosts[h]['name_label']
            resident_on = xc_servers[sessid][host].all_vms[ref]['resident_on']
            """
            Can start function could return:
            - Empty string means vm can start in that server
            - Not empty string means means vm cannot start in that server (not memory or other error)
            """
            can_start = xc_servers[sessid][host].can_start(ref, h)
            if can_start:
                host_name = host_name + " : " + can_start
            hosts.append([host_name, not (can_start != "" or h == resident_on), h])
        return mylookup.get_template("wherecanresume.html").render_unicode(hosts = hosts)

    @cherrypy.expose
    def availableservers(self, host, ref): 
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        hosts = []
        for server in xc_servers[sessid]:
            if xc_servers[sessid][server].is_connected == True:
                pool_ref = xc_servers[sessid][server].all_pools.keys()[0]
                if xc_servers[sessid][server].all_pools[pool_ref]["name_label"] == "":
                    ref =  xc_servers[sessid][server].all_hosts.keys()[0]
                    host_name = xc_servers[sessid][server].all_hosts[ref]["name_label"]
                    hosts.append([host_name, ref, server])
        return mylookup.get_template("availableservers.html").render_unicode(hosts = hosts)

    @cherrypy.expose
    def availablepools(self, host, ref): 
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        hosts = []
        for server in xc_servers[sessid]:
            if xc_servers[sessid][server].is_connected == True and server != host:
                pool_ref = xc_servers[sessid][server].all_pools.keys()[0]
                if xc_servers[sessid][server].all_pools[pool_ref]["name_label"] != "":
                    host_name = xc_servers[sessid][server].all_pools[pool_ref]["name_label"]
                    hosts.append([host_name, pool_ref, server])

        return mylookup.get_template("availablepools.html").render_unicode(hosts = hosts)

    @cherrypy.expose
    def fill_vm_search(self, host, ref): 
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        vms, parents = xc_servers[sessid][host].fill_vm_search(ref)
        return json.dumps([parents[0], mylookup.get_template("vmsearch.html").render_unicode(vms = vms)])

    @cherrypy.expose
    def reattachformathbalun(self, sr): 
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return mylookup.get_template("reattachformathbalun.html").render_unicode(sr = sr)

    @cherrypy.expose
    def alerts(self):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listalerts = []
        for host in xc_servers[sessid]:
            listalerts += xc_servers[sessid][host].fill_alerts()
        return mylookup.get_template("windowalerts.html").render_unicode(alerts = listalerts, number = len(listalerts)/2)

    @cherrypy.expose
    def hostdmesg(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        dmesg = xc_servers[sessid][host].get_dmesg(ref)
        return mylookup.get_template("hostdmesg.html").render_unicode(dmesg = dmesg)

    @cherrypy.expose
    def maintancemode(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listmaintenancemode = xc_servers[sessid][host].fill_vms_which_prevent_evacuation(ref)
        return mylookup.get_template("maintenancemode.html").render_unicode(vms = listmaintenancemode)

    @cherrypy.expose
    def exitmaintancemode(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        xc_servers[sessid][host].exit_maintancemode(ref)
        return """
           <script>
            parent.hidePopWin(false);
           </script>
           """

    @cherrypy.expose
    def statusreport(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listreport = xc_servers[sessid][host].fill_list_report(ref)
        return mylookup.get_template("statusreport.html").render_unicode(reports = listreport)        

    @cherrypy.expose
    def wcustomfields(self, host):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listcustomfields = xc_servers[sessid][host].fill_listcustomfields()
        return mylookup.get_template("wcustomfields.html").render_unicode(fields = listcustomfields)        
        
    @cherrypy.expose
    def set_pool_custom_fields(self, host, values):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        xml = "<CustomFieldDefinitions>"
        for value in json.loads(values):
            name, type = value.split(":", 1)
            xml = xml + '<CustomFieldDefinition name="%s" type="%s" defaultValue="" />' % (name, type)
        xml = xml + "</CustomFieldDefinitions>"
        xc_servers[sessid][host].set_pool_custom_fields(xml)
        return "OK"

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

    @cherrypy.expose
    def properties(self, host, ref, type):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        pool_ref =  xc_servers[sessid][host].all_pools.keys()[0]
        if "XenCenter.CustomFields" in xc_servers[sessid][host].all_pools[pool_ref]["gui_config"]:
            customfields = xc_servers[sessid][host].all_pools[pool_ref]["gui_config"]["XenCenter.CustomFields"]
        else:
            customfields = None
        cstmfields = []
        if customfields:
            dom =  xml.dom.minidom.parseString(customfields)
            for node in dom.getElementsByTagName("CustomFieldDefinition"):
                name = node.attributes.getNamedItem("name").value 
                cstmfields.append(name)

        show = {
            "vm" : ["general", "custom", "cpumemory", "startup", "homeserver"],
            "template" : ["general", "custom", "cpumemory", "startup", "homeserver"],
            "custom_template" : ["general", "custom", "cpumemory", "startup", "homeserver"],
            "host" : ["general","custom", "multipath", "logdest"],
            "storage" : ["general","custom"],
            "hostnetwork" : ["general","custom","networksettings"],
            "vdi" : ["general","custom","sizelocation","stgvm"],
            "pool" : ["general", "custom"]
        }
        fields = {}
        cstmvalues = {}
        if type == "pool":
            pool = xc_servers[sessid][host].all_pools[ref]
            fields["txtpropvmname"] = pool["name_label"]
            fields["txtpropvmdesc"] = pool["name_description"]
            fields["general"] = "   <i>" + pool['name_label'] + "</i>"
            other_config = pool['other_config']
            if "folder" in other_config:
                fields["lblpropvmfolder"] = other_config["folder"]
            else:
                fields["lblpropvmfolder"] = "" 
            if "tags" in pool:
                fields["lblpropvmtags"] = ", ".join(pool["tags"])
            else:
                fields["lblpropvmtags"] = ""
        elif type == "server" or type == "host":
            server = xc_servers[sessid][host].all_hosts[ref]
            fields["txtpropvmname"] = server["name_label"]
            fields["txtpropvmdesc"] = server["name_description"]
            fields["general"] = "   <i>" + server['name_label'] + "</i>"
            other_config = server['other_config']
            if "folder" in other_config:
                fields["lblpropvmfolder"] = other_config["folder"]
            else:
                fields["lblpropvmfolder"] = ""
            if "tags" in server:
                fields["lblpropvmtags"] = ", ".join(server["tags"])
            else:
                fields["lblpropvmtags"] = ""
            if server['logging']:
                fields["logdest"] = "Remote " + server["logging"]["syslog_destination"]
                fields["logipdest"] = server["logging"]["syslog_destination"]
            else:
                fields["logdest"] = "Local"
                fields["logipdest"] = ""
        elif type == "storage":
            stg = xc_servers[sessid][host].all_storage[ref]
            fields["txtpropvmname"] = stg["name_label"]
            fields["txtpropvmdesc"] = stg["name_description"]
            fields["general"] = "   <i>" + stg['name_label'] + "</i>"
            other_config = stg['other_config']
            if "folder" in other_config:
                fields["lblpropvmfolder"] = other_config["folder"]
            else:
                fields["lblpropvmfolder"] = "" 
            if "tags" in stg:
                fields["lblpropvmtags"] = ", ".join(stg["tags"])
            else:
                fields["lblpropvmtags"] = ""
        elif type == "vdi":
            vdi_sr = xc_servers[sessid][host].all_vdi[ref]['SR']
            vdi = xc_servers[sessid][host].all_vdi[ref]
            stg_name = xc_servers[sessid][host].all_storage[vdi_sr]['name_label']
            stg_pbds = xc_servers[sessid][host].all_storage[vdi_sr]['PBDs']
            hosts = []
            for stg_pbd in stg_pbds:
               stg_host = xc_servers[sessid][host].all_pbd[stg_pbd]['host']
               hosts.append(xc_servers[sessid][host].all_hosts[stg_host]['name_label'])
            fields["txtpropvmname"] = vdi['name_label']
            fields["txtpropvmdesc"] = vdi["name_description"]
            fields["general"] = "   <i>" + vdi['name_label'] + "</i>"
            subtext = self.convert_bytes(vdi['virtual_size']) + "," + stg_name + " on " + ",".join(hosts)
            fields["stgvm"] = "   <i>" + subtext + "</i>"
            from math import ceil 
            fields["adjvdisize"] = ceil(float(vdi['virtual_size'])/1024/1024/1024)
            fields["listvdilocation"], pos = xc_servers[sessid][host].fill_vdi_location(vdi_sr)
            fields["posvdilocation"] = fields["listvdilocation"][pos][0]
            if vdi['allowed_operations'].count("resize"):
                fields["spinvdisize"] = ""
            else:
                fields["spinvdisize"] = "disabled"
            other_config = vdi['other_config']
            if "folder" in other_config:
                fields["lblpropvmfolder"] = other_config["folder"]
            else:
                fields["lblpropvmfolder"] = "" 
            if "tags" in vdi:
                fields["lblpropvmtags"] = ", ".join(vdi["tags"])
            else:
                fields["lblpropvmtags"] = ""
            listdisks = []
            fields["freedevices"] = {}
            for vbd_ref in xc_servers[sessid][host].all_vdi[ref]['VBDs']:
                vm_ref = xc_servers[sessid][host].all_vbd[vbd_ref]['VM']
                device = xc_servers[sessid][host].all_vbd[vbd_ref]['userdevice']
                mode =   xc_servers[sessid][host].all_vbd[vbd_ref]['mode']
                vm_name = xc_servers[sessid][host].all_vms[vm_ref]['name_label']
                bootable = xc_servers[sessid][host].all_vbd[vbd_ref]['bootable']
                subtext = "Device %s, (%s)" % (device, mode)
                text =  vm_name 
                subtext = "   <i>" + subtext + "</i>"
                fields["freedevices"][vm_ref] = xc_servers[sessid][host].get_allowed_vbd_devices(vm_ref)
                listdisks.append(["images/prop_stgvm.png", text, subtext, mode, device, json.dumps(fields["freedevices"][vm_ref]), bootable, vbd_ref])
            fields["listdisk"] = listdisks

        elif type == "hostnetwork":
            network = xc_servers[sessid][host].all_network[ref]
            fields["txtpropvmname"] = network["name_label"].replace('Pool-wide network associated with eth','Network ')
            fields["txtpropvmdesc"] = network["name_description"]
            fields["general"] = "   <i>" + network['name_label'].replace('Pool-wide network associated with eth','Network ') + "</i>"
            other_config = network['other_config']
            if "folder" in other_config:
                fields["lblpropvmfolder"] = other_config["folder"]
            else:
                fields["lblpropvmfolder"] = "" 
            if "tags" in network:
                fields["lblpropvmtags"] = ", ".join(network["tags"])
            else:
                fields["lblpropvmtags"] = ""
            if "automatic" in network['other_config'] and network['other_config']['automatic'] == "true": 
                fields["checknetworkautoadd"] = "checked"
            else:
                fields["checknetworkautoadd"] = ""
            fields["networksettings"] = "Internal" # FIXME
        elif type == "vm" or type == "template" or type == "custom_template":
            vm = xc_servers[sessid][host].all_vms[ref]
            fields["txtpropvmname"] = vm["name_label"]
            fields["txtpropvmdesc"] = vm["name_description"]
            fields["general"] = "   <i>" + vm['name_label'] + "</i>"
            other_config = vm['other_config']
            if "folder" in other_config:
                fields["lblpropvmfolder"] = other_config["folder"]
            else:
                fields["lblpropvmfolder"] = "" 
            if "tags" in vm:
                fields["lblpropvmtags"] = ", ".join(vm["tags"])
            else:
                fields["lblpropvmtags"] = ""
            fields["cpumemory"] = "   <i>" + "%s VCPU(s) and %s RAM" % (vm["VCPUs_at_startup"],
                    self.convert_bytes(vm["memory_dynamic_max"])) + "</i>"
            fields["spinpropvmmem"] = int(vm["memory_dynamic_min"])/1024/1024
            fields["spinpropvmvcpus"] = int(vm["VCPUs_at_startup"])
            if "weight" in vm["VCPUs_params"]:
                fields["spinpropvmprio"] = float(vm["VCPUs_params"]["weight"])
            else:
                fields["spinpropvmprio"] = 256

            if "auto_poweron" in vm['other_config'] and vm['other_config']["auto_poweron"] == "true":
                fields["startup"] = "   <i>Auto-start on server boot</i>"
            else:
                fields["startup"] = "   <i>None defined</i>"

            if "auto_poweron" in vm['other_config'] and vm['other_config']["auto_poweron"] == "true":
               fields["checkvmpropautostart"] = "checked"
            else:
               fields["checkvmpropautostart"] = ""

            if not vm['HVM_boot_policy']:
                fields["txtvmpropparams"] = vm['PV_args']
            else:
                fields["txtvmpropparams"] = "none"
                listbootorder = []
                for param in list(vm['HVM_boot_params']['order']):
                    if param == 'c':
                        listbootorder.append([param, "Hard Disk", True])
                    elif param == 'd':
                        listbootorder.append([param, "DVD-Drive", True])
                    elif param == 'n':
                        listbootorder.append([param, "Network", True])
                listbootorder.append(["","-------------- VM will not boot from devices below this line ------------", False])
                if vm['HVM_boot_params']['order'].count("c") == 0:
                        listbootorder.append(["c", "Hard Disk", True])
                if vm['HVM_boot_params']['order'].count("d") == 0:
                        listbootorder.append(["d", "DVD-Drive", True])
                if vm['HVM_boot_params']['order'].count("n") == 0:
                        listbootorder.append(["n", "Network", True])
                fields["listbootorder"] = listbootorder

            if vm['affinity'] != "OpaqueRef:NULL" and vm['affinity'] in xc_servers[sessid][host].all_hosts:
                affinity =  xc_servers[sessid][host].all_hosts[vm['affinity']]
                fields["homeserver"] = "   <i>" +  affinity['name_label'] + "</i>"
            else:
                fields["homeserver"] = "   <i>None defined</i>"

            shared = True 
            for vbd_ref in vm['VBDs']:
                vbd = xc_servers[sessid][host].all_vbd[vbd_ref]
                if vbd['VDI'] != "OpaqueRef:NULL" and vbd['VDI'] and vbd['VDI'] in xc_servers[sessid][host].all_vdi:
                    vdi = xc_servers[sessid][host].all_vdi[vbd['VDI']]
                    if not xc_servers[sessid][host].all_storage[vdi['SR']]["shared"]:
                        shared = False 
                        break

            if shared:
                fields["radioautohome"] = "checked"
                fields["radiomanualhome"] = ""    
            else:
                fields["radioautohome"] = "disabled"
                fields["radiomanualhome"] = "checked"    

            fields["listhomeserver"], fields["selhost"] = xc_servers[sessid][host].fill_listhomeserver(vm["affinity"])
            fields["shadowmultiplier"] = "4.00"
            if "HVM_shadow_multiplier" in vm and "HVM_boot_policy" in vm and vm["HVM_boot_policy"]:
                show[type].append("advancedoptions")
                checkoptimize = {}
                checkoptimize["optimizegeneraluse"] = ""
                checkoptimize["optimizeforxenapp"] = ""
                checkoptimize["optimizemanually"] = ""
                if int(vm["HVM_shadow_multiplier"]) == 1:
                    checkoptimize["optimizegeneraluse"] = "checked"
                    fields["advancedoptions"] = "Optimize for general use"
                elif int(vm["HVM_shadow_multiplier"]) == 4:
                    checkoptimize["optimizeforxenapp"] = "checked"
                    fields["advancedoptions"] = "Optimize for Citrix XenApp"
                else:
                    checkoptimize["optimizemanually"] = "checked"
                    fields["advancedoptions"] = "Shadow memory multiplier: %s" % vm["HVM_shadow_multiplier"]
                fields["checkoptimize"] = checkoptimize
                fields["shadowmultiplier"] = vm["HVM_shadow_multiplier"] 

        for config in other_config:
            if "XenCenter.CustomFields." in config:
                cstmvalues[config[23:]] = other_config[config] 


        # FIXME: custom fields
        #listcustomfields = xc_servers[sessid][host].fill_listcustomfields()
        return mylookup.get_template("properties.html").render_unicode(show = show[type], fields = fields, cstmfields = cstmfields, cstmvalues = cstmvalues, type = type, ref = ref)        

    @cherrypy.expose
    def set_properties(self, host, ref, type, values):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        values = json.loads(values) 
        if type == "pool":
            pool = xc_servers[sessid][host].all_pools[ref]
            if values["txtpropvmname"] != pool['name_label']:
                xc_servers[sessid][host].set_pool_name_label(ref,
                        values["txtpropvmname"])
            if values["txtpropvmdesc"] != pool['name_description']:
                xc_servers[sessid][host].set_pool_name_description(ref,
                        values["txtpropvmdesc"])

            other_config = pool["other_config"]
            change, other_config = self.customfields_was_changed(other_config, values)
            if change:
                xc_servers[sessid][host].set_pool_other_config(ref, other_config)

        elif type == "host" or type == "server":
            server = xc_servers[sessid][host].all_hosts[ref]
            if str("syslog_destination" in server["logging"]) == str(values["radiologlocal"]):
                if values["radiologlocal"] == "True":
                    xc_servers[sessid][host].set_host_log_destination(ref,
                            None)
                else:
                    if values["txtlogserver"]:
                        xc_servers[sessid][host].set_host_log_destination(ref,
                                values["txtlogserver"])
                    else:
                        return "You must give a valid server to remote log"
            if values["txtpropvmname"] != server['name_label']:
                xc_servers[sessid][host].set_host_name_label(ref,
                        values["txtpropvmname"])
            if values["txtpropvmdesc"] != server['name_description']:
                xc_servers[sessid][host].set_host_name_description(ref,
                        values["txtpropvmdesc"])

            other_config = server["other_config"]
            change, other_config = self.customfields_was_changed(other_config, values)
            if change:
                xc_servers[sessid][host].set_host_other_config(ref, other_config)
        elif type == "storage":
            stg = xc_servers[sessid][host].all_storage[ref]
            if values["txtpropvmname"] != stg['name_label']:
                xc_servers[sessid][host].set_storage_name_label(ref,
                        values["txtpropvmname"])
            if values["txtpropvmdesc"] != stg['name_description']:
                xc_servers[sessid][host].set_storage_name_description(ref,
                        values["txtpropvmdesc"])

            other_config = stg["other_config"]
            change, other_config = self.customfields_was_changed(other_config, values)
            if change:
                xc_servers[sessid][host].set_storage_other_config(ref, other_config)
        elif type == "hostnetwork":
            network = xc_servers[sessid][host].all_network[ref]
            if values["txtpropvmname"] != network['name_label']:
                xc_servers[sessid][host].set_network_name_label(ref,
                        values["txtpropvmname"])
            if values["txtpropvmdesc"] != network['name_description']:
                xc_servers[sessid][host].set_network_name_description(ref,
                        values["txtpropvmdesc"])
            other_config = network["other_config"]
            change, other_config = self.customfields_was_changed(other_config, values)
            if change:
                xc_servers[sessid][host].set_network_other_config(ref, other_config) 
            if "automatic" in network['other_config'] and network['other_config']['automatic'] == "true":
                if values["checknetworkautoadd"] == str(False):
                    xc_servers[sessid][host].set_network_automatically(ref, False)
            else:
                if str(values["checknetworkautoadd"]) == "True":
                    xc_servers[sessid][host].set_network_automatically(ref, True)


        elif type == "vm" or type == "template" or type == "custom_template":
            vm = xc_servers[sessid][host].all_vms[ref]
            if values["txtpropvmname"] != vm['name_label']:
                xc_servers[sessid][host].set_vm_name_label(ref, values["txtpropvmname"])
            if values["txtpropvmdesc"] != vm['name_description']:
                xc_servers[sessid][host].set_vm_name_description(ref, values["txtpropvmdesc"])
            if int(values["spinpropvmmem"]) != int(vm["memory_dynamic_min"])/1024/1024:
                xc_servers[sessid][host].set_vm_memory(ref, int(values["spinpropvmmem"])) 
            if int(values["spinpropvmvcpus"]) != int(vm["VCPUs_at_startup"]):
                xc_servers[sessid][host].set_vm_vcpus(ref, values["spinpropvmvcpus"])

            if "weight" in vm["VCPUs_params"]:
                if int(values["spinpropvmprio"]) != int(vm["VCPUs_params"]["weight"]):
                    xc_servers[sessid][host].set_vm_prio(ref, values["spinpropvmprio"])
            else:
                if int(values["spinpropvmprio"]) != int(256):
                    xc_servers[sessid][host].set_vm_prio(ref, values["spinpropvmprio"])

            if "auto_poweron" in vm['other_config'] and vm['other_config']["auto_poweron"] == "true":
                if values["checkvmpropautostart"] == str(False) or not values["checkvmpropautostart"]:
                    xc_servers[sessid][host].set_vm_poweron(ref, False)
            else:
                if values["checkvmpropautostart"] == str(True) or values["checkvmpropautostart"]:
                    xc_servers[sessid][host].set_vm_poweron(ref, True)

            if not vm['HVM_boot_policy']:
                if values["txtvmpropparams"] != vm['PV_args']:
                    xc_servers[sessid][host].set_vm_bootpolicy(ref, values["txtvmpropparams"])
            else:
                if values["order"] != vm['HVM_boot_params']['order']:
                    xc_servers[sessid][host].set_vm_boot_params(ref, values["order"])

            if "memorymultiplier" in values:
                if float(values["memorymultiplier"]) != float(vm["HVM_shadow_multiplier"]):
                    xc_servers[sessid][host].set_vm_memory_multiplier(ref, values["memorymultiplier"])


            if (values["radioautohome"] == str(True) or values["radioautohome"]) and (vm["affinity"] != "OpaqueRef:NULL"):
                xc_servers[sessid][host].set_vm_affinity(ref, "OpaqueRef:NULL")
            if values["radiomanualhome"] == str(True) or values["radiomanualhome"]:
                if values["affinity"] != vm["affinity"]:
                    xc_servers[sessid][host].set_vm_affinity(ref, values["affinity"])

            other_config = vm["other_config"]
            change, other_config = self.customfields_was_changed(other_config, values)
            if change:
                xc_servers[sessid][host].set_vm_other_config(ref, other_config) 

        elif type == "vdi":
            vdi_sr = xc_servers[sessid][host].all_vdi[ref]['SR']
            vdi = xc_servers[sessid][host].all_vdi[ref]
            if values["txtpropvmname"] != vdi['name_label']:
                xc_servers[sessid][host].set_vdi_name_label(ref,
                        values["txtpropvmname"])
            if values["txtpropvmdesc"] != vdi['name_description']:
                xc_servers[sessid][host].set_vdi_name_description(ref,
                        values["txtpropvmdesc"])

            if float(values["spinvdisize"]) != float(vdi['virtual_size'])/1024/1024/1024:
               size = float(values["spinvdisize"])*1024*1024*1024
               xc_servers[sessid][host].resize_vdi(ref,size)

            other_config = vdi["other_config"]
            change, other_config = self.customfields_was_changed(other_config, values)
            if change:
                xc_servers[sessid][host].set_vdi_other_config(ref, other_config) 

            for mode in values["modes"]:
                ref = mode.replace("combostgmode_", "")
                if xc_servers[sessid][host].all_vbd[ref]["mode"] != values["modes"][mode]:
                   xc_servers[sessid][host].set_vbd_mode(ref, values["modes"][mode]) 
            for position in values["positions"]: 
                ref = position.replace("combostgposition_", "")
                if int(xc_servers[sessid][host].all_vbd[ref]["userdevice"]) != int(values["positions"][position]):
                   xc_servers[sessid][host].set_vbd_userdevice(ref, values["positions"][position]) 
            for bootable in values["bootables"]:
                ref = bootable.replace("isbootable_", "")
                if xc_servers[sessid][host].all_vbd[ref]["bootable"] != values["bootables"][bootable]:
                   xc_servers[sessid][host].set_vbd_bootable(ref, values["bootables"][bootable]) 
                
        return "OK"

    def customfields_was_changed(self, other_config, values):
        change = False
        for cfield in values["customfields"]:
            field = cfield.replace("cstmvalues_", "")
            if "XenCenter.CustomFields." + field in other_config:
                if values["customfields"][cfield] != other_config["XenCenter.CustomFields." + field]:
                    change = True
                    other_config["XenCenter.CustomFields." + cfield] = values["customfields"][cfield]
            else:
                if values["customfields"][cfield]:
                    change = True
                    other_config["XenCenter.CustomFields." + field] = values["customfields"][cfield]
        return change, other_config

    @cherrypy.expose
    def mgmtinterface(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listinterfaces = xc_servers[sessid][host].fill_mamagement_ifs_list()
        pif_ref = listinterfaces[0][0]
        pif = xc_servers[sessid][host].all_pif[pif_ref]
        name = xc_servers[sessid][host].all_hosts[ref]['name_label']
        listmgmtnetworks, current = xc_servers[sessid][host].fill_management_networks(pif['network'])
        return mylookup.get_template("mgmtinterface.html").render_unicode(interfaces = listinterfaces, name= name, networks = listmgmtnetworks, current = current, pif = pif, pif_ref = pif_ref)        

    @cherrypy.expose
    def updatemanager(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listupdates = xc_servers[sessid][host].fill_list_updates(ref)
        return mylookup.get_template("updatemanager.html").render_unicode(updates = listupdates)

    @cherrypy.expose
    def listupdatestatus(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        host_patches = xc_servers[sessid][host].all_pool_patch[ref]["host_patches"]
        listupdatestatus = []
        for host_ref in xc_servers[sessid][host].all_hosts.keys():
          name = xc_servers[sessid][host].all_hosts[host_ref]['name_label']
          found = False
          for host_patch in host_patches:
              host2 = xc_servers[sessid][host].all_host_patch[host_patch]['host']
              if host_ref == host2:
                  found = True
                  timestamp = xc_servers[sessid][host].all_host_patch[host_patch]['timestamp_applied']
                  patch_text = "<span style='color: green;'>%s - applied (%s)</span>" % (name, \
                      xc_servers[sessid][host].format_date(timestamp))
                  listupdatestatus.append([host, patch_text, False])
          
          if not found:
              patch_text = "<span style='color: red'>%s - not applied</span>" % (name)
              listupdatestatus.append([host, patch_text, True])
        return mylookup.get_template("listupdatestatus.html").render_unicode(updatestatus = listupdatestatus)


    @cherrypy.expose
    def repairstorage(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listrepairstorage = xc_servers[sessid][host].fill_listrepairstorage(ref)
        return mylookup.get_template("repairstorage.html").render_unicode(hosts = listrepairstorage)        

    @cherrypy.expose
    def filerestoreserver(self, host, ref, name):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return mylookup.get_template("filerestoreserver.html").render_unicode(ref = ref, host = host, name = name)        

    @cherrypy.expose
    def filerestorepool(self, host, ref, name):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return mylookup.get_template("filerestorepool.html").render_unicode(ref = ref, host = host, name = name)        

    @cherrypy.expose
    def filenewupdate(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return mylookup.get_template("filenewupdate.html").render_unicode(ref = ref, host = host)        


    @cherrypy.expose
    def newpool(self, selhost, ref=None):
        listpoolhosts = []
        listpoolmaster = []
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        # For each server add to combobox master servers list
        for host in config_hosts.keys():
           # If server is connected..
           if host in xc_servers[sessid]:
               # Add to combo
               pool = False
               for pool_ref in  xc_servers[sessid][host].all_pools:
                   if xc_servers[sessid][host].all_pools[pool_ref]['name_label'] != "":
                        pool = True
               if not pool:
                   listpoolmaster.append([host, xc_servers[sessid][host].hostname])

        # For each server add to possible servers for pool
        for host in config_hosts.keys():
           if host not in xc_servers[sessid]:
               listpoolhosts.append([None, host, 0, "Disconnected", False])
           else:
               if xc_servers[sessid][host].is_connected:
                   pool = False
                   for pool_ref in xc_servers[sessid][host].all_pools:
                       if xc_servers[sessid][host].all_pools[pool_ref]['name_label'] != "":
                            pool = True
                   if not pool:
                       if selhost != host:
                           listpoolhosts.append([host, xc_servers[sessid][host].hostname, False, "", True])
                       else:
                           listpoolhosts.append([host, xc_servers[sessid][host].hostname, True, "Master", False])
                   else:
                       listpoolhosts.append([host, xc_servers[sessid][host].hostname, False, "This server is already in a pool", False])
               else:
                   listpoolhosts.append([None, host, 0, "Disconnected", False])

        return mylookup.get_template("newpool.html").render_unicode(hosts=listpoolhosts, masters=listpoolmaster)

    @cherrypy.expose
    def newnetwork(self, host):
        global xc_servers
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listnetworknic, vlan = xc_servers[sessid][host].fill_listnetworknic()
        return mylookup.get_template("newnetwork.html").render_unicode(networks = listnetworknic, vlan=vlan) 

    @cherrypy.expose
    def newvmdisk(self, host, edit="false"):
        global xc_servers
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listnewvmdisk, default = xc_servers[sessid][host].fill_listnewvmdisk()
        return mylookup.get_template("newvmdisk.html").render_unicode(storages=listnewvmdisk, default=default, edit=edit) 

    @cherrypy.expose
    def vmaddnewdisk(self, host, vm):
        global xc_servers
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listnewvmdisk, default = xc_servers[sessid][host].fill_listnewvmdisk()
        name = xc_servers[sessid][host].all_vms[vm]['name_label']
        return mylookup.get_template("vmaddnewdisk.html").render_unicode(storages=listnewvmdisk, default=default, name=name) 

    @cherrypy.expose
    def stgaddnewdisk(self, host, ref):
        global xc_servers
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listnewvmdisk, default = xc_servers[sessid][host].fill_listnewvmdisk()
        name = xc_servers[sessid][host].all_storage[ref]['name_label']
        return mylookup.get_template("stgaddnewdisk.html").render_unicode(storages=listnewvmdisk, default=default, name=name) 

    @cherrypy.expose
    def vmaddnetwork(self, host, vm):
        global xc_servers
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listaddnetwork = xc_servers[sessid][host].fill_addinterface_network()
        return mylookup.get_template("vmaddnetwork.html").render_unicode(networks=listaddnetwork) 

    @cherrypy.expose
    def vmeditnetwork(self, host, ref):
        global xc_servers
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        vif = xc_servers[sessid][host].all_vif[ref]
        fields = {}
        fields["network_ref"] = vif['network']
        fields["limit"] = ""

        if "kbps" in vif['qos_algorithm_params']:
            fields["limit"] = str(vif['qos_algorithm_params']["kbps"])
        if "MAC_autogenerated" in vif and vif['MAC_autogenerated']:
            fields["radioeditauto"] = "checked"
            fields["radioeditmanual"] = ""
            fields["mac"] = ""
        else:
            fields["radioeditauto"] = ""
            fields["radioeditmanual"] = "checked"
            fields["mac"] = vif['mac']

        listeditnetwork, current = xc_servers[sessid][host].fill_editinterface_network(vif['network'])
        return mylookup.get_template("vmeditnetwork.html").render_unicode(networks=listeditnetwork, current=current, fields=fields) 

    @cherrypy.expose
    def windowcopyvm(self, host, vm):
        global xc_servers
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listcopystg, default = xc_servers[sessid][host].fill_listcopystg()
        name = xc_servers[sessid][host].all_vms[vm]['name_label']
        desc = xc_servers[sessid][host].all_vms[vm]['name_description']
        return mylookup.get_template("windowcopyvm.html").render_unicode(storages=listcopystg, default=default, name=name, desc=desc) 

    @cherrypy.expose
    def vmattachdisk(self, host, vm):
        global xc_servers
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        parents_listattachdisk, children_listattachdisk = xc_servers[sessid][host].fill_vm_storageattach()
        return mylookup.get_template("vmattachdisk.html").render_unicode(parents=parents_listattachdisk, children=children_listattachdisk) 
    
    @cherrypy.expose
    def set_vm_dvd(self, host, vm, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        xc_servers[sessid][host].set_vm_dvd(vm, ref)
        return """
           <script>
            parent.hidePopWin(false);
           </script>
           """

    @cherrypy.expose
    def set_default_storage(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        xc_servers[sessid][host].set_default_storage(ref)
        return """
           <script>
            parent.hidePopWin(false);
           </script>
           """
    @cherrypy.expose
    def repair_storage(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return xc_servers[sessid][host].repair_storage(ref)


    @cherrypy.expose
    def addbond(self, host):
        global xc_servers
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        listavailnics = xc_servers[sessid][host].fill_available_nics()
        return mylookup.get_template("addbond.html").render_unicode(nics= listavailnics) 

    @cherrypy.expose
    def license(self, host, ref):
        sessid = cherrypy.session.id
        if "license_server" in  xc_servers[sessid][host].all_hosts[ref]:
            return mylookup.get_template("licensehost.html").render_unicode(host = host, licenseserver = xc_servers[sessid][host].all_hosts[ref]["license_server"], ref = ref) 
        else:
            return mylookup.get_template("license.html").render_unicode(host = host, ref = ref) 

    @cherrypy.expose
    def is_vlan_available(self, host, vlan):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        for pif_key in xc_servers[sessid][host].all_pif:
            if int(xc_servers[sessid][host].all_pif[pif_key]['VLAN']) == int(vlan):
                return "False"
        return "True"

    @cherrypy.expose
    def get_nic_info(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return json.dumps(xc_servers[sessid][host].fill_nic_info(ref))

    @cherrypy.expose
    def check_password(self, host, password):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        if xc_servers[sessid][host].password != password:
            return "ERROR"
        else:
            return "OK"

    @cherrypy.expose
    def check_master_password(self, password):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        m = md5()
        m.update(password)
        if m.hexdigest() != config["gui"]["master_password"]:
            return "ERROR"
        else:
            return "OK"

    @cherrypy.expose
    def master_password_ok(self, password):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        m = md5()
        m.update(password)
        if m.hexdigest() != config["gui"]["master_password"]:
            return "ERROR"
        else:
            masterpasswords[sessid]  = password
            return "OK"

    @cherrypy.expose
    def set_options(self, checkpassword, password):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        self.toggleoption("save_password", checkpassword)
        masterpasswords[sessid] = "" 
        if checkpassword == "true":
            m = md5()
            m.update(password)
            config["gui"]["master_password"] = m.hexdigest()
            masterpasswords[sessid] = password
            config.write()
 

    @cherrypy.expose
    def applyLicense(self, host, ref, filelicensekey):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        license = filelicensekey.file.read().encode("base64").replace("\n","")
        if xc_servers[sessid][host].install_license_key(ref, license) == "OK":
            return """
               <script>
                alert("license applied");
                parent.hidePopWin(false);
               </script>
               """
        else:
            return """
            <script>
            alert("There was an error processing your license.  Please contact your support representative. Check your settings and try again.")
            parent.hidePopWin(false);
            </script>

            """
            
    @cherrypy.expose
    def destroy_storage(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res =  xc_servers[sessid][host].destroy_storage(ref)
        if res == "OK":
            return """
               <script>
                parent.hidePopWin(false);
               </script>
               """
        else:
            return "<script>alert('" + res + "'); parent.hidePopWin(false); </script>"

    @cherrypy.expose
    def unplug_storage(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res =  xc_servers[sessid][host].unplug_storage(ref)
        if res == "OK":
            return """
               <script>
                parent.hidePopWin(false);
               </script>
               """
        else:
            return "<script>alert('" + res + "'); parent.hidePopWin(false); </script>"

    @cherrypy.expose
    def forget_storage(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res =  xc_servers[sessid][host].forget_storage(ref)
        if res == "OK":
            return """
               <script>
                parent.hidePopWin(false);
               </script>
               """
        else:
            return "<script>alert('" + res + "'); parent.hidePopWin(false); </script>"
    @cherrypy.expose
    def copy_vm(self, host, ref, name, desc, full, sr):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res =  xc_servers[sessid][host].copy_vm(ref, name, desc, sr, full == "true")
        return res

    @cherrypy.expose
    def delete_pool(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res =  xc_servers[sessid][host].delete_pool(ref)
        if res == "OK":
            return """
               <script>
                parent.hidePopWin(false);
               </script>
               """
        else:
            return "<script>alert('" + res + "'); parent.hidePopWin(false); </script>"

    @cherrypy.expose
    def create_pool(self, name, desc, master, slaves):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][master].create_pool(name, desc)
        if res == "OK":
            for slave in slaves.split(","):
                res = xc_servers[sessid][slave].join_pool(xc_servers[sessid][master].host, xc_servers[sessid][master].user, xc_servers[sessid][master].password)
                if res != "OK":
                    return res
        else:
            return res
        return "OK"
        
    @cherrypy.expose
    def add_server_to_pool(self, host, ref, server_ref, server_ip, force=False):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        user = xc_servers[sessid][host].user
        password = xc_servers[sessid][host].password
        if force:
            res =  xc_servers[sessid][server_ip].connection.pool.join_force(xc_servers[sessid][server_ip].session_uuid, host, user, password)
        else:
            res =  xc_servers[sessid][server_ip].connection.pool.join(xc_servers[sessid][server_ip].session_uuid, host, user, password)
        if "Value" in res:
            del xc_servers[sessid][server_ip]
            return """
                <script>
                    alert("Server added to pool correctly")
                    parent.hidePopWin(false);      
                </script>
                """
        else:
            if res["ErrorDescription"][0] == "HOSTS_NOT_HOMOGENEOUS": 
                result = """
                    <script>
                        res = confirm("The hosts in this pool are not homogeneous.  Do you want force join to pool?")
                        if (res == true) {
                        """
                result +=  "document.location = '/add_server_to_pool?host=%s&ref=%s&server_ref=%s&server_ip=%s&force=True';" % (host, ref, server_ref, server_ip)
                result += """
                        } else {
                            parent.hidePopWin(false);      
                        }
                    </script>
                    """
                return result
            else:
                return str(res["ErrorDescription"])


    @cherrypy.expose
    def save_screenshot(self, host, ref, type):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        cherrypy.response.stream = True
        cherrypy.response.headers['Content-Type'] = 'application/x-download'
        cherrypy.response.headers['Content-Disposition'] = "attachment; filename=%s" % ("screenshot.png")
        if type == "host":
            if ref in  xc_servers[sessid][host].host_vm:
                ref = xc_servers[sessid][host].host_vm[ref][0]
            elif uuid in xc_servers[sessid][host].host_vm:
                ref = xc_servers[sessid][host].host_vm[uuid][0]

        f = xc_servers[sessid][host].save_screenshot(host, ref)
        return xc_servers[sessid][host].file2Generator(f)

    @cherrypy.expose
    def pool_backup_database(self, host, ref, name):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        cherrypy.response.stream = True
        cherrypy.response.headers['Content-Type'] = 'application/x-download'
        cherrypy.response.headers['Content-Disposition'] = "attachment; filename=\"%s\"" % (name + "_backup_db_xml")
        f = xc_servers[sessid][host].pool_backup_database(host, ref, name)
        return xc_servers[sessid][host].file2Generator(f)

    @cherrypy.expose
    def pool_restore_database(self, host, ref, file, name, submit=None):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        xc_servers[sessid][host].pool_restore_database(host, ref, file, name);
        return "File uploaded, see logs tab for more information"
        
    @cherrypy.expose
    def host_download_logs(self, host, ref, name):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        f = xc_servers[sessid][host].host_download_logs(host, ref, name)
        cherrypy.response.stream = True
        cherrypy.response.headers['Content-Type'] = 'application/x-download'
        cherrypy.response.headers['Content-Disposition'] = "attachment; filename=\"%s\"" % (name + "_logs.tar.gz")
        return xc_servers[sessid][host].file2Generator(f)

    @cherrypy.expose
    def backup_server(self, host, ref, name):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        f = xc_servers[sessid][host].backup_server(host, ref, name)
        cherrypy.response.stream = True
        cherrypy.response.headers['Content-Type'] = 'application/x-download'
        cherrypy.response.headers['Content-Disposition'] = "attachment; filename=\"%s\"" % (name + ".xbk")
        return xc_servers[sessid][host].file2Generator(f)

    @cherrypy.expose
    def restore_server(self, host, ref, file, name, submit=None):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        xc_servers[sessid][host].restore_server(host, ref, file, name);
        return "File uploaded, see logs tab for more information"
        
    @cherrypy.expose
    def export_vm(self, host, ref, name, ref2="", as_vm=False):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        f = xc_servers[sessid][host].export_vm(host, ref, name, as_vm)
        cherrypy.response.stream = True
        cherrypy.response.headers['Content-Type'] = 'application/x-download'
        cherrypy.response.headers['Content-Disposition'] = "attachment; filename=\"%s\"" % (name + ".xva")
        return xc_servers[sessid][host].file2Generator(f)

    @cherrypy.expose
    def host_download_status_report(self, host, ref, refs, name):
        from time import strftime
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        f = xc_servers[sessid][host].host_download_status_report(host, ref, refs, name)
        name = strftime("status-report-%Y-%m-%d-%H-%M-%S.tar")
        cherrypy.response.stream = True
        cherrypy.response.headers['Content-Type'] = 'application/x-download'
        cherrypy.response.headers['Content-Disposition'] = "attachment; filename=\"%s\"" % (name)
        return xc_servers[sessid][host].file2Generator(f)

    @cherrypy.expose
    def make_into_template(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        xc_servers[sessid][host].make_into_template(ref)
        return """
           <script>
            parent.hidePopWin(false);
            </script>
        """
    @cherrypy.expose
    def start_vm_recovery_mode(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        xc_servers[sessid][host].start_vm_recovery_mode(ref)
        return """
           <script>
            parent.hidePopWin(false);
            </script>
        """

    @cherrypy.expose
    def destroy_vm(self, host, ref, destroy_vdi, destroy_snap, returnOk=False):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        if str(returnOk) == "True":
            vdi = xc_servers[sessid][host].all_vdi[ref]
            for vbd_ref in vdi['VBDs']:
                ref = xc_servers[sessid][host].all_vbd[vbd_ref]["VM"]
                xc_servers[sessid][host].destroy_vm(ref, destroy_vdi == "true", destroy_snap == "true")
        else:
            xc_servers[sessid][host].destroy_vm(ref, destroy_vdi == "true", destroy_snap == "true")
        if str(returnOk) == "True":
            return "OK"
        else:
            return """
               <script>
                parent.hidePopWin(false);
                </script>
            """

    @cherrypy.expose
    def install_xenserver_tools(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        xc_servers[sessid][host].install_xenserver_tools(ref)
        return """
           <script>
            parent.hidePopWin(false);
            </script>
        """

    @cherrypy.expose
    def forget_saved_password(self, host):
        if host in config_hosts: 
           config_hosts[host] = [config_hosts[host][0], "",  config_hosts[host][2]]
           config['servers']['hosts']  = config_hosts
           config.write()
        
        return """
           <script>
            parent.update_vmtree();
            parent.hidePopWin(false);
            </script>
        """

    @cherrypy.expose
    def disconnect(self, host, ref):
        global treestores, xc_servers
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        xc_servers[sessid][host].logout()
        del xc_servers[sessid][host]
        treestores[sessid][ref] = {
            "image" : "images/tree_disconnected_16.png",
            "name" : host,
            "uuid" : None,
            "type" : "server",
            "state" : "Disconnected",
            "host" : host,
            "ref" : None,
            "actions" : ["connect", "forgetpw", "remove"],
            "ip" : None,
            "children" : []
        }

        return """
            <html>
            <head>
            <script>
            parent.update_vmtree();
            parent.document.getElementById("Home").onmousedown();
            parent.hidePopWin(false);
            </script>
            </head>
            <body>Disconnected, close this window.</body>
            </html>
            """
    @cherrypy.expose
    def disconnect_all(self):
        global treestores, xc_servers
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        for host in xc_servers[sessid].keys():
            xc_servers[sessid][host].logout()
            del xc_servers[sessid][host]
        for ref in treestores[sessid].keys():
            if treestores[sessid][ref]["state"] == "Connected" \
                or treestores[sessid][ref]["type"] == "home":
                treestores[sessid][ref] = {
                    "image" : "images/tree_disconnected_16.png",
                    "name" : host,
                    "uuid" : None,
                    "type" : "server",
                    "state" : "Disconnected",
                    "host" : host,
                    "ref" : None,
                    "actions" : ["connect", "forgetpw", "remove"],
                    "ip" : None,
                    "children" : []
                }

        return """
            <html>
            <head>
            <script>
            parent.update_vmtree();
            parent.hidePopWin(false);
            </script>
            </head>
            <body>Disconnected, close this window.</body>
            </html>
            """
    @cherrypy.expose
    def remove_server_from_pool(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        pool_ref = xc_servers[sessid][host].all_pools.keys()[0]
        if xc_servers[sessid][host].all_pools[pool_ref]["name_label"] != "":
            if xc_servers[sessid][host].all_pools[pool_ref]["master"] != ref:
                 res = xc_servers[sessid][host].remove_server_from_pool(ref)
                 if res == "OK":
                    return "<script>parent.hidePopWin(false);</script>"
                 else:
                    return "<script>alert('" + res + "');parent.hidePopWin(false);</script>"
            else:
                return "<script>alert('This server is the master on pool');parent.hidePopWin(false);</script>"
        else:
            return "<script>alert('This server is not on pool');parent.hidePopWin(false);</script>"

    @cherrypy.expose
    def reconfigure_pif(self, host, ref, pif_ref, configuration_mode, ip, mask, gw, dns):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return xc_servers[sessid][host].reconfigure_pif(pif_ref, configuration_mode, ip, mask, gw, dns, ref)

    @cherrypy.expose
    def rescanisos(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return xc_servers[sessid][host].rescan_isos(ref)

    @cherrypy.expose
    def cancel_task(self, host, task_ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return xc_servers[sessid][host].cancel_task(task_ref)
    
    @cherrypy.expose
    def toggleoption(self, option, value):
        global config
        if option in config["gui"]:
            config["gui"][option] = str(value == "true")
            config.write()

    @cherrypy.expose
    def toggleoptionmaps(self, option, value):
        global config
        if option in config["maps"]:
            config["maps"][option] = str(value == "true")
            config.write()

    @cherrypy.expose
    def remove_server(self, host):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        del config_hosts[host]
        del treestores[sessid][host]
        treestores[sessid]["home"]["children"].remove(host)
        config['servers']['hosts']  = config_hosts
        config.write()
        return "<script>parent.update_vmtree();parent.hidePopWin(false);</script>"

    @cherrypy.expose
    def reboot_server(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].reboot_server(ref)
        if res == "OK":
            del xc_servers[sessid][host]
            treestores[sessid][ref] = {
                "image" : "images/tree_disconnected_16.png",
                "name" : host,
                "uuid" : None,
                "type" : "server",
                "state" : "Disconnected",
                "host" : host,
                "ref" : None,
                "actions" : ["connect", "forgetpw", "remove"],
                "ip" : None,
                "children" : []
            }

            return "<script>parent.update_vmtree();parent.hidePopWin(false);</script>"
        else:
            return "<script>alert('Error rebooting server: %s');parent.hidePopWin(false);</script>" % res

    @cherrypy.expose
    def shutdown_server(self, host, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        res = xc_servers[sessid][host].shutdown_server(ref)
        if res == "OK":
            del xc_servers[sessid][host]
            treestores[sessid][ref] = {
                "image" : "images/tree_disconnected_16.png",
                "name" : host,
                "uuid" : None,
                "type" : "server",
                "state" : "Disconnected",
                "host" : host,
                "ref" : None,
                "actions" : ["connect", "forgetpw", "remove"],
                "ip" : None,
                "children" : []
            }

            return "<script>parent.update_vmtree();parent.hidePopWin(false);</script>"
        else:
            return "<script>alert('Error on shutdown server: %s');parent.hidePopWin(false);</script>" % res


    @cherrypy.expose
    def apply_patch(self, host, host_ref, ref):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        return xc_servers[sessid][host].apply_patch(host_ref, ref)

    @cherrypy.expose
    def remove_patch(self, host, host_ref, ref):
       sessid = cherrypy.session.id
       cherrypy.session.release_lock()
       return xc_servers[sessid][host].remove_patch(host_ref, ref)

    @cherrypy.expose
    def upload_patch(self, host, ref, file, submit=None):
        sessid = cherrypy.session.id
        cherrypy.session.release_lock()
        xc_servers[sessid][host].upload_patch(host, ref, file);
        return "File uploaded, see logs tab for more information"

    @cherrypy.expose
    def close_console(self):
        global tunnels
        sessid = cherrypy.session.id
        if sessid in tunnels:
            for tunnel in tunnels[sessid]:
                tunnel.close()
                if sessid in tunnels:
                    del tunnels[sessid]
            try:
                websocket.do_halt()
            except:
                pass

            tunnel = None


    def dump(self, obj):
        """
        Internal use only
        """
        for attr in dir(obj):
           print "obj.%s = %s" % (attr, getattr(obj, attr))



############## MISC FUNCTIONS #######################################

def close_threads():
    for tunnel in tunnels:
        for tunnel2 in tunnels[tunnel]:
            tunnels[tunnel][tunnel2].close()
            del tunnels[tunnel][tunnel2]
    try:
        websocket.halt = True
    except:
        pass
        
    for sessid in xc_servers:
        for host in xc_servers[sessid]:
            print "Logout of: ", host
            xc_servers[sessid][host].logout()

if len(sys.argv) > 1 and sys.argv[1] == "-daemon":
    d = Daemonizer(cherrypy.engine)
    d.subscribe()

else:
    print "Logging to access_log and error_log files..."

    
# Set up the site
if os.path.exists("/etc/xenmagic/cherry.conf"):
    cherrypy.config.update("/etc/xenmagic/cherry.conf")
else:
    cherrypy.config.update("cherry.conf")
# Set up the application
root = frontend()
cherrypy.engine.subscribe('exit', close_threads)
if os.path.exists("/etc/xenmagic/cherry.conf"):
    cherrypy.tree.mount(root, "/", "/etc/xenmagic/cherry.conf")
else:
    cherrypy.tree.mount(root, "/", "cherry.conf")
cherrypy.engine.start()
cherrypy.engine.block()

