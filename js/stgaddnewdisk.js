var selected_row_ref = "";
function selectRow(ref) {
    document.getElementById("acceptstgaddnewdisk").disabled = false;
    if (selected_row_ref && document.getElementById(selected_row_ref)) {
        document.getElementById(selected_row_ref).style.backgroundColor = selected_row_color
    }
    selected_row_ref = ref;
    selected_row_color =  document.getElementById(selected_row_ref).style.backgroundColor;
    document.getElementById(selected_row_ref).style.backgroundColor = "#3366CC";
}

function on_acceptstgaddnewdisk_clicked() {
    var name = document.getElementById("stgaddnewdisk_name").value;
    var desc = document.getElementById("stgaddnewdisk_desc").value;
    var size = document.getElementById("newstgdisksize").value;
    var client = new XMLHttpRequest();
    document.getElementById("loading").style.display = "";
    client.open("GET", "add_disk_to_stg?host=" + parent.selected_host + "&name=" + name+ "&desc=" + desc + "&size=" + size + "&ref=" + selected_row_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            if (this.responseText != "OK") {
                alert(this.resonseText);
            }
            parent.hidePopWin(false);
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error on_btacceptattachdisk_clicked";
        }            
    }
    client.send(null)    

}
