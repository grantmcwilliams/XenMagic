var selected_actions = new Array();
var selected_type = "home";
var selected_ref = "";
var selected_hostname = "";
var selected_type = "";
var selected_host = "";
var selected_uuid = "";
var selected_state = "";
var selected_name = "";
var selected_tab = "";
var selected_window = "";

var hosts = new Array();
var checkupdates = true;

var selected_vdi_ref = "";
var selected_vdi_issnap = "";
var selected_vdi_vm_ref = "";
var selected_vif_vm_ref = "";
var selected_snap_vm_ref = "";
var selected_snap_vm_name = "";
var selected_vbd_vm_ref = "";
var selected_network_ref = "";
var selected_row_ref = "";
var selected_row_color = "";

function updateContextMenu() {
    $('div.elementvmtree').contextMenu('menu_vm', {
          bindings: {
            'm_start': function(t) {
               callFunction('start_vm')
            },
            'm_repair_storage': function(t) {
               showPopWin('repairstorage?host=' + selected_host + '&ref=' + selected_ref, 470, 420, null);
            },
            'm_connect': function(t) {
               showPopWin('addserver?host=' + selected_host, 440, 260, null);
            },
            'm_disconnect': function(t) {
                javascript:showPopWin('disconnect?host=' + selected_host + '&ref=' + selected_ref, 320, 200, null); 
                document.getElementById('home').onclick();
            },
            'm_forgetpw': function(t) {
                showPopWin('forget_saved_password?host=' + selected_host, 440, 260, null);
            },
            'm_remove': function(t) {
               showPopWin('remove_server?host=' + selected_host, 320, 200, null);   
            },
            'm_newvm': function(t) {
                showPopWin('newvm?host=' + selected_host, 805, 550, null);
            },
            'm_newstorage': function(t) {
                showPopWin('newstorage?host=' + selected_host, 840, 550, null);
            },
            'm_addserver': function(t) {
                showPopWin('addserver?host=' + selected_host, 440, 260, null);
            },
            'm_clean_shutdown': function(t) {
                callFunction('clean_shutdown_vm');
            },
            'm_suspend': function(t) {
                callFunction('suspend_vm');
            },
            'm_pause': function(t) {
                callFunction('suspend_vm'); 
            },
            'm_unsuspend': function(t) {
                callFunction('resume_vm');
            },
            'm_unpause': function(t) {
                callFunction('resume_vm');
            },
            'm_clean_reboot': function(t) {
                callFunction('clean_reboot_vm');
            },
            'm_snapshot': function(t) {
                on_bttakesnapshot_clicked();
            },
            'm_installxenservertools': function(t) {
                showPopWin('install_xenserver_tools?host=' + selected_host + '&ref=' + selected_ref, 520, 300, null);
            },
            'm_hard_shutdown': function(t) {
                callFunction('hard_shutdown_vm');
            },
            'm_hard_reboot': function(t) {
                callFunction('hard_reboot_vm');
            },
            'm_unplug': function(t) {
                on_menuitem_stg_unplug_clicked();
            },
            'm_plug': function(t) {
                showPopWin('newstorage?host=' + selected_host + '&ref=' + selected_ref, 840, 550, null);
            },
            'm_forget': function(t) {
                on_menuitem_stg_forget_clicked(); 
            },
            'm_copy': function(t) {
                showPopWin('windowcopyvm?host=' + selected_host + '&vm=' + selected_ref, 620, 530, null);
            },
            'm_export': function(t) {
                showPopWin('export_vm?host=' + selected_host + '&ref=' + selected_ref + '&name=' + selected_name, 520, 300, null);
            },
            'm_make_into_template': function(t) {
                showPopWin('make_into_template?host=' + selected_host + '&ref=' + selected_ref, 520, 300, null);
            },
            'm_destroy': function(t) {
                on_m_destroy_activate();
            },
            'm_delete': function(t) {
                on_m_destroy_activate();
            },
            'm_connectall': function(t) {
                alert("TODO");
            },
            'm_disconnectall': function(t) {
                showPopWin('disconnect_all', 320, 200, null); document.getElementById('home').onclick();
            },
            'm_properties': function(t) {
                showPopWin('properties?host=' + selected_host + '&ref=' + selected_ref + '&type=' + selected_type, 820, 570, null);
            },
            'm_pool_migrate': function(t) {
                alert("TODO");
            }

          },
          onShowMenu: function(e, menu) {
            var menu_vm = document.getElementById("menu_vm");            
            var elements = menu_vm.getElementsByTagName("ul")[0].getElementsByTagName("li");
            for (element in elements) {
                if (elements[element].id) {
                    if (elements[element].id.substring(0,2) == "m_") {
                        var name = elements[element].id.substr(2);    
                        if (!(name in oc(selected_actions))) {
                            $('#' + elements[element].id, menu).remove();
                        }
                    }
                }
            }
            return menu;
          }
        });
}
function callFunction(func, ref2) {
    var client = new XMLHttpRequest();
    client.onreadystatechange = function () {
        if(this.readyState == 4 && this.status == 200) {
            if (this.responseText != "OK") {
                alert(this.responseText);
            }
        } else if (this.readyState == 4 && this.status != 200) {
            alert("Error on callFunction()");
        }
    }
    if (!ref2) {
        client.open("GET", "do_action?action=" + func + "&ref=" + selected_ref + "&host=" + selected_host);
    } else {
        client.open("GET", "do_action?action=" + func + "&ref=" + selected_ref + "&host=" + selected_host + "&ref2=" + ref2);
    }
    client.send()
}
function callRowFunction(func, ref2) {
    var client = new XMLHttpRequest();
    client.onreadystatechange = function () {
        if(this.readyState == 4 && this.status == 200) {
            if (this.responseText != "OK") {
                alert(this.responseText);
            }
        } else if (this.readyState == 4 && this.status != 200) {
            alert("Error on callFunction()");
        }
    }
    if (!ref2) {
        client.open("GET", "do_action?action=" + func + "&ref=" + selected_row_ref + "&host=" + selected_host);
    } else {
        args = "";
        for (var i in ref2) {
            args = "&" + i + "=" + ref2[i];
        }

        client.open("GET", "do_action?action=" + func + "&ref=" + selected_row_ref + "&host=" + selected_host + args);
    }
    client.send()
}

