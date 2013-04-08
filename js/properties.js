var selected_page = "tabprop0";
var selected_prop = "lblprop0";
var selected_vdi_ref = "";
var selected_host_ref = "";

function on_btvmpropaccept_accept() {
    prop = new Object();
    var type = document.getElementById("type").value;
    var ref = document.getElementById("ref").value;
    prop["txtpropvmname"] = document.getElementById("txtpropvmname").value;
    prop["txtpropvmdesc"] = document.getElementById("txtpropvmdesc").value;
    customfields = document.getElementsByName("cstmvalues");
    custom = new Object();
    for (var i=0; i < customfields.length; i++) {
        custom[customfields[i].getAttribute("id")] = customfields[i].value;
    }
    prop["customfields"] = custom;
    var client = new XMLHttpRequest();
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            if (this.responseText != "OK") {
                alert(this.responseText);
            } else {
                parent.on_tabbox_focus_tab(null, parent.selected_tab);
                parent.hidePopWin(false); 
            }
        } else if (this.readyState == 4 && this.status != 200 && this.status != 0) {
            alert("Error on set_properties()");
        }
    }

    if (type == "server" || type == "host") {
        prop["radiologlocal"] = document.getElementById("radiologlocal").checked;
        prop["txtlogserver"] = document.getElementById("txtlogserver").value;
    }
    if (type == "hostnetwork") {
        prop["checknetworkautoadd"] = document.getElementById("checknetworkautoadd").checked;
    } 
    if (type == "vm" || type == "template" || type == "custom_template") {
        prop["spinpropvmmem"] = document.getElementById("spinpropvmmem").value;
        prop["spinpropvmvcpus"] = document.getElementById("spinpropvmvcpus").value;
        scalepropvmprio = document.getElementById("scalepropvmprio")
        prop["spinpropvmprio"] = scalepropvmprio.options[scalepropvmprio.selectedIndex].value;
        prop["checkvmpropautostart"] = document.getElementById("checkvmpropautostart").checked;
        if (document.getElementById("txtvmpropparams")) {
            prop["txtvmpropparams"] = document.getElementById("txtvmpropparams").value;
        } else {
            prop["txtvmpropparams"] = "";
        }
        var listbootorder = document.getElementById("listbootorder");
        prop["order"] = '';
        if (listbootorder) {
            for (var i = 0; i < listbootorder.options.length; i++) {
                if (listbootorder.options[i].disabled == false) {
                    prop["order"] += listbootorder.options[i].value;
                } else {
                    break;
                }
            }
        }
        prop["radioautohome"] = document.getElementById("radioautohome").checked;
        prop["radiomanualhome"] = document.getElementById("radiomanualhome").checked;
        prop["affinity"] = selected_host_ref;
    }
    if (type == "vdi") {
        prop["spinvdisize"] = document.getElementById("spinvdisize").value;
        var modes = new Object();
        var positions = new Object();
        var bootables= new Object();
        combostgmode = document.getElementsByName("combostgmode");
        combostgposition = document.getElementsByName("combostgposition");
        isbootable = document.getElementsByName("isbootable");
        for (var i = 0; i < combostgmode.length; i++) {
            list = combostgmode[i];
            modes[combostgmode[i].getAttribute("id")] = list.options[list.selectedIndex].value;
        }
        for (var i = 0; i < combostgposition.length; i++) {
            list = combostgposition[i];
            positions[combostgposition[i].getAttribute("id")] = list.options[list.selectedIndex].value;
        }
        for (var i = 0; i < isbootable.length; i++) {
            bootables[isbootable[i].getAttribute("id")] = isbootable[i].checked;
        }
        prop["modes"] = modes;
        prop["positions"] = positions;
        prop["bootables"] = bootables;
    }
    if (document.getElementById("optimizegeneraluse").checked) {
        prop["memorymultiplier"] = "1.00";

    } else {
        if (document.getElementById("optimizeforxenapp").checked) {
            prop["memorymultiplier"] = "4.00";
        } else {
            prop["memorymultiplier"] = document.getElementById("memorymultiplier").value;
        }
    }

    
    client.open("POST", "set_properties", true); 
    params = "&host=" + parent.selected_ip +"&ref=" + ref + "&type=" + type;
    params += "&values=" + JSON.stringify(prop);
    client.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    client.setRequestHeader("Content-Length", params.length);
    client.setRequestHeader("Connection", "close");
    client.send(params)

}

