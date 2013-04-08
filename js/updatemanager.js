var selected_row_ref = "";
var selected_row_color = "";
var selected_host_ref = "";
var selected_host_color = "";
function selectRowRef(ref, name, desc, version, guidance) {
    if (selected_row_ref && document.getElementById(selected_row_ref)) {
        document.getElementById(selected_row_ref).style.backgroundColor = selected_row_color
    }
    selected_row_ref = ref;
    selected_row_color =  document.getElementById(selected_row_ref).style.backgroundColor;
    document.getElementById(selected_row_ref).style.backgroundColor = "#3366CC";
    document.getElementById("lblupdatename").innerHTML = name;
    document.getElementById("lblupdatedesc").innerHTML = desc;
    document.getElementById("lblupdateversion").innerHTML = version;
    document.getElementById("lblupdateguidance").innerHTML = guidance;
    var client = new XMLHttpRequest();
    client.open("GET", "listupdatestatus?host=" + parent.selected_host + "&ref=" + selected_row_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            document.getElementById("statuspatch").innerHTML = this.responseText;
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error fillResumeServers";
        }            
    }
    client.send(null) 
    document.getElementById("btremoveupdate").disabled = false;

}
function selectHostRef(ref, name, desc, version, guidance) {
    document.getElementById("btapplypatch").disabled = false;
    if (seected_host_ref && document.getElementById(seected_host_ref)) {
        document.getElementById(seected_host_ref).style.backgroundColor = selected_host_color
    }
    seected_host_ref = ref;
    selected_host_color =  document.getElementById(seected_host_ref).style.backgroundColor;
}
function on_btremoveupdate_clicked() {
   var client = new XMLHttpRequest();
    client.open("GET", "remove_patch?host=" + parent.selected_host + "&host_ref=" + parent.selected_ref + "&ref=" + selected_row_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            if(this.responseText == "OK") {
                alert("Patch removed");
            } else {
                alert(this.responseText);
            }
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error on_btremoveupdate_clicked";
        }            
    }
    client.send(null) 

}
function on_btapplypatch_clicked() {
   var client = new XMLHttpRequest();
    client.open("GET", "apply_patch?host=" + parent.selected_host + "&host_ref=" + selected_host_ref + "&ref=" + selected_row_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            if(this.responseText == "OK") {
                alert("Patch applied");
                 document.getElementById(selected_row_ref).onclick();
            } else {
                alert(this.responseText);
            }
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error on_btapplypatch_clicked";
        }            
    }
    client.send(null) 
 
}
