var selected_row_ref = "";
function selectRow(ref) {
    if (selected_row_ref && document.getElementById(selected_row_ref)) {
        document.getElementById(selected_row_ref).style.backgroundColor = selected_row_color
    }
    selected_row_ref = ref;
    selected_row_color =  document.getElementById(selected_row_ref).style.backgroundColor;
    document.getElementById(selected_row_ref).style.backgroundColor = "#3366CC";
}

function on_acceptrepairstorage_clicked() {
    var client = new XMLHttpRequest();
    document.getElementById("loading").style.display = "";
    client.open("GET", "repair_storage?host=" + parent.selected_host + "&ref=" + parent.selected_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            document.getElementById("lblrepairerror").style.display = "";
            document.getElementById("lblrepairerror").innerHTML = this.responseText;
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error on_btacceptattachdisk_clicked";
        }            
    }
    client.send(null)    
    
}
