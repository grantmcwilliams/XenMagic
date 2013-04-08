var pagenumber = 0;
var reattach_ref = "";
function goPrevious() {
    document.getElementById("newstg" + pagenumber).style.display = "none";
    document.getElementById("newstg0").style.display = ""; 
    document.getElementById("previousnewstorage").disabled  = true;
    document.getElementById("nextnewstorage").disabled = false;
    document.getElementById("finishnewstorage").disabled = true;
    document.getElementById("lblnewstg0").style.backgroundColor = "#d5e5f7";
    document.getElementById("lblnewstg1").style.backgroundColor = "";
}

function goNext() {
    for (var i = 0; i < document.getElementsByName("radionewstg").length; i++) {
        if (document.getElementsByName("radionewstg")[i].checked) {
            pagenumber = i + 1;
        }
    }
    if (pagenumber == 3) {
        document.getElementById("loadinghba").style.display = "";
        var client = new XMLHttpRequest();
        client.open("GET", "fill_hw_hba?host=" + parent.selected_ip + "&ref=" + parent.selected_ref, true);
        client.onreadystatechange = function() {
             return function() {
                if(this.readyState == 4 && this.status == 200) {
                    document.getElementById("loadinghba").style.display = "none";
                    if(this.responseText == "ERROR") {
                        alert("No LUNs were found. Please verify your hardware configuration");
                    } else {
                        document.getElementById("treehbalun").innerHTML = this.responseText;
                    }
                } else if (this.readyState == 4 && this.status != 200) {
                    document.getElementById("statusbar").innerHTML = "error goNext - hba";
                }
            }
        }();
        client.send(null);

    }
    if (pagenumber != 4 && pagenumber != 5) {
        document.getElementById("newstg" + pagenumber).style.display = "";
        document.getElementById("newstg0").style.display = "none"; 
        document.getElementById("previousnewstorage").disabled  = false;
        document.getElementById("nextnewstorage").disabled = true;
        document.getElementById("finishnewstorage").disabled = true;
        document.getElementById("lblnewstg0").style.backgroundColor = "";
        document.getElementById("lblnewstg1").style.backgroundColor = "#d5e5f7";
    }
}
function update_sr_desc(id) {
    var descs = new Array();
    descs["radionewstgnfsvhd"] = "NFS servers are a common form of shared filesystem infrastructure, and can be used as a storage repository substrate for virtual disks.<br><br>As NFS storage repositories are shared, the virtual disks stored in them allow VMs to be started on any server in a resource pool and to be migrated between them using XenMotion.<br><br>When you configure an NFS storage repository, you simply provide the hostname or IP address of the NFS server and the path to a directory that will be used to contain the storage repository. The NFS server must be configured to export the specified path to all servers in the pool";
    descs["radionewstgiscsi"] = "Shared Logical Volume Manager (LVM) support is available using either iSCSI or Fibre Channel access to a shared LUN.<br><br>Using the LVM-based shared SR provides the same performance benefits as unshared LVM for local disk storage, however in the shared context, iSCSI or Fibre Channel-based SRs enable VM agility -- VMs may be started on any server in a pool and migrated between them.";
    descs["radionewstghwhba"] = "XenServer Hosts support Fibre Channel (FC) storage area networks (SANs) through Emulex or QLogic host bus adapters (HBAs).<br><br>All FC configuration required to expose a FC LUN to the host must be completed manually, including storage devices, network devices, and the HBA within the XenServer host.<br><br>Once all FC configuration is complete the HBA will expose a SCSI device backed by the FC LUN to the host. The SCSI device can then be used to access to the FC LUN as if it were a locally attached SCSI device.";
    descs["radionewstgnetapp"] = "Main developer of xenwebmanager hasn't NetApp and hasn't Essentials";
    descs["radionewstgdell"] = "Main developer of xenwebmanager hasn't Dell EqualLogic and hasn't Essentials";
    descs["radionewstgcifs"] =  "Select this option if you have a library of VM installation ISO images available as a Windows File Sharing share that you wish to attach to your host or pool.";
    descs["radionewstgnfsiso"] = "Select this option if you have a library of VM installation ISO images available as a NFS share that you wish to attach to your host or pool.";
    descs["radionewstgaoe"] = "ATA over Ethernet (AoE) is a network protocol designed for simple, high-performance access of SATA storage devices over Ethernet networks. It gives the possibility to build SANs with low-cost, standard technologies.";
    document.getElementById("srdesc").innerHTML = descs[id];

}
function on_btnewstgsnfsscan_clicked() {
    share = document.getElementById("txtnewstgnfspath").value;
    options = document.getElementById("txtnewstgnfsoptions").value;
    var client = new XMLHttpRequest();
    client.open("GET", "scan_nfs_vhd?host=" + parent.selected_ip + "&ref=" + parent.selected_ref + "&share=" + share + "&options=" + options, true);
    document.getElementById("loadingnfs").style.display = "";
    client.onreadystatechange = function() {
         return function() {
            if(this.readyState == 4 && this.status == 200) {
                if(this.responseText) {
                    document.getElementById("loadingnfs").style.display = "none";
                    result = eval('(' + this.responseText + ')');
                    ClearOptionsFast("treereattachnewstgnfs");
                    if (result[1] == 1) {
                        document.getElementById("radioreattachsr").disabled = true;
                        document.getElementById("finishnewstorage").disabled = false;
                    } else {
                        if (result[1] == 2) {
                            document.getElementById("radioreattachsr").disabled = false;
                            document.getElementById("finishnewstorage").disabled = false;
                            treereattachnewstgnfs = document.getElementById("treereattachnewstgnfs");
                            for (var i = 0; i < result[0].length; i++) {
                                addOption(treereattachnewstgnfs,  result[0][i],  result[0][i]);
                            }
                            treereattachnewstgnfs.selectedIndex = 0;
                        } else {
                            document.getElementById("radioreattachsr").disabled = true;
                            document.getElementById("finishnewstorage").disabled = true;
                            alert(result[2]);
                        }
                    }
                }
            } else if (this.readyState == 4 && this.status != 200) {
                document.getElementById("statusbar").innerHTML = "error on_btnewstgsnfsscan_clicked";
            }
        }
    }();
    client.send(null);
}
function addOption(select, text, value) {
    var elOptNew = document.createElement('option');
    elOptNew.text = text; //result[0][i];
    elOptNew.value = value; //result[0][i];
    try {
      select.add(elOptNew, null); // standards compliant; doesn't work in IE
    }
    catch(ex) {
      select.add(elOptNew); // IE only
    }

}
function on_finishnewstorage_clicked() {
    if (pagenumber == 1) {
        name = document.getElementById("txtnewstgnfsname").value;
        share = document.getElementById("txtnewstgnfspath").value;
        options = document.getElementById("txtnewstgnfsoptions").value;
        create = document.getElementById("radiocreatenewsr").checked;
        treereattachnewstgnfs = document.getElementById("treereattachnewstgnfs");
        if (!create) {
            var r=confirm("Warning: you must ensure that the SR is not in use by any server not connected to XenCenter. Failure to do so may result in data loss.\n\nSR: " + treereattachnewstgnfs.options[treereattachnewstgnfs.selectedIndex].value + "\n\nDo you want to reattach the SR?");
            if (r == true) {
                uuid = treereattachnewstgnfs.options[treereattachnewstgnfs.selectedIndex].value;
                var client = new XMLHttpRequest();
                client.open("GET", "reattach_nfs_vhd?host=" + parent.selected_ip + "&ref=" + parent.selected_ref + "&name=" + name + "&share=" + share + "&options=" + options + "&uuid=" + uuid, true);
                client.onreadystatechange = function() {
                     return function() {
                        if(this.readyState == 4 && this.status == 200) {
                            if(this.responseText == "OK") {
                                parent.hidePopWin(false);
                            } else {
                                alert(this.responseText);
                            }
                        } else if (this.readyState == 4 && this.status != 200) {
                            document.getElementById("statusbar").innerHTML = "error on_finishnewstorage_clicked";
                        }
                    }
                }();
                client.send(null);

            }
        } else {
            var client = new XMLHttpRequest();
            client.open("GET", "create_nfs_vhd?host=" + parent.selected_ip + "&ref=" + parent.selected_ref + "&name=" + name + "&share=" + share + "&options=" + options, true);
            client.onreadystatechange = function() {
                 return function() {
                    if(this.readyState == 4 && this.status == 200) {
                        if(this.responseText == "OK") {
                            parent.hidePopWin(false);
                        } else {
                            alert(this.responseText);
                        }
                    } else if (this.readyState == 4 && this.status != 200) {
                        document.getElementById("statusbar").innerHTML = "error on_finishnewstorage_clicked";
                    }
                }
            }();
            client.send(null);

        }
    } else if (pagenumber == 2) {
        var client = new XMLHttpRequest();
        name = document.getElementById("txtiscsiname").value;
        target = document.getElementById("txtiscsitarget").value;
        iscsiport = document.getElementById("txtiscsiport").value;
        if (document.getElementById("checkscsichap").checked) {
            user = document.getElementById("txtiscsichapuser").value;
            password = document.getElementById("txtiscsichapsecret").value;
        }  else {
            user = ""
            password = ""
        }
        combotargetiqn = document.getElementById("combotargetiqn")
        targetiqn = combotargetiqn.options[combotargetiqn.selectedIndex].value;
        combotargetlun = document.getElementById("combotargetlun")
        targetlun = combotargetlun.options[combotargetlun.selectedIndex].value;
        document.getElementById("loadingiscsi").style.display = "";

        params = "&name=" + name + "&target=" + target + "&iscsiport=" + iscsiport + "&user=" + user + "&password=" + password;
        params += "&targetiqn=" + targetiqn + "&targetlun=" + targetlun;
        client.open("GET", "check_iscsi?host=" + parent.selected_ip + "&ref=" + parent.selected_ref + params, true);
        client.onreadystatechange = function() {
             return function() {
                if(this.readyState == 4 && this.status == 200) {
                    document.getElementById("loadingiscsi").style.display = "none";
                    reattach_ref = this.responseText;
                    if (reattach_ref) {
                        showPopWin("confirmiscsi.html", 400, 200, null);
                    } else {
                        var r = confirm("Creating a new virtual disk on this LUN will destroy any data present. You must ensure that no other system is using the LUN, including any XenServers, or the virtual disk may become corrupted while in use.\n\nDo you wish to format the disk?");
                        if (r == true) {
                           on_acceptformatiscsidisk_clicked(); 
                        }
                    }
                } else if (this.readyState == 4 && this.status != 200) {
                    document.getElementById("statusbar").innerHTML = "error on_finishnewstorage_clicked";
                }
            }
        }();
        client.send(null);
    } else if (pagenumber == 3) {
        document.getElementById("loadinghba").style.display = "";
        var client = new XMLHttpRequest();
        params = "&uuid=" + selected_hba_id + "&text=" + selected_hba_ref;
        client.open("GET", "check_hardware_hba?host=" + parent.selected_ip + "&ref=" + parent.selected_ref + params, true);
        client.onreadystatechange = function() {
             return function() {
                if(this.readyState == 4 && this.status == 200) {
                    res = eval("(" + this.responseText + ")");
                    document.getElementById("loadinghba").style.display = "none";
                    if (res[0] == 0) {
                        res = confirm("Creating a new virtual disk on this LUN will destroy any data present. You must ensure that no other system is using the LUN, including any XenServers, or the virtual disk may become corrupted while in use.\n\nDo you wish format the disk?");
                        if (res == true)  {
                            on_accepformatdisklun_clicked();
                        }
                    } else if (res[0] == 1) {
                        alert("The SR '" + res[1] + "' is in use on '" + res[2] + "' and cannot be introduced.  You must detach the SR from '" + res[2] + "' before using it again.");
                    } else if (res[0] == 2) {
                        confirm("Warning: to prevent data loss you must ensure that the LUN is not in use by any other system, including XenServer hosts that are not connected to XenCenter.\n\n  SR: '" + res[1] + "'\n\n Do you want to reattach the SR?");
                        if (res == true) {
                            on_acceptreattachhbalun_clicked();
                        }
                    } else if (res[0] == 3) {
                        showPopWin("reattachformathbalun?sr=" + res[1], 400, 200, null);
                    }
                } else if (this.readyState == 4 && this.status != 200) {
                    document.getElementById("statusbar").innerHTML = "error on_finishnewstorage_clicked";
                }
            }
        }();
        client.send(null);
 
    } else if (pagenumber == 6) {
        var client = new XMLHttpRequest();
        name = document.getElementById("txtnewstgcifsname").value;
        sharename = document.getElementById("txtnewstgcifspath").value;
        options = document.getElementById("txtnewstgcifsoptions").value;
        if (document.getElementById("checknewstgcifslogin").checked) {
            username = document.getElementById("txtnewstgcifsusername").value;
            password = document.getElementById("txtnewstgcifspassword").value;
        } else {
            username = "";
            password = "";
        }
        params = "&name=" + name + "&sharename=" + sharename+ "&options=" + options + "&username=" + username + "&password=" + password;
        if (!document.getElementById("stgtype")) {
            client.open("GET", "create_cifs_iso?host=" + parent.selected_ip + "&ref=" + parent.selected_ref + params, true);
        } else {
            client.open("GET", "reattach_cifs_iso?host=" + parent.selected_ip + "&ref=" + parent.selected_ref + params, true);
        }
        client.onreadystatechange = function() {
             return function() {
                if(this.readyState == 4 && this.status == 200) {
                    if (this.responseText == "OK") {
                        parent.hidePopWin(false);
                    } else {
                        alert(this.responseText);
                    }
                } else if (this.readyState == 4 && this.status != 200) {
                    document.getElementById("statusbar").innerHTML = "error on_finishnewstorage_clicked";
                }
            }
        }();
        client.send(null);
        
    } else if (pagenumber == 7) {
        var client = new XMLHttpRequest();
        name = document.getElementById("txtnewstgnfsisoname").value;
        sharename = document.getElementById("txtnewstgnfsisopath").value;
        options = document.getElementById("txtnewstgnfsisooptions").value;
        params = "&name=" + name + "&sharename=" + sharename+ "&options=" + options;
        if (!document.getElementById("stgtype")) {
            client.open("GET", "create_nfs_iso?host=" + parent.selected_ip + "&ref=" + parent.selected_ref + params, true);
        } else {
            client.open("GET", "reattach_nfs_iso?host=" + parent.selected_ip + "&ref=" + parent.selected_ref + params, true);

        }

        client.onreadystatechange = function() {
             return function() {
                if(this.readyState == 4 && this.status == 200) {
                    if (this.responseText == "OK") {
                        parent.hidePopWin(false);
                    } else {
                        alert(this.responseText);
                    }
                } else if (this.readyState == 4 && this.status != 200) {
                    document.getElementById("statusbar").innerHTML = "error on_finishnewstorage_clicked";
                }
            }
        }();
        client.send(null);


    }

}
function on_acceptformatiscsidisk_clicked() {
        var client = new XMLHttpRequest();
        name = document.getElementById("txtiscsiname").value;
        target = document.getElementById("txtiscsitarget").value;
        iscsiport = document.getElementById("txtiscsiport").value;
        if (document.getElementById("checkscsichap").checked) {
            user = document.getElementById("txtiscsichapuser").value;
            password = document.getElementById("txtiscsichapsecret").value;
        }  else {
            user = ""
            password = ""
        }
        combotargetiqn = document.getElementById("combotargetiqn")
        targetiqn = combotargetiqn.options[combotargetiqn.selectedIndex].value;
        combotargetlun = document.getElementById("combotargetlun")
        targetlun = combotargetlun.options[combotargetlun.selectedIndex].value;
        document.getElementById("loadingiscsi").style.display = "";

        params = "&name=" + name + "&target=" + target + "&iscsiport=" + iscsiport + "&user=" + user + "&password=" + password;
        params += "&targetiqn=" + targetiqn + "&targetlun=" + targetlun;
        client.open("GET", "create_iscsi?host=" + parent.selected_ip + "&ref=" + parent.selected_ref + params, true);
        client.onreadystatechange = function() {
             return function() {
                if(this.readyState == 4 && this.status == 200) {
                    document.getElementById("loadingiscsi").style.display = "none";
                    if(this.responseText == '"OK"') {
                        hidePopWin(false);
                        parent.hidePopWin(false);
                    } else {
                        alert(this.responseText);
                    }
                } else if (this.readyState == 4 && this.status != 200) {
                    document.getElementById("statusbar").innerHTML = "error on_finishnewstorage_clicked";
                }
            }
        }();
        client.send(null);

}

