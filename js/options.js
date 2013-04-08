function on_acceptdialogoptions_clicked() {
    var checksavepassword = document.getElementById("checksavepassword").checked;
    var txtmasterpassword = document.getElementById("txtmasterpassword").value;
    if (checksavepassword && !txtmasterpassword) {
        alert("You should specify a master password");
    } else {
        var client = new XMLHttpRequest();
        client.onreadystatechange = function () {
            if(this.readyState == 4 && this.status == 200) {
               parent.hidePopWin(false);
            } else if (this.readyState == 4 && this.status != 200) {
                alert("Error on on_acceptdialogoptions_clicked()");
            }
        }
        client.open("POST", "set_options", true);
        params = "checkpassword=" + checksavepassword + "&password=" + txtmasterpassword ;
        client.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        client.setRequestHeader("Content-Length", params.length);
        client.setRequestHeader("Connection", "close");
        client.send(params);
 
    }
}
