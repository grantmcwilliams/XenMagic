var selected_row_ref = "";
var selected_host_ref = "";
function selectRow(ref, host_ref) {
    if (selected_row_ref) {
        document.getElementById(selected_row_ref).style.backgroundColor = selected_row_color
    }
    selected_row_ref = ref;
    selected_host_ref = host_ref;
    selected_row_color =  document.getElementById(selected_row_ref).style.backgroundColor;
    document.getElementById(selected_row_ref).style.backgroundColor = "#3366CC";
    
}
function on_btalertdismiss_clicked() {
    if (!selected_row_ref) {
        alert("Please select an alert to dismiss");
    } else {
        var client = new XMLHttpRequest();
        client.onreadystatechange = function () {
            if(this.readyState == 4 && this.status == 200) {
                if (this.responseText != "OK") {
                    alert(this.responseText);
                }
            } else if (this.readyState == 4 && this.status != 200) {
                alert("Error on callFunction()");
            }
        }
        client.open("GET", "do_action?action=dismiss_alert&ref=" + selected_row_ref + "&host=" + selected_host_ref);
        client.send()
    }
}