function on_reattachscsidisk_clicked() {
        var client = new XMLHttpRequest();
        name = document.getElementById("txtiscsiname").value;
        target = document.getElementById("txtiscsitarget").value;
        iscsiport = document.getElementById("txtiscsiport").value;
        if (document.getElementById("checkscsichap").checked) {
            user = document.getElementById("txtiscsichapuser").value;
            password = document.getElementById("txtiscsichapsecret").value;
        }  else {
            user = ""
            password = ""
        }
        combotargetiqn = document.getElementById("combotargetiqn")
        targetiqn = combotargetiqn.options[combotargetiqn.selectedIndex].value;
        combotargetlun = document.getElementById("combotargetlun")
        targetlun = combotargetlun.options[combotargetlun.selectedIndex].value;
        document.getElementById("loadingiscsi").style.display = "";

        params = "&name=" + name + "&target=" + target + "&iscsiport=" + iscsiport + "&user=" + user + "&password=" + password;
        params += "&targetiqn=" + targetiqn + "&targetlun=" + targetlun + "&reattach_ref=" + reattach_ref;
        client.open("GET", "reattach_iscsi?host=" + parent.selected_ip + "&ref=" + parent.selected_ref + params, true);
        client.onreadystatechange = function() {
             return function() {
                if(this.readyState == 4 && this.status == 200) {
                    document.getElementById("loadingiscsi").style.display = "none";
                    if(this.responseText == '"OK"') {
                        hidePopWin(false);
                        parent.hidePopWin(false);
                    } else {
                        alert(this.responseText);
                    }
                } else if (this.readyState == 4 && this.status != 200) {
                    document.getElementById("statusbar").innerHTML = "error on_reattachscsidisk_clicked";
                }
            }
        }();
        client.send(null);
}

