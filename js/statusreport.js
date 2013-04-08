selected_row_ref = ""
function selectRow(ref, desc, size, time, conf) {
    if (selected_row_ref) {
        document.getElementById(selected_row_ref).style.backgroundColor = selected_row_color
    }
    selected_row_ref = ref;
    selected_row_color =  document.getElementById(selected_row_ref).style.backgroundColor;
    document.getElementById(selected_row_ref).style.backgroundColor = "#3366CC";
    document.getElementById("lblreportdesc").innerHTML = desc;
    document.getElementById("lblreportsize").innerHTML = size;
    document.getElementById("lblreporttime").innerHTML = time;
    document.getElementById("lblreportconf").innerHTML = conf;
}
function convert_bytes(bytes, precision)
{  
    var kilobyte = 1024;
    var megabyte = kilobyte * 1024;
    var gigabyte = megabyte * 1024;
    var terabyte = gigabyte * 1024;
   
    if ((bytes >= 0) && (bytes < kilobyte)) {
        return bytes + ' B';
 
    } else if ((bytes >= kilobyte) && (bytes < megabyte)) {
        return (bytes / kilobyte).toFixed(precision) + ' KB';
 
    } else if ((bytes >= megabyte) && (bytes < gigabyte)) {
        return (bytes / megabyte).toFixed(precision) + ' MB';
 
    } else if ((bytes >= gigabyte) && (bytes < terabyte)) {
        return (bytes / gigabyte).toFixed(precision) + ' GB';
 
    } else if (bytes >= terabyte) {
        return (bytes / terabyte).toFixed(precision) + ' TB';
 
    } else {
        return bytes + ' B';
    }
}
function changeAll(check) {
    tablereport = document.getElementById("tablereport");
    for (i=0; i < tablereport.rows.length; i++) {
        if (tablereport.rows[i].cells[0].childNodes[0].checked != check) {
            tablereport.rows[i].cells[0].childNodes[0].checked = check;
        }
    }
    updateSizeAndTime();
}

function updateSizeAndTime() {
    tablereport = document.getElementById("tablereport");
    totalsize = 0;
    totaltime = 0;
    for (i=0; i < tablereport.rows.length; i++) {
        if (tablereport.rows[i].cells[0].childNodes[0].checked) {
            totalsize += parseInt(tablereport.rows[i].cells[3].innerHTML);
            totaltime += parseInt(tablereport.rows[i].cells[4].innerHTML);
        }
    } 
    document.getElementById("lblreportotalsize").innerHTML = "< " + convert_bytes(totalsize, 2) + "";
    document.getElementById("lblreportotaltime").innerHTML = "< " + Math.round(totaltime/60) + " minutes";
}

function on_acceptstatusreport_clicked() {
        document.getElementById("loading").style.display = "";
        var refs = new Array(); 
        tablereport = document.getElementById("tablereport");
        for (i=0; i < tablereport.rows.length; i++) {
            if (tablereport.rows[i].cells[0].childNodes[0].checked) {
                refs.push(tablereport.rows[i].cells[0].childNodes[0].value);
            }
        }
        refs = refs.join(",");
        url = "host_download_status_report?host=" + parent.selected_ip + "&ref=" + parent.selected_ref + "&name=" + parent.selected_name + "&refs=" + refs;
        document.location = url;
}
