var close_console = false;
function on_tabbox_focus_tab(tab, frame) {
    if (selected_tab != "frameconsole" && close_console) {
        var client = new XMLHttpRequest();
        client.open("GET", "close_console");
        client.send();
        close_console = false;
    }
    if (selected_tab == "frameconsole") {
        close_console = true;
    }
    selected_tab = frame 
    if (tab) {
        for (i in tab.parentNode.childNodes) {
            if (tab.parentNode.childNodes[i].className == "tabactive") {
                tab.parentNode.childNodes[i].className = "tabinactive"
            }
        }
        tab.className = "tabactive"
    }
    var client = new XMLHttpRequest();
    client.onreadystatechange = update_frame;
    client.open("GET", "" + frame + "?ref=" + selected_ref + "&hostname=" + selected_hostname + "&type=" + selected_type + "&host=" + selected_host + "&ip=" + selected_ip + "&uuid=" + selected_uuid + "&name=" + selected_name);
    client.send();
    return false;
}

function update_frame() {
    if(this.readyState == 4 && this.status == 200) {
        document.getElementById("frame").innerHTML = this.responseText;
        if (selected_tab == "framesearch") {
            tablesearch = document.getElementById("tablesearch")
            for (i=1; i < tablesearch.rows.length; i++) {
                if (tablesearch.rows[i].getAttribute("name")) {
                    updateFrameSearch(selected_host, tablesearch.rows[i].getAttribute("name"));
                }
            }
        }
    } else if (this.readyState == 4 && this.status != 200) {
        document.getElementById("frame").innerHTML = this.responseText;
        document.getElementById("statusbar").innerHTML = "error updating frame.." + selected_tab
    }
}