function on_checkscsichap_checked() {
    checkscsichap = document.getElementById("checkscsichap");
    if (checkscsichap.checked) {
        document.getElementById("framescsichap").style.display = "";
    } else {
        document.getElementById("framescsichap").style.display = "none";
    }
}

function on_btdiscoveriqns_clicked() {
    var client = new XMLHttpRequest();
    target = document.getElementById("txtiscsitarget").value;
    iscsiport = document.getElementById("txtiscsiport").value;
    if (document.getElementById("checkscsichap").checked) {
        user = document.getElementById("txtiscsichapuser").value;
        password = document.getElementById("txtiscsichapsecret").value;
    }  else {
        user = ""
        password = ""
    }
    document.getElementById("loadingiscsi").style.display = "";
    params = "&target=" + target + "&iscsiport=" + iscsiport + "&user=" + user + "&password=" + password;
    client.open("GET", "fill_iscsi_target_iqn?host=" + parent.selected_ip + "&ref=" + parent.selected_ref + params, true);
    client.onreadystatechange = function() {
         return function() {
            if(this.readyState == 4 && this.status == 200) {
                result = eval('(' + this.responseText + ')');
                document.getElementById("loadingiscsi").style.display = "none";
                if (result[0]) {
                    ClearOptionsFast("combotargetiqn");
                    for (var index in  result[1]) {
                        row = result[1][index]
                        addOption(document.getElementById("combotargetiqn"),  row[1],  row[0]);
                    }
                    document.getElementById("combotargetiqn").disabled = false;
                    document.getElementById("btdiscoverluns").disabled = false;
                    document.getElementById("combotargetlun").disabled = true;
                    document.getElementById("btdiscoverluns").focus();
                } else {
                    alert("Scanning for IQNs on iSCSI filer " + target + "\n\nUnable to connect to ISCSI service on target\nCheck your settings and try again")
                    document.getElementById("combotargetiqn").disabled = true;
                    document.getElementById("combotargetlun").disabled = true;
                    document.getElementById("btdiscoverluns").disabled = true;
                }
            } else if (this.readyState == 4 && this.status != 200) {
                document.getElementById("statusbar").innerHTML = "error on_finishnewstorage_clicked";
            }
        }
    }();
    client.send(null);
}

