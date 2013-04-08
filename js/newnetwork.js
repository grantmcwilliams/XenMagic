function checkVlan(vlan) {
   var client = new XMLHttpRequest();
    client.open("GET", "is_vlan_available?host=" + parent.selected_ip + "&vlan=" + vlan.value, true);
    client.onreadystatechange = function() {
            if(this.readyState == 4 && this.status == 200) {
                if (this.responseText == "True") {
                   document.getElementById("lblvlaninuse").style.display="none"
                   document.getElementById("acceptnewnetwork").disabled = false;
                } else {
                   document.getElementById("lblvlaninuse").style.display="";
                   document.getElementById("acceptnewnetwork").disabled = true;
                }
            } else if (this.readyState == 4 && this.status != 200) {
                parent.document.getElementById("statusbar").innerHTML = "error checkVlan";
            }            
    }
    client.send(null)
}
function toggleExternal(checkbox) {
    if (checkbox.value == "radiointernalnetwork") {
        document.getElementById("internalnetwork").style.display = "none";
    } else {
        document.getElementById("internalnetwork").style.display = "";
    }
}
function on_acceptnewnetwork_clicked() {
    external = document.getElementById("radioexternalnetwork").checked;
    name = document.getElementById("txtnetworkname").value;
    desc = document.getElementById("txtnetworkdesc").value;
    combonetworknic = document.getElementById("combonetworknic");
    pif = combonetworknic.options[combonetworknic.selectedIndex].value;
    vlan = document.getElementById("spinnetworkvlan").value; 
    auto = document.getElementById("checkautonetwork").checked;
    document.getElementById("loading").style.display="";
    document.getElementById("acceptnewnetwork").style.display="none";
    document.getElementById("cancelnewnetwork").style.display="none";
    if (external) {
        parameters = "action=create_external_network&ref=" + name + "&host=" + parent.selected_ip + "&desc=" + desc + "&auto=" + auto + "&pif=" + pif + "&vlan=" + vlan
    } else {
        parameters = "action=create_internal_network&ref=" + name + "&host=" + parent.selected_ip + "&desc=" + desc + "&auto=" + auto;
    }
    var client = new XMLHttpRequest();
    client.onreadystatechange = function () {
        if(this.readyState == 4 && this.status == 200) {
            document.getElementById("loading").style.display="none";
            document.getElementById("acceptnewnetwork").style.display="";
            document.getElementById("cancelnewnetwork").style.display="";
            if (this.responseText != "OK") {
                alert(this.responseText);
            } else {
                parent.hidePopWin(false); 
            }
        } else if (this.readyState == 4 && this.status != 200) {
            document.getElementById("loading").style.display="none";
            document.getElementById("acceptnewnetwork").style.display="";
            document.getElementById("cancelnewnetwork").style.display="";
            alert("Error on callFunction()");
        }
    }
    client.open("GET", "do_action?" + parameters);
    client.send()
}