function selectRow(ref) {
    if (selected_row_ref && document.getElementById(selected_row_ref)) {
        document.getElementById(selected_row_ref).style.backgroundColor = selected_row_color
    }
    selected_row_ref = ref;
    selected_row_color = document.getElementById(selected_row_ref).style.backgroundColor;
    document.getElementById(selected_row_ref).style.backgroundColor = "#3366CC";
}

function selectHostNetworkRow(ref) {
    document.getElementById("bthostnetworkproperties").disabled = false;
    if (selected_network_ref && document.getElementById(selected_network_ref)) {
        document.getElementById(selected_network_ref).style.backgroundColor = selected_row_color
    }
    selected_network_ref = ref;
    selected_row_color =  document.getElementById(selected_network_ref).style.backgroundColor;
    document.getElementById(selected_network_ref).style.backgroundColor = "#3366CC";
}

function selectVdiRow(ref, issnap) {
    document.getElementById("btstgproperties").disabled = false;
    document.getElementById("btstgremove").disabled = false;
    if (selected_vdi_ref && document.getElementById(selected_vdi_ref)) {
        document.getElementById(selected_vdi_ref).style.backgroundColor = selected_row_color
    }
    selected_vdi_ref = ref;
    selected_vdi_issnap = issnap;
    selected_row_color =  document.getElementById(selected_vdi_ref).style.backgroundColor;
    document.getElementById(selected_vdi_ref).style.backgroundColor = "#3366CC";
}
function selectVdiVmRow(ref, ref_vbd, attached, type, destroy) {
    document.getElementById("btstorageproperties").disabled = false;
    if (selected_vdi_vm_ref && document.getElementById(selected_vdi_vm_ref)) {
        document.getElementById(selected_vdi_vm_ref).style.backgroundColor = selected_row_color
    }
    selected_vdi_vm_ref = ref;
    selected_vbd_vm_ref = ref_vbd;
    selected_row_color =  document.getElementById(selected_vdi_vm_ref).style.backgroundColor;
    document.getElementById(selected_vdi_vm_ref).style.backgroundColor = "#3366CC";

    if (type == "user") {
        document.getElementById("btstoragedeactivate").disabled = false;
        if (attached == "True") {
            document.getElementById("btstoragedeactivate").value = "Deactivate";
        } else {
            document.getElementById("btstoragedeactivate").value = "Activate";
            document.getElementById("btstoragedetach").disabled = false;    
        }
    } else {
        document.getElementById("btstoragedeactivate").disabled = true;
        document.getElementById("btstoragedetach").disabled = true;
    }
    document.getElementById("btstoragedelete").disabled  = (destroy != "True");
}
function selectVifVmRow(ref, destroy) {
    document.getElementById("btpropertiesinterface").disabled = false;
    if (selected_vif_vm_ref && document.getElementById(selected_vif_vm_ref)) {
        document.getElementById(selected_vif_vm_ref).style.backgroundColor = selected_row_color
    }
    selected_vif_vm_ref = ref;
    selected_row_color =  document.getElementById(selected_vif_vm_ref).style.backgroundColor;
    document.getElementById(selected_vif_vm_ref).style.backgroundColor = "#3366CC";
    if (destroy == 1) {
        document.getElementById("btremoveinterface").disabled = false;
    } else {
        document.getElementById("btremoveinterface").disabled = true;
    }
}

