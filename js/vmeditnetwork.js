function on_accepteditnetwork_clicked() {
    var ref = parent.selected_vif_vm_ref;
    var treeeditnetwork = document.getElementById("treeeditnetwork");
    var networkref = treeeditnetwork.options[treeeditnetwork.selectedIndex].value;
    var mac = "";
    if (!document.getElementById("radioeditauto").checked) {
        mac = document.getElementById("entryeditmac").value;
    }
    var limit = document.getElementById("entryeditlimit").value;
    var client = new XMLHttpRequest();
    client.open("GET", "vm_edit_interface?host=" + parent.selected_host + "&ref=" + ref + "&networkref=" + networkref + "&mac=" + mac + "&limit=" + limit + "&vm=" + parent.selected_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            if (this.responseText != "OK") {
                alert(this.resonseText);
            }
            parent.hidePopWin(false);
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error on_accepteditnetwork_clicked";
        }            
    }
    client.send(null)    
}
