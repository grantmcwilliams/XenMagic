function on_acceptmaintenancemode_clicked() {
    document.getElementById("loadingiscsi").style.display = "";
    var client = new XMLHttpRequest();
    client.open("GET", "enter_maintancemode?host=" + parent.selected_host + "&ref=" + parent.selected_ref, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            document.getElementById("loadingiscsi").style.display = "none";
            if (this.responseText != "OK") {
                alert(this.responseText);
            }
            parent.hidePopWin(false);
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error on_acceptmaintenancemode_clicked";
            parent.hidePopWin(false);
        }            
    }
    client.send(null)    

}
