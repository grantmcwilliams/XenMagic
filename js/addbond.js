function fillnicinfo(nic, bondlist) {

    var client = new XMLHttpRequest();
    client.open("GET", "get_nic_info?host=" + parent.selected_ip + "&ref=" + nic.options[nic.selectedIndex].value, true);
    client.onreadystatechange = function() {
            if(this.readyState == 4 && this.status == 200) {
                var returned = eval('(' + this.responseText + ')');
                for(element in returned) {
                    document.getElementById(element).innerHTML = returned[element];
                }
            } else if (this.readyState == 4 && this.status != 200) {
                parent.document.getElementById("statusbar").innerHTML = "error fillnicinfo";
            }            
    }
    client.send(null)
    if (!bondlist) {
        if (nic.options[nic.selectedIndex].disabled == false) {
            document.getElementById("btaddbondednic").disabled = false;
        }
        document.getElementById("btrembondednic").disabled = true;
    } else {
        document.getElementById("btaddbondednic").disabled = true;
        document.getElementById("btrembondednic").disabled = false;
    }
}

function on_btaddbondednic_clicked() {
    treeavailnics = document.getElementById("treeavailnics");
    treebondnics = document.getElementById("treebondnics");

    var newopt = document.createElement('option');
    newopt.text = treeavailnics.options[treeavailnics.selectedIndex].text;
    newopt.value = treeavailnics.options[treeavailnics.selectedIndex].value;
    try {
        treebondnics.add(newopt, null);
    } catch (ex) {
        treebondnics.add(newopt);
    }
    treeavailnics.remove(treeavailnics.selectedIndex);
    document.getElementById("btacceptaddbond").disabled = (treebondnics.options.length != 2);
    document.getElementById("btaddbondednic").disabled = (treebondnics.options.length == 2);
}

function on_btrembondednic_clicked() {
    treeavailnics = document.getElementById("treeavailnics");
    treebondnics = document.getElementById("treebondnics");

    var newopt = document.createElement('option');
    newopt.text = treebondnics.options[treebondnics.selectedIndex].text;
    newopt.value = treebondnics.options[treebondnics.selectedIndex].value;
    try {
        treeavailnics.add(newopt, null);
    } catch (ex) {
        treeavailnics.add(newopt);
    }
    treebondnics.remove(treebondnics.selectedIndex);
    document.getElementById("btacceptaddbond").disabled = (treebondnics.options.length != 2);
    document.getElementById("btaddbondednic").disabled = false;
}

function on_btacceptaddbond_clicked() {
    document.getElementById("loading").style.display="";
    treebondnics = document.getElementById("treebondnics");
    auto = document.getElementById("checkautoaddbond").checked;
    ref = treebondnics.options[0].value;
    name = treebondnics.options[0].text;
    ref2 = treebondnics.options[1].value;
    name2 = treebondnics.options[1].text;
    var client = new XMLHttpRequest();
    client.onreadystatechange = function () {
        if(this.readyState == 4 && this.status == 200) {
            document.getElementById("loading").style.display="none";
            document.getElementById("btacceptaddbond").style.display="";
            document.getElementById("btcanceladdbond").style.display="";
            if (this.responseText != "OK") {
                alert(this.responseText);
            } else {
                parent.hidePopWin(false); 
            }
        } else if (this.readyState == 4 && this.status != 200) {
            document.getElementById("loading").style.display="none";
            document.getElementById("btacceptaddbond").style.display="";
            document.getElementById("btcanceladdbond").style.display="";
            alert("Error on callFunction()");
        }
    }
    client.open("GET", "do_action?action=create_bond&ref=" + ref + "&host=" + self.parent.selected_ip + "&ref2=" + ref2 + "&name=" + name + "&name2=" + name2);
    client.send()

}

