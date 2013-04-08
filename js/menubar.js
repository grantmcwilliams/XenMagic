menubar = new Array();
menubar["pool"] = ["menuitem_pool_new", "menuitem_pool_delete", "menuitem_pool_disconnect","menuitem_pool_prop", "menuitem_pool_backupdb", "menuitem_pool_restoredb", "menuitem_pool_add_server", "menuitem_addserver", "menuitem_disconnectall", "menuitem_connectall", "menuitem_forget", "menuitem_remove", "menuitem_options", "menuitem_migratetool", "menuitem_tools_updatemanager", "menuitem_checkforupdates"];
menubar["home"] = ["menuitem_addserver", "menuitem_connectall", "menuitem_disconnectall", "menuitem_importvm2", "menuitem_options","menuitem_tools_alerts", "menuitem_migratetool"];
menubar["vm"] = ["menuitem_newvm", "menuitem_server_prop", "menuitem_mgmt_ifs", "menuitem_addserver", "menuitem_disconnectall", "menuitem_importvm2", "menuitem_newvm2", "menuitem_vm_prop", "menuitem_stg_new", "menuitem_stg_newvdi", "menuitem_stg_attachvdi", "menuitem_tpl_import", "menuitem_options","menuitem_tools_alerts", "menuitem_takescreenshot", "menuitem_migratetool"] ;
menubar["host"] = ["menuitem_pool_new", "menuitem_addserver", "menuitem_disconnectall", "menuitem_disconnect", "menuitem_forget", "menuitem_remove",  "menuitem_newvm", "menuitem_server_prop", "menuitem_mgmt_ifs", "menuitem_dmesg","menuitem_server_reboot", "menuitem_server_shutdown",  "menuitem_changepw","menuitem_backupserver", "menuitem_restoreserver","menuitem_install_xslic","menuitem_server_add_to_pool", "menuitem_downloadlogs", "menuitem_importvm2", "menuitem_newvm2", "menuitem_stg_new", "menuitem_tpl_import", "menuitem_options","menuitem_tools_alerts", "menuitem_takescreenshot", "menuitem_migratetool", "menuitem_tools_statusreport", "menuitem_tools_updatemanager", "menuitem_checkforupdates", "menuitem_pool_remove_server"];
menubar["server"] = ["menuitem_addserver", "menuitem_disconnectall", "menuitem_connectall", "menuitem_connect", "menuitem_forget", "menuitem_remove", "menuitem_options", "menuitem_migratetool"];
menubar["template"] = ["menuitem_pool_new", "menuitem_addserver", "menuitem_connectall", "menuitem_disconnectall","menuitem_newvm", "menuitem_importvm2", "menuitem_newvm2", "menuitem_stg_new", "menuitem_tpl_newvm", "menuitem_tpl_import", "menuitem_tpl_export", "menuitem_tpl_copy", "menuitem_tpl_delete", "menuitem_options","menuitem_tools_alerts", "menuitem_migratetool"];
menubar["custom_template"] = ["menuitem_pool_new", "menuitem_addserver", "menuitem_connectall", "menuitem_disconnectall","menuitem_newvm", "menuitem_importvm2", "menuitem_newvm2", "menuitem_stg_new", "menuitem_tpl_newvm", "menuitem_tpl_import", "menuitem_tpl_export", "menuitem_tpl_copy", "menuitem_tpl_delete", "menuitem_options","menuitem_tools_alerts", "menuitem_migratetool"];

menubar["storage"] = ["menuitem_pool_new", "menuitem_addserver", "menuitem_connectall", "menuitem_disconnectall","menuitem_newvm", "menuitem_importvm2","menuitem_newvm2", "menuitem_stg_new","menuitem_stg_newvdi", "menuitem_stg_attachvdi", "menuitem_options","menuitem_tools_alerts", "menuitem_migratetool", "menuitem_stg_prop", "menuitem_stg_default", "menuitem_stg_repairstorage", ];



//SuckerTree Horizontal Menu (Sept 14th, 06)
//By Dynamic Drive: http://www.dynamicdrive.com/style/

var menuids=["treemenu1"] //Enter id(s) of SuckerTree UL menus, separated by commas

function buildsubmenus_horizontal(){
for (var i=0; i<menuids.length; i++){
  var ultags=document.getElementById(menuids[i]).getElementsByTagName("ul")
    for (var t=0; t<ultags.length; t++){
        if (ultags[t].parentNode.parentNode.id==menuids[i]){ //if this is a first level submenu
            ultags[t].style.top=ultags[t].parentNode.offsetHeight+"px" //dynamically position first level submenus to be height of main menu item
            ultags[t].parentNode.getElementsByTagName("a")[0].className="mainfoldericon"
        }
        else{ //else if this is a sub level menu (ul)
          ultags[t].style.left=ultags[t-1].getElementsByTagName("a")[0].offsetWidth+"px" //position menu to the right of menu item that activated it
        ultags[t].parentNode.getElementsByTagName("a")[0].className="subfoldericon"
        }
    ultags[t].parentNode.onmouseover=function(){
    this.getElementsByTagName("ul")[0].style.visibility="visible"
    }
    ultags[t].parentNode.onmouseout=function(){
    this.getElementsByTagName("ul")[0].style.visibility="hidden"
    }
    }
  }
}