function selectSnapRow(ref, name, revert) {
    document.getElementById("btsnapnewvm").disabled = false;
    document.getElementById("btsnapcreatetpl").disabled = false;
    document.getElementById("btsnapexport").disabled = false;
    document.getElementById("btsnapexportvm").disabled = false;
    document.getElementById("btsnapdelete").disabled = false;
    document.getElementById("btsnaprevert").disabled = (revert != 'True');
    if (selected_snap_vm_ref && document.getElementById(selected_snap_vm_ref)) {
        document.getElementById(selected_snap_vm_ref).style.backgroundColor = selected_row_color
    }
    selected_snap_vm_ref = ref;
    selected_snap_vm_name = name;
    selected_row_color =  document.getElementById(selected_snap_vm_ref).style.backgroundColor;
    document.getElementById(selected_snap_vm_ref).style.backgroundColor = "#3366CC";
 
}

function on_m_destroy_activate() {
    if (selected_type == "vm") {
        var res = confirm("Are you sure you want to delete VM '" + selected_name + "' ?")
    } else {
        var res = confirm("Are you sure you want to delete template '" + selected_name + "' ?")
    }
    var res1 = confirm("Do you want delete attached virtual disks?")
    var res2 = confirm("Do you want delete associated snapshots?") 
    if (res == true) {
       showPopWin('/destroy_vm?host=' + selected_ip + '&ref=' + selected_ref + '&destroy_vdi=' + res1 + '&destroy_snap=' + res2, 520, 300, null);
    }
}
function autoconnect(hostname, username, password, ssl) {
    var hostname = escape(hostname);
    var username = escape(username);
    var password = escape(password);
    var ssl = (ssl == "True");
    var client = new XMLHttpRequest();
    client.onreadystatechange = update_connect_status;
    client.open("POST", "connect_server", true);
    params = "hostname=" + hostname + "&username=" + username + "&password=" + password + "&ssl=" + ssl + "&decrypt=true"
    selected_host = hostname
    client.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    client.setRequestHeader("Content-Length", params.length);
    client.setRequestHeader("Connection", "close");
    client.send(params);
    document.getElementById("popupFrame").contentWindow.document.getElementById("connecting").style.display="";
    document.getElementById("popupFrame").contentWindow.document.getElementById("addserver").style.display="none";
}

function connect() {
    hostname = escape(document.getElementById("popupFrame").contentWindow.document.getElementById("addserverhostname").value)
    username = escape(document.getElementById("popupFrame").contentWindow.document.getElementById("addserverusername").value)
    password = escape(document.getElementById("popupFrame").contentWindow.document.getElementById("addserverpassword").value)
    ssl = escape(document.getElementById("popupFrame").contentWindow.document.getElementById("checksslconnection").checked)
    var client = new XMLHttpRequest();
    client.onreadystatechange = update_connect_status;
    client.open("POST", "connect_server", true);
    params = "hostname=" + hostname + "&username=" + username + "&password=" + password + "&ssl=" + ssl
    selected_host = hostname
    client.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    client.setRequestHeader("Content-Length", params.length);
    client.setRequestHeader("Connection", "close");
    client.send(params);
    document.getElementById("popupFrame").contentWindow.document.getElementById("connecting").style.display="";
    document.getElementById("popupFrame").contentWindow.document.getElementById("addserver").style.display="none";
}

