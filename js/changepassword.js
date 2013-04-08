function on_acceptchangepassword_clicked() {
    var txtcurrentpw = escape(document.getElementById("txtcurrentpw").value);
    var txtnewpw = escape(document.getElementById("txtnewpw").value);
    var txtrenewpw = escape(document.getElementById("txtrenewpw").value);
    if (!txtnewpw) {
        alert("Password cannot be empty");
    }
    else if (txtnewpw != txtrenewpw) {
        alert("Password mismatch");
    } else {
        var client = new XMLHttpRequest();
        client.onreadystatechange = function () {
            if(this.readyState == 4 && this.status == 200) {
                if (this.responseText == "ERROR") {
                   document.getElementById("lblwrongpw").style.display = ""; 
                } else {
                    var client = new XMLHttpRequest();
                    client.onreadystatechange = function () {
                        if(this.readyState == 4 && this.status == 200) {
                            if (this.responseText != "OK") {
                                alert(this.responseText);
                            } else {
                                parent.hidePopWin(false); 
                            }
                        } else if (this.readyState == 4 && this.status != 200) {
                            alert("Error on callFunction()");
                        }
                    }
                    client.open("POST", "do_action_no_ref", true); 
                    params = "action=change_server_password&host=" + parent.selected_ip + "&old=" + txtcurrentpw + "&new=" + txtnewpw;
                    client.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
                    client.setRequestHeader("Content-Length", params.length);
                    client.setRequestHeader("Connection", "close");
                    client.send(params)

                }
            } else if (this.readyState == 4 && this.status != 200) {
                alert("Error on callFunction()");
            }
        }
        client.open("POST", "check_password", true);
        params = "host=" + parent.selected_ip + "&password=" + txtcurrentpw
        client.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
        client.setRequestHeader("Content-Length", params.length);
        client.setRequestHeader("Connection", "close");
        client.send(params);
    }
} 