if (window.addEventListener)
window.addEventListener("load", buildsubmenus_horizontal, false)
else if (window.attachEvent)
window.attachEvent("onload", buildsubmenus_horizontal)


function update_menubar() {
    if (selected_type == "vm") {
        menubar["vm"] = ["menuitem_newvm", "menuitem_server_prop", "menuitem_mgmt_ifs", "menuitem_addserver", "menuitem_disconnectall", "menuitem_importvm2", "menuitem_newvm2", "menuitem_vm_prop", "menuitem_stg_new", "menuitem_stg_newvdi", "menuitem_stg_attachvdi", "menuitem_tpl_import", "menuitem_options","menuitem_tools_alerts", "menuitem_takescreenshot", "menuitem_migratetool", "menuitem_vm_copy"];
        for (op in selected_actions) {
             menubar["vm"].push("menuitem_vm_" + selected_actions[op]);
        }
        if (selected_state == "Running") {
            menubar["vm"].push("menuitem_vm_install_xs_tools");
        } else {
            menubar["vm"].push("menuitem_vm_startrecovery");
            menubar["vm"].push("menuitem_vm_copy");
        }
    } 
    if (selected_type == "storage") {
        menubar["storage"] = ["menuitem_pool_new", "menuitem_addserver", "menuitem_connectall", "menuitem_disconnectall","menuitem_newvm", "menuitem_importvm2","menuitem_newvm2", "menuitem_stg_new","menuitem_stg_newvdi", "menuitem_stg_attachvdi", "menuitem_options","menuitem_tools_alerts", "menuitem_migratetool", "menuitem_stg_prop", "menuitem_stg_default", "menuitem_stg_repairstorage", ];
        for (op in selected_actions) {
            if (document.getElementById("menuitem_stg_" + selected_actions[op])) {    
                menubar["storage"].push("menuitem_stg_" + selected_actions[op]);
            }
        }
    }
    if (selected_type == "host") {
        menubar["host"] = ["menuitem_pool_new", "menuitem_addserver", "menuitem_disconnectall", "menuitem_disconnect", "menuitem_forget", "menuitem_remove",  "menuitem_newvm", "menuitem_server_prop", "menuitem_mgmt_ifs", "menuitem_dmesg","menuitem_server_reboot", "menuitem_server_shutdown",  "menuitem_changepw","menuitem_backupserver", "menuitem_restoreserver","menuitem_install_xslic","menuitem_server_add_to_pool", "menuitem_downloadlogs", "menuitem_importvm2", "menuitem_newvm2", "menuitem_stg_new", "menuitem_tpl_import", "menuitem_options","menuitem_tools_alerts", "menuitem_takescreenshot", "menuitem_migratetool", "menuitem_tools_statusreport", "menuitem_tools_updatemanager", "menuitem_checkforupdates", "menuitem_pool_remove_server"];
        for (op in selected_actions) {
            if (selected_actions[op] == "enable") {
                menubar["host"].push("menuitem_exitmaintenancemode");
            }
            else {
                if (selected_actions[op] == "disable") {
                    menubar["host"].push("menuitem_entermaintenancemode");
                }
            }
        }
    }
    menu = document.getElementById("treemenu1");
    for (children in menu.childNodes) {
        if (menu.childNodes[children].nodeName == "LI") {
            elements = menu.childNodes[children].getElementsByTagName("li")
            for (element=0; element < elements.length; element++) { 
                if (elements[element].getAttribute("id")) {
                    if (elements[element].getAttribute("id").substring(0, 8) == "menuitem" && elements[element].getAttribute("id") != "menuitem_options" ) {
                        if (elements[element].getAttribute("id") in oc(menubar[selected_type])) {
                            elements[element].setAttribute("class", "");
                            elements[element].disabled = false;
                            link = elements[element].getElementsByTagName("A")[0];
                            link.disabled = false;
                            if (link.getAttribute("onClick") == undefined) {
                                link.setAttribute("onClick", link.getAttribute("onclick_bak"));
                                link.removeAttribute("onclick_bak");
                            }
                        } else {
                            elements[element].setAttribute("class", "disabled");
                            link = elements[element].getElementsByTagName("A")[0];
                            if (link.getAttribute("onClick") != undefined) {
                                link.setAttribute("onclick_bak", link.getAttribute("onClick"));
                                link.removeAttribute("onClick")
                                link.disabled = true;
                            }
                        }
                    }
                }
            }
        }
    }
    document.getElementById("menuitem_options").setAttribute("class", "");
}

