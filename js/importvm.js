var pagenumber = 0;
var reattach_ref = "";
var selected_host_ref = "";
var selected_stg_ref = "";
var selected_vif_ref = "";
function goPrevious() {
    pagenumber--;
    document.getElementById("importvm" + (pagenumber + 1)).style.display = "none";
    document.getElementById("importvm" + pagenumber).style.display = ""; 
    if (pagenumber == 0) {
        document.getElementById("previousvmimport").disabled  = true;
    }
    document.getElementById("nextvmimport").disabled = false;
    document.getElementById("finishvmimport").disabled = true;
    document.getElementById("lblimportvm" + pagenumber).style.backgroundColor = "#d5e5f7";
    document.getElementById("lblimportvm" + (pagenumber + 1)).style.backgroundColor = "";
}

function goNext() {
        if (!document.getElementById("filechooserimportvm").value) {
            alert("Choose file to import");
            return
        }
        pagenumber++;
        document.getElementById("lblimportvm" + (pagenumber - 1)).style.backgroundColor = "";
        document.getElementById("importvm" + (pagenumber - 1)).style.display = "none";
        document.getElementById("lblimportvm" + pagenumber).style.backgroundColor = "#d5e5f7";
        document.getElementById("importvm" + pagenumber).style.display = "";
        document.getElementById("previousvmimport").disabled  = false;
        if (pagenumber == 1) {
            document.getElementById(document.getElementById("selhost").innerHTML).onclick();
        }
        if (pagenumber == 4) {
            document.getElementById("nextvmimport").disabled = true;
            document.getElementById("finishvmimport").disabled = false;
        }
}

function selectHostRow(ref, cpu, mtotal, mfree) {
    if (selected_host_ref && document.getElementById(selected_host_ref)) {
        document.getElementById(selected_host_ref).style.backgroundColor = selected_host_color
    }
    selected_host_ref = ref;
    selected_host_color =  document.getElementById(selected_host_ref).style.backgroundColor;
    var client = new XMLHttpRequest();
    client.open("GET", "importvmstorage?&host=" + parent.selected_host + "&ref=" + selected_host_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            document.getElementById("treeimportstg").innerHTML = this.responseText;
            document.getElementById(document.getElementById("default_sr").value).onclick();
            
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error importvmstorage";
        }            
    }
    client.send(null)    

    document.getElementById(selected_host_ref).style.backgroundColor = "#3366CC";

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
function on_btimportaddnetwork_clicked() {
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

function on_btimportdeletenetwork_clicked() {
    if (selected_vif_ref) {
        document.getElementById(selected_vif_ref).parentNode.removeChild(document.getElementById(selected_vif_ref))
    }
}                                

function on_finishvmimport_clicked() {
    disks = [];
    vifs = [];
    tablenewstorage = document.getElementById("tablenewstorage");
    for (i = 1; i < tablenewstorage.rows.length; i++) {
        disks[i-1] = [tablenewstorage.rows[i].cells[1].innerHTML, tablenewstorage.rows[i].cells[2].innerHTML];
    }
    tablenewnetwork = document.getElementById("tablenewnetwork");
    for (i = 1; i < tablenewnetwork.rows.length; i++) {
        var networkcolumn = tablenewnetwork.rows[i].cells[2].childNodes[1];
        if (!networkcolumn) {
            networkcolumn = tablenewnetwork.rows[i].cells[2].childNodes[0];
        }
        vifs[i-1] = [tablenewnetwork.rows[i].cells[0].innerHTML, networkcolumn.options[networkcolumn.selectedIndex].value];
    }
    document.getElementById("host_ref").value = selected_host_ref;
    document.getElementById("stg").value = selected_stg_ref
    document.getElementById("vifs").value = vifs;
    document.getElementById("disks").value = disks;
    document.getElementById("loading").style.display = "";
    var client = new XMLHttpRequest();
    client.open("GET", "pre_import_vm?host=" + parent.selected_host + "&ref=" + selected_host_ref +  "&stg=" + selected_stg_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            document.getElementById("importvmform").submit();
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error importvmstorage";
        }            
    }
    client.send(null)    

}
