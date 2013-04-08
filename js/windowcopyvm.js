var selected_row_ref = "";
function selectRow(ref) {
    document.getElementById("windowcopyvm_copy").disabled = false;
    document.getElementById("radiofullclone").checked = true;
    if (selected_row_ref && document.getElementById(selected_row_ref)) {
        document.getElementById(selected_row_ref).style.backgroundColor = selected_row_color
    }
    selected_row_ref = ref;
    selected_row_color =  document.getElementById(selected_row_ref).style.backgroundColor;
    document.getElementById(selected_row_ref).style.backgroundColor = "#3366CC";
}

function checkSelected(el) {
    if (!selected_row_ref) {
        document.getElementById("windowcopyvm_copy").disabled = true;
    }
}

function on_windowcopyvm_copy_clicked() {
    var name = document.getElementById("txtcopyvmname").value;
    var desc = document.getElementById("txtcopyvmdesc").value;
    var full = document.getElementById("radiofullclone").checked; 
    var client = new XMLHttpRequest();
    client.open("GET", "copy_vm?host=" + parent.selected_host + "&ref=" + parent.selected_ref +  "&name=" + name + "&desc=" + desc + "&full=" + full + "&sr=" + selected_row_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            if (this.responseText != "OK") {
                alert(this.responseText);
            }
            parent.hidePopWin(false);
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error on_windowcopyvm_copy_clicked";
        }            
    }
    client.send(null)    

}