function update_connect_status() {
    // Function handler when for update tabs
    if(this.readyState == 4 && this.status == 200) {
        if (this.responseText == "OK") {
            hostname = escape(document.getElementById("popupFrame").contentWindow.document.getElementById("addserverhostname").value);
            var client = new XMLHttpRequest();
            client.onreadystatechange = get_response_update_vmtree;
            var searchvmtree = document.getElementById("searchvmtree").value;
            client.open("GET", "vmtree?filter=" + escape(searchvmtree));
            client.send();
            hidePopWin(false);
            update_alerts();
            document.getElementById("popupFrame").contentWindow.document.getElementById("connecting").style.display="none"
            document.getElementById("popupFrame").contentWindow.document.getElementById("addserver").style.display="";
            func_update(hostname);

        } else {
            document.getElementById("popupFrame").contentWindow.document.getElementById("connecting").style.display="none"
            document.getElementById("popupFrame").contentWindow.document.getElementById("addserver").style.display="";
            alert(this.responseText)
        }
    } else if (this.readyState == 4 && this.status != 200) {
        alert("error update_connect_status..");
    }
}

function update_vmtree() {
    var client = new XMLHttpRequest();
    var searchvmtree = document.getElementById("searchvmtree").value;
    client.onreadystatechange = get_response_update_vmtree;
    client.open("GET", "vmtree?filter=" + escape(searchvmtree));
    client.send()
}
function update_tab_pool_general() {
    return;
    alert("update_tab_pool_general");
}
function show_reconnect_alert() {
    return;
}
function update_alerts() {
   var client = new XMLHttpRequest();
    client.open("GET", "get_alerts_count", true);
    client.onreadystatechange = function() {
        return function() {
            if(this.readyState == 4 && this.status == 200) {
                if (this.responseText != "0") {
                   document.getElementById("imgtbalerts").src="images/warn.png"
                   document.getElementById("txttbalerts").innerHTML = this.responseText + " System Alerts"
                   document.getElementById("txttbalerts").style.color = "red"
                } else {
                   document.getElementById("imgtbalerts").src="images/ok.png"
                   document.getElementById("txttbalerts").innerHTML ="No System Alerts"
                   document.getElementById("txttbalerts").style.color = "black"

                }
            } else if (this.readyState == 4 && this.status != 200) {
                document.getElementById("statusbar").innerHTML = "error updating alert count";
            }            
        }
    }()
    client.send(null)
    if (selected_window == "alerts") {
       hidePopWin(false);
       showPopWin('/alerts', 850, 500, null); 
    } 
    return;
}
function update_host_networks() {
    if ((selected_type == "server" || selected_type == "host") && selected_tab == "framehostnetwork") {
        on_tabbox_focus_tab("", 'framehostnetwork');
    }
	return;
}
function update_host_nics() {
    if ((selected_type == "server" || selected_type == "host") && selected_tab == "framehostnics") {
        on_tabbox_focus_tab("", 'framehostnics');
    }
	return;
}
function update_local_storage() {
    if ((selected_type == "storage") && selected_tab == "framestgdisks") {
        on_tabbox_focus_tab("", 'framestgdisks');
    }
	return;
}
function update_logs() {
    if (selected_tab == "framelogs") {
        on_tabbox_focus_tab("", 'framelogs');
    }
	return;
}
function update_snapshots() {
    if (selected_type == "vm" && selected_tab == "framesnapshots") {
        on_tabbox_focus_tab("", 'framesnapshots');
    }
	return;
}
function update_vm_network() {
    if (selected_type == "vm" && selected_tab == "framevmnetwork") {
        on_tabbox_focus_tab("", 'framevnnetwork');
    }
	return;
}
function update_vm_storage() {
    if (selected_type == "vm" && selected_tab == "framevmstorage") {
        on_tabbox_focus_tab("", 'framevmstorage');
    }
	return;
}