function on_btdiscoverluns_clicked() {
    var client = new XMLHttpRequest();
    target = document.getElementById("txtiscsitarget").value;
    iscsiport = document.getElementById("txtiscsiport").value;
    if (document.getElementById("checkscsichap").checked) {
        user = document.getElementById("txtiscsichapuser").value;
        password = document.getElementById("txtiscsichapsecret").value;
    }  else {
        user = ""
        password = ""
    }
    combotargetiqn = document.getElementById("combotargetiqn")
    targetiqn = combotargetiqn.options[combotargetiqn.selectedIndex].value;

    document.getElementById("loadingiscsi").style.display = "";

    params = "&target=" + target + "&iscsiport=" + iscsiport + "&user=" + user + "&password=" + password + "&targetiqn=" + targetiqn;
    client.open("GET", "fill_iscsi_target_lun?host=" + parent.selected_ip + "&ref=" + parent.selected_ref + params, true);
    client.onreadystatechange = function() {
         return function() {
            if(this.readyState == 4 && this.status == 200) {
                result = eval('(' + this.responseText + ')');
                document.getElementById("loadingiscsi").style.display = "none";
                if (result[0]) {
                    ClearOptionsFast("btdiscoverluns");
                    if (!result[1].length) {
                        alert("Scanning for LUNs on iSCSI filer " + target + "\n\nNo LUNs were found on " + target + "\nCheck your settings and try again")
                    } else {
                        for (var index in  result[1]) {
                            row = result[1][index]
                            addOption(document.getElementById("combotargetlun"),  row[1],  row[0]);
                        }
                        document.getElementById("combotargetiqn").disabled = false;
                        document.getElementById("btdiscoverluns").disabled = false;
                        document.getElementById("combotargetlun").disabled = false;
                        document.getElementById("btdiscoverluns").disabled = false;
                        document.getElementById("finishnewstorage").disabled = false;
                        document.getElementById("finishnewstorage").focus();
                    } 
                } else {
                    alert("Scanning for IQNs on iSCSI filer " + target + "\n\nUnable to connect to ISCSI service on target\nCheck your settings and try again")
                    document.getElementById("combotargetiqn").disabled = true;
                    document.getElementById("combotargetlun").disabled = true;
                    document.getElementById("btdiscoverluns").disabled = true;
                    document.getElementById("finishnewstorage").disabled = true;
                }
            } else if (this.readyState == 4 && this.status != 200) {
                document.getElementById("statusbar").innerHTML = "error on_finishnewstorage_clicked";
            }
        }
    }();
    client.send(null);

}

