var selected_index = 0;
function on_combopoolmaster_changed(el) {
    document.getElementById(el.options[selected_index].value).getElementsByTagName("INPUT")[0].disabled = false;
    document.getElementById(el.options[selected_index].value).getElementsByTagName("TD")[1].style.color = "";
    selected_index = el.selectedIndex;
    document.getElementById(el.options[selected_index].value).getElementsByTagName("INPUT")[0].disabled = true;
    document.getElementById(el.options[selected_index].value).getElementsByTagName("TD")[1].style.color = "gray";
}

function on_acceptnewpool_clicked() {
   var name = document.getElementById("txtpoolname").value;
   var desc = document.getElementById("txtpooldesc").value; 
   var combopoolmaster = document.getElementById("combopoolmaster")
   var master = combopoolmaster.options[combopoolmaster.selectedIndex].value;
   var slaves = new Array();
   for (index in document.getElementById("poolslaves").getElementsByTagName("INPUT")) {
        element = document.getElementById("poolslaves").getElementsByTagName("INPUT")[index]
        if (element.disabled == false && element.checked == true) {
            slaves.push(element.value);
        }
   }
    var client = new XMLHttpRequest();
    client.open("GET", "create_pool?name=" + name + "&desc=" + desc + "&master=" + master + "&slaves=" + slaves.join(","), true);
    client.onreadystatechange = function() {
        if(this.readyState == 4 && this.status == 200) {
            if (this.responseText != "OK") {
                alert(this.responseText);
            }
            parent.hidePopWin(false);
        } else if (this.readyState == 4 && this.status != 200) {
            parent.document.getElementById("statusbar").innerHTML = "error on_acceptnewpool_clicked";
        }            
    }
    client.send(null)    

}
