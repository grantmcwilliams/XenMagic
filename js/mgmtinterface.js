function on_acceptmgmtinterface_clicked() {
    res = confirm("You are reconfiguring the primary management interface.  If the new settings are\n incorrect then XenCenter may permanently lose the connection to the server.\n\n You should only proceed if you have verified that these settings are correct.");
    if (res == true) {
        var ip = document.getElementById("txtmgmtip").value;
        var pif_ref = document.getElementById("txtpifref").value;
        var combomgmtnetworks = document.getElementById("combomgmtnetworks")
        var network_ref = combomgmtnetworks.options[combomgmtnetworks.selectedIndex].value;
        var mask = document.getElementById("txtmgmtmask").value;
        var gw = document.getElementById("txtmgmtgw").value;
        var dns1 = document.getElementById("txtmgmtdns1").value;
        var dns2 = document.getElementById("txtmgmtdns2").value;
        var dns = ""
        if (!document.getElementById("radiomgmtdnsdhcp").checked) {
            dns = dns1 + "," + dns2;
        }
        var configuration_mode = "Static";
        if (document.getElementById("radiomgmtipdhcp").checked) {
            configuration_mode = "DHCP";
        }

        var client = new XMLHttpRequest();
        params = "&pif_ref=" + pif_ref + "&configuration_mode=" + configuration_mode + "&ip=" + ip;
        params += "&mask=" + mask + "&gw=" + gw + "&dns=" + dns;
        client.open("GET", "reconfigure_pif?host=" + parent.selected_ip + "&ref=" + parent.selected_ref + params, true);
        client.onreadystatechange = function() {
             return function() {
                if(this.readyState == 4 && this.status == 200) {
                    if (this.responseText == "OK") {
                        parent.hidePopWin(false);
                    } else {
                        alert(this.responseText);
                    }
                } else if (this.readyState == 4 && this.status != 200) {
                    document.getElementById("statusbar").innerHTML = "error on_acceptmgmtinterface_clicked";
                }
            }
        }();
        client.send(null);

    }
}
