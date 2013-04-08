tabs = new Array();
tabs["pool"] = "framepoolgeneral"
tabs["home"] = "framehome"
tabs["vm"] = "framevmgeneral"
tabs["host"] = "framesearch"
tabs["template"] = "frametplgeneral"
tabs["custom_template"] = "frametplgeneral"
tabs["storage"] = "framestggeneral"




last_widget = ""
function on_treevm_button_press_event(event, widget, name, type, actions, image, ref, host, type, ip, uuid, state) {
    // Set selected variables
    selected_actions = actions
    selected_type = type
    selected_ref = ref 
    selected_hostname = host 
    selected_type = type
    selected_host = host 
    selected_ip = ip
    selected_uuid = uuid 
    selected_state = state
    selected_name = name
    // Update toolbar and menubar
    update_toolbar()
    update_menubar()

    // Set background color
    if (last_widget) {
        last_widget.style.backgroundColor="#fcfcfc";
        last_widget.style.color="black";
    }
    last_widget = widget
    widget.style.backgroundColor="#4b6983";
    widget.style.color="white";
    widget.style.zIndex="-100";
    if (type == "server" && state == "Disconnected") {
        return;
    } 

    // update tabs
    var client = new XMLHttpRequest();
    client.onreadystatechange = update_tabs;
    client.open("GET", "tabs?type=" + type + "&state=" + state);
    client.send();
    on_tabbox_focus_tab("", tabs[type])


    // Update header
    document.getElementById("headlabel").innerHTML = name;
    document.getElementById("headimage").src = image;

    return false;
}

function update_tabs() {
    // Function handler when for update tabs
    if(this.readyState == 4 && this.status == 200) {
        // Set the tabs
        document.getElementById("tabbox").innerHTML = this.responseText;
    } else if (this.readyState == 4 && this.status != 200) {
        alert("error updating tabs..");
    }
}