function get_response_update_vmtree() {
    if(this.readyState == 4 && this.status == 200) {
        
        document.getElementById("idvmtree").innerHTML = this.responseText;
        sitemapstyler();
        hosts.push(selected_host);        
        check_updates(hosts);
        if (last_widget) {
            widget = document.getElementById(selected_ref);
            // Set background color
            if (last_widget) {
                last_widget.style.backgroundColor="#fcfcfc";
                last_widget.style.color="black";
            }           
            last_widget = widget
            if(widget) {
                widget.style.backgroundColor="#4b6983";
                widget.style.color="white";
                widget.style.zIndex="-100";
                var error = "";
                try {
                    widget.onclick();
                } catch (err) {
                    error = err; 
                }
            }
        }
        updateContextMenu();
    } else if (this.readyState == 4 && this.status != 200) {
        alert("error update_vmtree..");
    }
}

function check_updates(hosts) {
    if (checkupdates) {
        for (var h = 0; h < hosts.length; h++) {
            if (hosts[h])  {
                func_update(hosts[h])
            }
        }
    }
    checkupdates = false
}

function func_update(ref) {
    var allow_functions = new Array("show_reconnect_alert", "update_alerts",
        "update_host_network", "update_host_networks", "update_host_nics", "update_local_storage", 
        "update_logs", "update_snapshots", "update_tab_pool_general", "update_vm_network", 
        "update_vm_snapshots", "update_vm_storage", "update_vmtree")
    var client = new XMLHttpRequest();
    client.open("GET", "get_update?ref=" + ref, true);
    client.onreadystatechange = function(ref2) {
         return function() {
            if(this.readyState == 4 && this.status == 200) {
                var returned = eval('(' + this.responseText + ')');
                functions = returned[0]
                alertinfo = returned[1]
                if (alertinfo) {
                    document.getElementById("statusbar").innerHTML = alertinfo
                }
                for (i=0; i < functions.length; i++) {
                    if (functions[i] in oc(allow_functions)) {
                        eval(functions[i] + "()"); 
                     } else {
                        alert("javascript function not allowed");
                    }         
                }
                setTimeout("func_update('" + ref2 + "')", 5000);
            } else if (this.readyState == 4 && this.status != 200) {
                document.getElementById("statusbar").innerHTML = "error update_tree.. event_next..";
            }
        }
    }(ref);
    client.send(null)
} 

// Host
function on_hostnetwork_selected(physical) {
    document.getElementById("bthostnetworkremove").disabled = (physical == "True");

}
function on_hostnics_selected(bond) {
    document.getElementById("bthostnicremove").disabled = (bond != "True");
}
function on_bthostnetworkremove_clicked() {
    var argument = new Object();
    argument["ref_vm"] = selected_ref;
    callRowFunction("delete_network", argument);
}

function on_bthostnicremove_clicked() {
    var argument = new Object();
    argument["ref_vm"] = selected_ref;
    callRowFunction("delete_nic", argument);
}

function on_btstoragedetach_clicked() {
    var ref = selected_vbd_vm_ref 
    var client = new XMLHttpRequest();
    client.open("GET", "vm_storagedetach?host=" + parent.selected_host + "&ref=" + ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            if (this.responseText != "OK") {
                alert(this.responseText);
            }
            parent.hidePopWin(false);
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error on_btstoragedetach_clicked";
        }            
    }
    client.send(null)    
    
}

function on_btstoragedeactivate_clicked() {
    var label = escape(document.getElementById("btstoragedeactivate").value);
    var ref = selected_vbd_vm_ref;
    var client = new XMLHttpRequest();
    if (label == "Activate") {
        client.open("GET", "vm_storageplug?host=" + parent.selected_host + "&ref=" + ref, true);
    } else {
        client.open("GET", "vm_storageunplug?host=" + parent.selected_host + "&ref=" + ref, true);
    }
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            if (this.responseText != "OK") {
                alert(this.responseText);
            }
            parent.hidePopWin(false);
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error on_btstoragedeactivate_clicked";
        }            
    }
    client.send(null)    
}

function on_btstoragedelete_clicked() {
    var ref = selected_vdi_vm_ref 
    var client = new XMLHttpRequest();
    var res = confirm("This will delete this virtual disk permanently, destroying the data on it. Continue?");

    if (res == true) {        
        client.open("GET", "delete_vdi?host=" + parent.selected_host + "&ref=" + ref + "&vm=" + parent.selected_ref, true);
        client.onreadystatechange = function() {
            if(this.readyState == 4 && this.status == 200) {
                if (this.responseText != "OK") {
                    alert(this.responseText);
                }
                parent.hidePopWin(false);
            } else if (this.readyState == 4 && this.status != 200) {
                parent.document.getElementById("statusbar").innerHTML = "error on_btstoragedelete_clicked";
            }            
        }
        client.send(null)    
    }
}