function checkcifspath() {
    var re = new RegExp(document.getElementById("regexp").value);
    sharename = document.getElementById("txtnewstgcifspath").value;
    name = document.getElementById("txtnewstgcifsname").value;
    if (sharename.match(re) && name.length) {
        document.getElementById("finishnewstorage").disabled = false ;
    } else {
        document.getElementById("finishnewstorage").disabled = true;
    }
}

function checknfspath() {
    var re = new RegExp(document.getElementById("regexp2").value);
    sharename = document.getElementById("txtnewstgnfsisopath").value;
    name = document.getElementById("txtnewstgnfsisoname").value;
    if (sharename.match(re) && name.length) {
        document.getElementById("finishnewstorage").disabled = false ;
    } else {
        document.getElementById("finishnewstorage").disabled = true;
    }
}
function ClearOptionsFast(id)
{
    var selectObj = document.getElementById(id);
    var selectParentNode = selectObj.parentNode;
    var newSelectObj = selectObj.cloneNode(false); // Make a shallow copy
    selectParentNode.replaceChild(newSelectObj, selectObj);
    return newSelectObj;
}

var selected_hba_ref = "";
var selected_hba_id = "";
var selected_hba_path = "";
function selectHbaRow(ref, id, path) {
    document.getElementById("finishnewstorage").disabled = false;
    if (selected_hba_ref && document.getElementById(selected_hba_ref)) {
        document.getElementById(selected_hba_ref).style.backgroundColor = selected_hba_color
    }
    selected_hba_ref = ref;
    selected_hba_id = id;
    selected_hba_path = path;
    selected_hba_color =  document.getElementById(selected_hba_ref).style.backgroundColor;
    document.getElementById(selected_hba_ref).style.backgroundColor = "#3366CC";
}

