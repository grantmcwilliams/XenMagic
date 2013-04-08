function on_acceptaddnetwork_clicked() {
    var ref = parent.selected_ref;
    var treeaddnetwork = document.getElementById("treeaddnetwork");
    var networkref = treeaddnetwork.options[treeaddnetwork.selectedIndex].value;
    var mac = "";
    if (!document.getElementById("radioauto").checked) {
        mac = document.getElementById("entrymac").value;
    }
    var limit = document.getElementById("entrylimit").value;
    var client = new XMLHttpRequest();
    client.open("GET", "vm_add_interface?host=" + parent.selected_host + "&ref=" + ref + "&networkref=" + networkref + "&mac=" + mac + "&limit=" + limit, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            if (this.responseText != "OK") {
                alert(this.resonseText);
            }
            parent.hidePopWin(false);
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error on_acceptaddnetwork_clicked";
        }            
    }
    client.send(null)    
}
