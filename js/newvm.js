var selected_row_color = "";
var selected_row_ref = "";
var selected_host_ref = "";
var selected_host_color = "";
var selected_stg_ref = "";
var selected_stg_color = "";
var selected_vif_ref = "";
var selected_vif_color = "";

var pagenumber = 0;
var show_location = true;
function selectTplRow(ref, desc, pvargs, cpu, mem, loc, type) {
    if (selected_row_ref && document.getElementById(selected_row_ref)) {
        document.getElementById(selected_row_ref).style.backgroundColor = selected_row_color
    }
    selected_row_ref = ref;
    selected_row_color =  document.getElementById(selected_row_ref).style.backgroundColor;
    document.getElementById(selected_row_ref).style.backgroundColor = "#3366CC";
    document.getElementById("lblnewvminfo").innerHTML = desc;
    document.getElementById("nextwindownewvm").disabled = false;
    var now = new Date();
    month = parseInt(now.getMonth())
    datestring = now.getFullYear() + "-" + (month + 1) + "-" + now.getDate();
    document.getElementById("entrynewvmname").value = document.getElementById(selected_row_ref).cells[1].innerHTML + " (" + datestring + ")";
    document.getElementById("entrybootparameters").value = pvargs;
    document.getElementById("numberofvcpus").value = cpu;
    document.getElementById("initialmemory").value = mem;
    if (loc == "True") {
        show_location = true;
        document.getElementById("lblnewvm2").style.visibility = "hidden";
    } else {
        show_location = false;
        document.getElementById("lblnewvm2").style.visibility = "visible";
    }
    if (type == "custom_template") {
        document.getElementById("customtemplatealert").style.display = "";
    } else {
        document.getElementById("customtemplatealert").style.display = "none";
    }
    document.getElementById("addnewvmstorage").disabled = (type == "custom_template");
    document.getElementById("editnewvmstorage").disabled = (type == "custom_template");
    document.getElementById("deletenewvmstorage").disabled = (type == "custom_template");
}
function selectHostRow(ref, cpu, mtotal, mfree) {
    if (selected_host_ref && document.getElementById(selected_host_ref)) {
        document.getElementById(selected_host_ref).style.backgroundColor = selected_host_color
    }
    selected_host_ref = ref;
    selected_host_color =  document.getElementById(selected_host_ref).style.backgroundColor;
    document.getElementById(selected_host_ref).style.backgroundColor = "#3366CC";
    document.getElementById("lblnewvmcpus").innerHTML = cpu;
    document.getElementById("lblnewvmtotalmemory").innerHTML = mtotal;
    document.getElementById("lblnewvmfreememory").innerHTML = mfree;

    var client = new XMLHttpRequest();
    client.open("GET", "newvmstorage?vm=" + selected_row_ref + "&host=" + parent.selected_host + "&host_ref=" + selected_host_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            document.getElementById("newvmstorage").innerHTML = this.responseText;
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error newvmstorage";
        }            
    }
    client.send(null)    
}
function selectStgRow(ref) {
    if (selected_stg_ref && document.getElementById(selected_stg_ref)) {
        document.getElementById(selected_stg_ref).style.backgroundColor = selected_stg_color
    }
    selected_stg_ref = ref;
    selected_stg_color =  document.getElementById(selected_stg_ref).style.backgroundColor;
    document.getElementById(selected_stg_ref).style.backgroundColor = "#3366CC";
}

function selectVifRow(ref) {
    if (selected_vif_ref && document.getElementById(selected_vif_ref)) {
        document.getElementById(selected_vif_ref).style.backgroundColor = selected_vif_color
    }
    selected_vif_ref = ref;
    selected_vif_color =  document.getElementById(selected_vif_ref).style.backgroundColor;
    document.getElementById(selected_vif_ref).style.backgroundColor = "#3366CC";
}

function filterTpls() {
    searchtpl = document.getElementById("searchtpl").value;
    tabletemplates = document.getElementById("tabletemplates");
    for (i = 1; i < tabletemplates.rows.length; i++) {
        if (!searchtpl || tabletemplates.rows[i].cells[1].innerHTML.toLowerCase().indexOf(searchtpl.toLowerCase()) > -1) {
            tabletemplates.rows[i].style.display="";
        } else {
            tabletemplates.rows[i].style.display="none";
        }
    }
}