function on_accepformatdisklun_clicked() {
        var client = new XMLHttpRequest();
        name = document.getElementById("txtihbaname").value;
        params = "&uuid=" + selected_hba_id + "&path=" + selected_hba_path + "&name=" + name;
        client.open("GET", "format_hardware_hba?host=" + parent.selected_ip + "&ref=" + parent.selected_ref + params, true);
        client.onreadystatechange = function() {
             return function() {
                if(this.readyState == 4 && this.status == 200) {
                    if (this.responseText == "OK") {
                        parent.hidePopWin(false);
                    } else {
                        alert(this.responseText);
                    }
                } else if (this.readyState == 4 && this.status != 200) {
                    document.getElementById("statusbar").innerHTML = "error on_accepformatdisklun_clicked";
                }
            }
        }();
        client.send(null);
}

function on_acceptreattachhbalun_clicked() {
        var client = new XMLHttpRequest();
        name = document.getElementById("txtihbaname").value;
        params = "&uuid=" + selected_hba_id + "&path=" + selected_hba_path + "&name=" + name;
        client.open("GET", "reattach_hardware_hba?host=" + parent.selected_ip + "&ref=" + parent.selected_ref + params, true);
        client.onreadystatechange = function() {
             return function() {
                if(this.readyState == 4 && this.status == 200) {
                    if (this.responseText == "OK") {
                        parent.hidePopWin(false);
                    } else {
                        alert(this.responseText);
                    }
                } else if (this.readyState == 4 && this.status != 200) {
                    document.getElementById("statusbar").innerHTML = "error on_acceptreattachhbalun_clicked";
                }
            }
        }();
        client.send(null);
}

function on_acceptareattachformathbalun_clicked() {
        var client = new XMLHttpRequest();
        name = document.getElementById("txtihbaname").value;
        params = "&uuid=" + selected_hba_id + "&path=" + selected_hba_path + "&name=" + name;
        client.open("GET", "reattach_and_introduce_hardware_hba?host=" + parent.selected_ip + "&ref=" + parent.selected_ref + params, true);
        client.onreadystatechange = function() {
             return function() {
                if(this.readyState == 4 && this.status == 200) {
                    if (this.responseText == "OK") {
                        parent.hidePopWin(false);
                    } else {
                        alert(this.responseText);
                    }
                } else if (this.readyState == 4 && this.status != 200) {
                    document.getElementById("statusbar").innerHTML = "error reattach_and_introduce_hardware_hba";
                }
            }
        }();
        client.send(null);
}
