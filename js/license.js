function on_acceptlicensekey_clicked() {
    formlicensekey = document.getElementById("formlicensekey")
    formlicensekey.submit();
}

function on_acceptlicensehost_clicked() {
    var licensehost = document.getElementById("licensehost").value;
    var licenseport = document.getElementById("licenseport").value;
    var edition = "advanced";
    var license = document.getElementsByName("license");
    for (var i=0; i < license.length; i++) {
        if (license[i].checked) {
            edition = license[i].id;
        }
    }
    document.getElementById("uploading").style.display = "";
    var client = new XMLHttpRequest();
    client.open("GET", "set_license_host?host=" + parent.selected_host + "&ref=" + parent.selected_ref +  "&licensehost=" + licensehost + "&licenseport=" + licenseport + "&edition=" + edition, true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            if (this.responseText != "OK") {
                alert(this.responseText);
            }
            parent.hidePopWin(false);
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error on_acceptlicensehost_clicked";
        }            
    }
    client.send(null); 
}