function on_btremoveinterface_clicked() {
    var ref = selected_vif_vm_ref 
    var client = new XMLHttpRequest();
    var res = confirm("This will delete the selected network interface permanently. Continue?");

    if (res == true) {        
        client.open("GET", "vm_remove_interface?host=" + parent.selected_host + "&ref=" + ref + "&vm=" + parent.selected_ref, true);
        client.onreadystatechange = function() {
            if(this.readyState == 4 && this.status == 200) {
                if (this.responseText != "OK") {
                    alert(this.responseText);
                }
                parent.hidePopWin(false);
            } else if (this.readyState == 4 && this.status != 200) {
                parent.document.getElementById("statusbar").innerHTML = "error on_btremoveinterface_clicked";
            }            
        }
        client.send(null)    
    }
}

function on_bttakesnapshot_clicked() {
   var name=prompt("New snapshot name:","Snapshot of " + self.selected_name ); 
   if (name != null && name != "") {
        var ref = selected_ref;
        var client = new XMLHttpRequest();
        client.open("GET", "take_snapshot?host=" + selected_host + "&ref=" + ref + "&name=" + name, true);
        client.onreadystatechange = function() {
            if(this.readyState == 4 && this.status == 200) {
                if (this.responseText != "OK") {
                    alert(this.responseText);
                }
                parent.hidePopWin(false);
            } else if (this.readyState == 4 && this.status != 200) {
                parent.document.getElementById("statusbar").innerHTML = "error on_btremoveinterface_clicked";
            }            
        }
        client.send(null)    
 
   } else {
        alert("Please specify a name");
   } 
}

function on_btrevertsnap_clicked() {
    var ref = selected_ref;
    var client = new XMLHttpRequest();
    client.open("GET", "revert_to_snapshot?host=" + selected_host + "&ref=" + ref + "&snapref=" + selected_snap_vm_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            if (this.responseText != "OK") {
                alert(this.responseText);
            }
            parent.hidePopWin(false);
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error on_btremoveinterface_clicked";
        }            
    }
    client.send(null)    
 
}

function on_btsnapcreatetpl_clicked() {
   var name=prompt("Enter name for new template:","Template from snapshot " + selected_snap_vm_name); 
   if (name != null && name != "") {
        var ref = selected_snap_vm_ref;
        var client = new XMLHttpRequest();
        client.open("GET", "create_template_from_snap?host=" + selected_host + "&ref=" + ref + "&name=" + name, true);
        client.onreadystatechange = function() {
            if(this.readyState == 4 && this.status == 200) {
                if (this.responseText != "OK") {
                    alert(this.responseText);
                }
                parent.hidePopWin(false);
            } else if (this.readyState == 4 && this.status != 200) {
                parent.document.getElementById("statusbar").innerHTML = "error on_btremoveinterface_clicked";
            }            
        }
        client.send(null)    
 
   } else {
        alert("Please specify a name");
   } 
}


function on_btsnapdelete_activate() {
    var ref = selected_snap_vm_ref 
    var client = new XMLHttpRequest();
    var res = confirm("Are you sure you want to delete this snapshot? This operation cannot be undone.");

    if (res == true) {        
        client.open("GET", "delete_snapshot?host=" + parent.selected_host + "&ref=" + ref + "&vm=" + parent.selected_ref, true);
        client.onreadystatechange = function() {
            if(this.readyState == 4 && this.status == 200) {
                if (this.responseText != "OK") {
                    alert(this.responseText);
                }
                parent.hidePopWin(false);
            } else if (this.readyState == 4 && this.status != 200) {
                parent.document.getElementById("statusbar").innerHTML = "error on_btsnapdelete_activate";
            }            
        }
        client.send(null)    
    }
}
function on_combovmstoragedvd_changed() {
    combovmstoragedvd = document.getElementById("combovmstoragedvd")
    var vm = parent.selected_ref
    var ref = combovmstoragedvd.options[combovmstoragedvd.selectedIndex].value;
   showPopWin('/set_vm_dvd?host=' + selected_host + '&vm=' + vm+ '&ref=' + ref, 520, 300, null);
}

