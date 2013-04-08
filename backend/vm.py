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
from vm_network import *
from vm_storage import *
from vm_snapshot import *

class vm(vmnetwork,vmstorage,vmsnapshot):
   def thread_import_vm(self, ref, file):
        Thread(target=self.import_vm, args=(ref, file)).start()
        return True

   def copy_vm(self, ref, name, desc, sr=None, full=False):
       if full:
            res = self.connection.Async.VM.copy(self.session_uuid, ref, name, sr)
            if "Value" in res:
                self.track_tasks[res['Value']] = ref
                self.set_descriptions[res['Value']] = desc
                return "OK"
            else:
                return res["ErrorDescription"][0]
       else:
            res = self.connection.Async.VM.clone(self.session_uuid, ref, name)
            if "Value" in res:
                self.track_tasks[res['Value']] = ref
                self.set_descriptions[res['Value']] = desc
                return "OK"
            else:
                return res["ErrorDescription"][0]

   def fill_importstg(self, ref):
        list = []
        for sr in self.all_storage.keys():
            storage = self.all_storage[sr]
            if storage['type'] != "iso" and storage['type'] != "udev":
                if len(self.all_storage[sr]['PBDs']) == 0 or self.all_pbd[self.all_storage[sr]['PBDs'][0]]['currently_attached'] == False \
                    or  len(self.all_storage[sr]['PBDs']) > 0 and self.all_storage[sr]["allowed_operations"].count("unplug") ==  0:
                    pass
                else:
                    on_host = False
                    for pbd in storage['PBDs']:
                        if self.all_pbd[pbd]['host'] == ref:
                            on_host = True

                    if storage['shared'] or on_host:
                        if self.default_sr == sr:
                            list.append(["images/storage_default_16.png", sr, storage['name_label'],
                             self.convert_bytes(int(storage['physical_size'])-int(storage['virtual_allocation'])) + " free of " + \
                             self.convert_bytes(storage['physical_size'])])

                        else:
                            list.append(["images/storage_shaped_16.png", sr, storage['name_label'],
                             self.convert_bytes(int(storage['physical_size'])-int(storage['virtual_allocation'])) + " free of " + \
                             self.convert_bytes(storage['physical_size'])])
        return list