function showPage(page) {
    document.getElementById(selected_page).style.display = "none";
    selected_page = page;
    document.getElementById(selected_page).style.display = "";
    document.getElementById(selected_prop).style.backgroundColor= "";
    selected_prop = "lblprop" + selected_page.replace("tabprop", "") 
    document.getElementById(selected_prop).style.backgroundColor= "#d5e5f7";
}

function selectVdiRow(ref) {
    if (selected_vdi_ref && document.getElementById(selected_vdi_ref)) {
        document.getElementById(selected_vdi_ref).style.backgroundColor = selected_row_color
    }
    selected_vdi_ref = ref;
    selected_row_color =  document.getElementById(selected_vdi_ref).style.backgroundColor;
    document.getElementById(selected_vdi_ref).style.backgroundColor = "#3366CC";
}

function selectHostRow(ref) {
    if (selected_host_ref && document.getElementById(selected_host_ref)) {
        document.getElementById(selected_host_ref).style.backgroundColor = selected_row_color
    }
    selected_host_ref = ref;
    selected_row_color =  document.getElementById(selected_host_ref).style.backgroundColor;
    document.getElementById(selected_host_ref).style.backgroundColor = "#3366CC";
    document.getElementById("radiomanualhome").checked = true;
}

function checkFreePosition(free, device, select, label) {
    sel = document.getElementById(select);
    value = sel.options[sel.selectedIndex].value;
    if (value == device) {
        document.getElementById(label).style.display = "none";
        document.getElementById("btvmpropaccept").disabled = false;
    } else {
        free = eval(free);
        found = false;
        for (i=0; i < free.length; i++) {
            if (value == free[i]) {
                found = true;
            }
        }
        if (found) {
            document.getElementById(label).style.display = "none";
            document.getElementById("btvmpropaccept").disabled = false;
        } else {
            document.getElementById(label).style.display = "";
            document.getElementById("btvmpropaccept").disabled = true;
        }
    }
}

function on_listbootorder_changed() {
    listbootorder = document.getElementById("listbootorder")
    if (listbootorder.selectedIndex == 0) {
        document.getElementById("btmoveup").disabled = true;
        document.getElementById("btmovedown").disabled = false;
    } else if (listbootorder.selectedIndex == 3) {
        document.getElementById("btmoveup").disabled = false;
        document.getElementById("btmovedown").disabled = true;
    } else {
        document.getElementById("btmoveup").disabled = false;
        document.getElementById("btmovedown").disabled = false;
    }
}
function on_btmoveup_clicked() {
    listbootorder = document.getElementById("listbootorder")
    var opt1 = new Option(listbootorder[listbootorder.selectedIndex].text,  listbootorder[listbootorder.selectedIndex].value)
    var opt2 = new Option(listbootorder[listbootorder.selectedIndex-1].text,  listbootorder[listbootorder.selectedIndex-1].value)
    sel = listbootorder.selectedIndex
    listbootorder.options[sel] = opt2;
    listbootorder.options[sel-1] = opt1;
    listbootorder.options[sel-1].selected = true;
    on_listbootorder_changed();
}
function on_btmovedown_clicked() {
    listbootorder = document.getElementById("listbootorder")
    var opt1 = new Option(listbootorder[listbootorder.selectedIndex].text,  listbootorder[listbootorder.selectedIndex].value)
    var opt2 = new Option(listbootorder[listbootorder.selectedIndex+1].text,  listbootorder[listbootorder.selectedIndex+1].value)
    sel = listbootorder.selectedIndex
    listbootorder.options[sel] = opt2;
    listbootorder.options[sel+1] = opt1;
    listbootorder.options[sel+1].selected = true;
    on_listbootorder_changed();
}

