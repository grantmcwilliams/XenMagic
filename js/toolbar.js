function oc(a)
{
  if (a) {
      var o = {};
      for(var i=0;i<a.length;i++)
      {
        o[a[i]]='';
      }
      return o;
  }    
  return Array();
}

function update_toolbar() {
    for (children in document.getElementById("menutoolbar").childNodes) {
        if (document.getElementById("menutoolbar").childNodes[children].nodeName == "DIV") {
            name = document.getElementById("menutoolbar").childNodes[children].getAttribute("id")
            if (name.substring(0, 3) == "tb_") {
                element =  document.getElementById(name)
                if (name.substring(3) in oc(selected_actions)) {
                    document.getElementById(name + "_enabled").style.display = "";
                    document.getElementById(name + "_disabled").style.display = "none";
                } else {
                    document.getElementById(name + "_enabled").style.display = "none";
                    document.getElementById(name + "_disabled").style.display = "";
                }
            }
        }
    }
}