function on_btstgremove_activate() {
    var res = false;
    if (selected_vdi_issnap == "True") {
        res = confirm("Deleting a single snapshot disk is not allowed. This action will delete the entire snapshot, and any other disks attached. This operation cannot be undone. Do you wish continue?");
    } else {
        res = confirm("This will delete this virtual disk permanently destroying the data on it. Continue?");
    }
    if (res == true) {
        var client = new XMLHttpRequest();
        if (selected_vdi_issnap == "True") {
            client.open("GET", "destroy_vm?host=" + selected_host + "&ref=" + selected_vdi_ref + "&destroy_vdi=true&destroy_snap=false&returnOk=True", true);
            client.onreadystatechange = function() {
                if(this.readyState == 4 && this.status == 200) {
                    if (this.responseText != "OK") {
                        alert(this.responseText);
                    }
                    parent.hidePopWin(false);
                } else if (this.readyState == 4 && this.status != 200) {
                    parent.document.getElementById("statusbar").innerHTML = "error on_btstgremove_activate";
                }            
            }
            client.send(null)    
        } else {
            client.open("GET", "delete_vdi?host=" + selected_host + "&ref=" + selected_vdi_ref + "&vm=" + selected_ref, true);
            client.onreadystatechange = function() {
                if(this.readyState == 4 && this.status == 200) {
                    if (this.responseText != "OK") {
                        alert(this.responseText);
                    }
                    parent.hidePopWin(false);
                } else if (this.readyState == 4 && this.status != 200) {
                    parent.document.getElementById("statusbar").innerHTML = "error on_btstgremove_activate";
                }            
            }
            client.send(null)    
        }
    }
        
}
function on_rescanisos_clicked() {
    var client = new XMLHttpRequest();
    client.open("GET", "rescanisos?host=" + selected_host + "&ref=" + selected_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            if (this.responseText != "OK") {
                alert(this.responseText);
            }
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error toggleConfig";
        }            
    }
    client.send(null)    

}
function toogleConfigMaps(el) {
    name = el.name;
    checked = el.checked;
    var client = new XMLHttpRequest();
    client.open("GET", "toggleoptionmaps?option=" + name + "&value=" + checked, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            var obj =  document.getElementById("generatemapimage");
            var src = obj.src;
            var pos = src.indexOf('&v=');
            if (pos >= 0) {
              src = src.substr(0, pos);
            }
            var date = new Date();
            obj.src = src + '&v=' + date.getTime();
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error toggleConfig";
        }            
    }
    client.send(null)    
}


function updateFrameSearch(host, ref) {
    if (selected_tab == "framesearch") {
        var client = new XMLHttpRequest();
        client.open("GET", "fill_vm_search?host=" + parent.selected_host + "&ref=" + ref, true);
        client.onreadystatechange = function(ref) {
            return function() {
                if(this.readyState == 4 && this.status == 200) {
                    response = eval("(" + this.responseText + ")");
                    document.getElementById("row_" + ref).cells[1].getElementsByTagName("IMG")[0].src = response[0][0];
                    document.getElementById("row_" + ref).cells[1].getElementsByTagName("FONT")[0].innerHTML = response[0][1];
                    document.getElementById("row_" + ref).cells[4].innerHTML = response[0][2];
                    document.getElementById("search_" + ref).parentNode.innerHTML = response[1] + '<div id="search_' + ref + '"></div>';
                    setTimeout("updateFrameSearch('" + selected_host + "','" +  ref + "')", 60000);
                } else if (this.readyState == 4 && this.status != 200) {
                    parent.document.getElementById("statusbar").innerHTML = "error updateFrameSearch";
                }            
            }
        }(ref);
        client.send(null);
    }
}

function updatePerformance(interval) {
        var obj = document.getElementById("iframeperformance");
        var src = obj.src;
        var pos = src.indexOf('&interval=');
        if (pos >= 0) {
          src = src.substr(0, pos);
        }
        obj.src = src + '&interval=' + interval;
}


function cancelTask(task_ref) {
    var client = new XMLHttpRequest();
    client.open("GET", "cancel_task?host=" + selected_host + "&task_ref=" + task_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            if (this.responseText != "OK") {
                alert(this.responseText)
            }
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error cancelTask";
        }            
    }
    client.send(null)    
}
