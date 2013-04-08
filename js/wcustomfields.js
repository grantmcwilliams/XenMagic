function deleteCustomField() {
    if (treecustomfields.selectedIndex) {
        treecustomfields = document.getElementById("treecustomfields");
        treecustomfields.remove(treecustomfields.selectedIndex);
    }
}
function addCustomField() {
    var treecustomfields = document.getElementById("treecustomfields");
    var option = document.createElement('option');
    var combocustomfields = document.getElementById("combocustomfields");
    option.text = document.getElementById("namecustomfields").value + " (" + combocustomfields.options[combocustomfields.selectedIndex].value + ")";
    option.value =  document.getElementById("namecustomfields").value + ":" + combocustomfields.options[combocustomfields.selectedIndex].value;
    try {
      treecustomfields.add(option, null); // standards compliant; doesn't work in IE
    }
    catch(ex) {
      treecustomfields.add(option); // IE only
    }
}

function on_acceptwcustomfields_accepted() {
    treecustomfields = document.getElementById("treecustomfields")
    values = []
    for (i = 0; i < treecustomfields.options.length; i++) {
        values[i] = treecustomfields.options[i].value;
    }
    var client = new XMLHttpRequest();
    client.open("GET", "set_pool_custom_fields?host=" + parent.parent.selected_host + "&values=" + JSON.stringify(values), true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            alert("FIXME: close properties window and open again to see new custom field");
            parent.hidePopWin(false);
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error on_acceptwcustomfields_accepted";
        }            
    }
    client.send(null)    
}
