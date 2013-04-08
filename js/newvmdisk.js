var selected_row_ref = "";
function selectRow(ref) {
    if (selected_row_ref && document.getElementById(selected_row_ref)) {
        document.getElementById(selected_row_ref).style.backgroundColor = selected_row_color
    }
    selected_row_ref = ref;
    selected_row_color =  document.getElementById(selected_row_ref).style.backgroundColor;
    document.getElementById(selected_row_ref).style.backgroundColor = "#3366CC";
}
function setSize(edit) {
    if (edit) {
        document.getElementById("newvmdisksize").value = parent.document.getElementById(parent.selected_stg_ref).cells[0].innerHTML;
    }
}
function on_acceptnewvmdisk_clicked(edit) {
    if (!selected_row_ref) {
        parent.hidePopWin(false);
        return;
    }
    if (!edit) {
        tablenewstorage = parent.document.getElementById("tablenewstorage")
        row = document.createElement("TR");    
        row.setAttribute("class", "row");
        row.style.clear = "both";
        row.id = "newstg" + (tablenewstorage.rows.length-1);
        row.setAttribute("onclick", "selectStgRow('newstg" + (tablenewstorage.rows.length-1) + "');");
        cell1 = document.createElement("TD");
        cell2 = document.createElement("TD");
        cell3 = document.createElement("TD");
        cell4 = document.createElement("TD");

        content1 = document.createTextNode(document.getElementById("newvmdisksize").value);
        cell1.appendChild(content1);

        content2 = document.createTextNode(document.getElementById(selected_row_ref).cells[0].innerHTML);
        cell2.appendChild(content2);

        content3 = document.createTextNode(document.getElementById(selected_row_ref).cells[4].innerHTML);
        cell3.appendChild(content3);

        content4 = document.createTextNode(document.getElementById(selected_row_ref).cells[5].innerHTML);
        cell4.appendChild(content4);
        cell4.setAttribute("style", "display: none;");

        row.appendChild(cell1);
        row.appendChild(cell2);
        row.appendChild(cell3);
        row.appendChild(cell4);
        tablenewstorage.appendChild(row);
    } else  {
        row = parent.document.getElementById(parent.selected_stg_ref);
        alert(row.innerHTML);
        row.cells[0].innerHTML = document.getElementById("newvmdisksize").value;
        row.cells[1].innerHTML = document.getElementById(selected_row_ref).cells[0].innerHTML;
        row.cells[2].innerHTML = document.getElementById(selected_row_ref).cells[4].innerHTML;
        row.cells[3].innerHTML = document.getElementById(selected_row_ref).cells[5].innerHTML;
    }
    parent.hidePopWin(false);
}