function goPage(offset) {
    document.getElementById("lblnewvm" + pagenumber).style.backgroundColor = "white";    
    document.getElementById("newvm" + pagenumber).style.display = "none";    
    if (show_location && ((offset < 0 && pagenumber == 3) || (offset > 0 && pagenumber == 1))) {
        pagenumber += offset;
    } 
    pagenumber += offset;
    document.getElementById("lblnewvm" + pagenumber).style.backgroundColor = "#d5e5f7";    
    document.getElementById("newvm" + pagenumber).style.display = "";    
    document.getElementById("previouswindownewvm").disabled = (pagenumber == 0);    
    document.getElementById("nextwindownewvm").disabled = (pagenumber == 7);
    document.getElementById("finishwindownewvm").disabled = (pagenumber != 7);
    if (pagenumber == 1) {
        selected_tpl_ref = selected_row_ref;
        document.getElementById(document.getElementById("selhost").innerHTML).onclick();
    }
}
function on_deletenewvmstorage_clicked() {
    if (selected_stg_ref) {
        document.getElementById(selected_stg_ref).parentNode.removeChild(document.getElementById(selected_stg_ref))
    }
}
function on_addnewvmnetwork_clicked() {
    row=document.createElement("TR");
    row.setAttribute("class", "row");
    row.style.clear = "both";
    row.id = "newvif" + (document.getElementById("tablenewnetwork").rows.length-1);
    row.setAttribute("onclick", "selectVifRow('newvif" + (document.getElementById("tablenewnetwork").rows.length-1) + "');");
    cell1 = document.createElement("TD");
    cell2 = document.createElement("TD");
    cell3 = document.createElement("TD");
    textnode1 = document.createTextNode("Interface " + (document.getElementById("tablenewnetwork").rows.length-1));
    cell1.appendChild(textnode1);
    content2 = document.createElement("input");
    content2.setAttribute("type", "text");
    content2.setAttribute("name", "macnewvif" + document.getElementById("tablenewnetwork").rows.length-1);
    content2.setAttribute("style", "border: 1px dotted; background-color: #d5e5f7;");
    content2.setAttribute("value", "auto-generated");
    cell2.appendChild(content2);
    networkselect = document.getElementById("networkselect")
    content3 = networkselect.cloneNode(true);
    content3.id = "newworkref" + (document.getElementById("tablenewnetwork").rows.length-1);
    content3.style.display = "";
    cell3.appendChild(content3);
    row.appendChild(cell1);
    row.appendChild(cell2);
    row.appendChild(cell3);
    document.getElementById("tablenewnetwork").appendChild(row);
}

function on_deletenewvmnetwork_clicked() {
    if (selected_vif_ref) {
        document.getElementById(selected_vif_ref).parentNode.removeChild(document.getElementById(selected_vif_ref))
    }
}

function on_finishwindownewvm_clicked() {
    var i = 0;

    ref = selected_row_ref;
    name = document.getElementById("entrynewvmname").value;
    description = document.getElementById("entrynewvmdescription").value;
    host = selected_host_ref; 
    for (i=0; i < document.getElementsByName("radiobutton1").length; i++) {
        if (document.getElementsByName("radiobutton1")[i].checked) {
            loc = document.getElementsByName("radiobutton1")[i].value;
        }
    }        
    location_url = document.getElementById("radiobutton1_data").value; 
    radiobutton2_data = document.getElementById("radiobutton2_data");
    vdi = "";
    if (loc == "radiobutton2") {
        radiobutton2_data = document.getElementById("radiobutton2_data");
        vdi = radiobutton2_data.options[radiobutton2_data.selectedIndex].value;
    } else if (loc == "radiobutton3") {
            radiobutton3_data = document.getElementById("radiobutton3_data");
            vdi = radiobutton3_data.options[radiobutton3_data.selectedIndex].value; 
    }
    memorymb = document.getElementById("initialmemory").value;
    numberofvcpus = document.getElementById("numberofvcpus").value;
    entrybootparameters = document.getElementById("entrybootparameters").value;
    startvm = document.getElementById("checkstartvm").checked;
    disks = [];
    vifs = [];
    tablenewstorage = document.getElementById("tablenewstorage");
    for (i = 1; i < tablenewstorage.rows.length; i++) {
        disks[i-1] = [tablenewstorage.rows[i].cells[0].innerHTML, tablenewstorage.rows[i].cells[3].innerHTML];
    }
    tablenewnetwork = document.getElementById("tablenewnetwork");
    for (i = 1; i < tablenewnetwork.rows.length; i++) {
        networkcolumn = tablenewnetwork.rows[i].cells[2].childNodes[1];
	if(!networkcolumn) {
		networkcolumn = tablenewnetwork.rows[i].cells[2].childNodes[0];
	}
        vifs[i-1] = [tablenewnetwork.rows[i].cells[0].innerHTML, networkcolumn.options[networkcolumn.selectedIndex].value];
    }
    document.getElementById("loading").style.display = "";
    var client = new XMLHttpRequest();
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            if (this.responseText != "OK") {
                alert(this.responseText);
            } else {
                parent.hidePopWin(false); 
            }
        } else if (this.readyState == 4 && this.status != 200 && this.status != 0) {
            alert("Error on creating newvm(): " + this.status);
        }
    }
    client.open("POST", "do_action_newvm", true); 
    params = "&server=" + parent.selected_ip +"&ref=" + ref + "&name=" + name + "&description=" + description + "&host=" + host;
    params += "&location_url=" + location_url + "&vdi=" + vdi;
    params += "&memorymb=" + memorymb + "&numberofvcpus=" + numberofvcpus + "&entrybootparameters=" + entrybootparameters;
    params += "&startvm=" + startvm + "&disks=" + JSON.stringify(disks) + "&vifs=" + JSON.stringify(vifs) + "&location=" + loc;

    client.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    client.setRequestHeader("Content-Length", params.length);
    client.setRequestHeader("Connection", "close");
    client.send(params)

    /*
     * ref
     * name
     * host
     * description
     * location
     * location_url
     * vdi?
     * memorymb
      numberofvcpus
     * entrybootparameters
     */
}