/**
 * *
 * *  Javascript trim, ltrim, rtrim
 * *  http://www.webtoolkit.info/
 * *
 * **/
 
function trim(str, chars) {
        return ltrim(rtrim(str, chars), chars);
}
 
function ltrim(str, chars) {
        chars = chars || "\\s";
        return str.replace(new RegExp("^[" + chars + "]+", "g"), "");
}
 
function rtrim(str, chars) {
        chars = chars || "\\s";
        return str.replace(new RegExp("[" + chars + "]+$", "g"), "");
}

function toogleConfig(el) {
    id = el.parentNode.id;
    if (trim(el.innerHTML).substring(1,2) == "x") {
        el.innerHTML = el.innerHTML.replace("[x]", "[ ]")
        checked = false;    
        if (id == "show_toolbar") {
            document.getElementById("toolbar").style.display = "none";
        } 

    } else {
        el.innerHTML = el.innerHTML.replace("[ ]", "[x]")
        checked = true;    
        if (id == "show_toolbar") {
            document.getElementById("toolbar").style.display = "";
        } 
    }

    var client = new XMLHttpRequest();
    client.open("GET", "toggleoption?option=" + id + "&value=" + checked, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            if (id != "show_toolbar") {
                update_vmtree();
            }
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error toggleConfig";
        }            
    }
    client.send(null)    
}


function fillMigrateServers() {
    var client = new XMLHttpRequest();
    client.open("GET", "wherecanmigrate?host=" + selected_host + "&ref=" + selected_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            document.getElementById("menu_vm_migrate").innerHTML = '<li><a href="#" style="cursor: pointer;">Servers</a></li><li><a href="#"><hr /></a></li> ' + this.responseText;
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error fillMigrateServers";
        }            
    }
    client.send(null)    
}
function fillStartServers() {
    var client = new XMLHttpRequest();
    client.open("GET", "wherecanstart?host=" + selected_host + "&ref=" + selected_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            document.getElementById("menu_vm_start_on").innerHTML = '<li><a href="#" style="cursor: pointer;">Servers</a></li><li><a href="#"><hr /></a></li> ' + this.responseText;
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error fillStartServers";
        }            
    }
    client.send(null)    
}
function fillResumeServers() {
    var client = new XMLHttpRequest();
    client.open("GET", "wherecanresume?host=" + selected_host + "&ref=" + selected_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            document.getElementById("menu_vm_resume_on").innerHTML = '<li><a href="#" style="cursor: pointer;">Servers</a></li><li><a href="#"><hr /></a></li> ' + this.responseText;
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error fillResumeServers";
        }            
    }
    client.send(null)    
}

function fillAddServersToPool() {
    var client = new XMLHttpRequest();
    client.open("GET", "availableservers?host=" + selected_host + "&ref=" + selected_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            document.getElementById("menu_add_server").innerHTML = '<li><a href="#" style="cursor: pointer;">Servers</a></li><li><a href="#"><hr /></a></li> ' + this.responseText;
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error fillAddServersToPool";
        }            
    }
    client.send(null)    
}
function fillPoolsToAddToPool() {
    var client = new XMLHttpRequest();
    client.open("GET", "availablepools?host=" + selected_host + "&ref=" + selected_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            document.getElementById("menu_server_add_to_pool").innerHTML = '<li><a href="#" style="cursor: pointer;">Pools</a></li><li><a href="#"><hr /></a></li> ' + this.responseText;
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error fillPoolsToAddToPool";
        }            
    }
    client.send(null)    
}

function on_menuitem_stg_forget_clicked() {
    res = confirm("Forgetting this storage repository will permanently remove the information used to connect the virtual machines to the virtual disks in the storage repository.  The contents of the virtual disks themselves will remain intact.\n\nAre you sure you want to forget this storage repository? This operation cannot be undone.");
    if (res == true) {
        showPopWin('/forget_storage?host=' + selected_host + '&ref=' + selected_ref, 580, 450, null);
    }
}

function on_menuitem_stg_unplug_clicked() {
    res = confirm("Detaching this storage repository will make the virtual disks that it contains inaccessible. The contents of the virtual disks themselves will remain intact.\n\nIf you subsequently reattach the storage repository, you will need to provide the correct device configuration details.\n\nAre you sure you want to detach this storage repository?");
    if (res == true) {
        showPopWin('/unplug_storage?host=' + selected_host + '&ref=' + selected_ref, 580, 450, null);
    }
}
function on_menuitem_stg_destroy_clicked() {
    res = confirm("Destroying this storage repository will permanently remove all associated virtual disks from the underlying storage device.\n\n\nAre you sure you want to destroy this storage repository? This operation cannot be undone.");
    if (res == true) {
        showPopWin('/destroy_storage?host=' + selected_host + '&ref=' + selected_ref, 580, 450, null);
    }
}

