function on_acceptmasterpassword_clicked() {
    var txtaskmasterpassword = escape(document.getElementById("txtaskmasterpassword").value);
    if (!txtaskmasterpassword) {
        alert("Password cannot be empty");
    } else {
        var client = new XMLHttpRequest();
        client.onreadystatechange = function () {
            if(this.readyState == 4 && this.status == 200) {
                if (this.responseText == "ERROR") {
                   document.getElementById("lblwrongpassword").style.display = ""; 
                } else {
                    var client = new XMLHttpRequest();
                    client.onreadystatechange = function () {
                        if(this.readyState == 4 && this.status == 200) {
                            if (this.responseText != "OK") {
                                alert("Something is wrong with password typed");
                            } else {
                                parent.hidePopWin(false); 
                            }
                        } else if (this.readyState == 4 && this.status != 200) {
                            alert("Error on on_acceptmasterpassword_clicked()");
                        }
                    }
                    client.open("POST", "master_password_ok", true); 
                    params =  "&password=" + txtaskmasterpassword 
                    client.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                    client.setRequestHeader("Content-Length", params.length);
                    client.setRequestHeader("Connection", "close");
                    client.send(params)

                }
            } else if (this.readyState == 4 && this.status != 200) {
                alert("Error on callFunction()");
            }
        }
        client.open("POST", "check_master_password", true);
        params = "&password=" + txtaskmasterpassword 
        client.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        client.setRequestHeader("Content-Length", params.length);
        client.setRequestHeader("Connection", "close");
        client.send(params);
    }
} 
