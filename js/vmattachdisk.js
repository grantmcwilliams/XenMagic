var selected_row_ref = "";
function selectRow(ref) {
    document.getElementById("acceptnewvmdisk").disabled = false;
    if (selected_row_ref && document.getElementById(selected_row_ref)) {
        document.getElementById(selected_row_ref).style.backgroundColor = selected_row_color
    }
    selected_row_ref = ref;
    selected_row_color =  document.getElementById(selected_row_ref).style.backgroundColor;
    document.getElementById(selected_row_ref).style.backgroundColor = "#3366CC";
}
function on_btacceptattachdisk_clicked() {
    var ro = document.getElementById("checkattachdisk").checked;
    var client = new XMLHttpRequest();
    client.open("GET", "attach_disk_to_vm?host=" + parent.selected_host + "&vm=" + parent.selected_ref + "&disk=" + selected_row_ref + "&ro=" + ro, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            if (this.responseText != "OK") {
                alert(this.responseText);
            }
            parent.hidePopWin(false);
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error on_btacceptattachdisk_clicked";
        }            
    }
    client.send(null)    
}

