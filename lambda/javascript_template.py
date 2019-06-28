PHP_FUNCTION_LOOP = """
if(this.checkEnabled()){{
    //adiciona o css na página
    var css = {templates_key_css};
    var styleEl = document.createElement('style');
    styleEl.type = 'text/css';
    styleEl.appendChild(document.createTextNode(css));
    document.getElementsByTagName("head")[0].appendChild(styleEl);
    //cria div container
    var eC = document.createElement('div');
    eC.id = {templates_key_identifier};
    //botao de fechar
        var closeBtn = document.createElement('div');
        closeBtn.classList.add("adsR4Close");
        closeBtn.innerHTML = "X";
        eC.appendChild(closeBtn);
        closeBtn.onclick = function(){{
        this.parentElement.remove()
        }};
    //iframe publicidade
    var ist = "height:100%;border: 0px;";
    var i = this.d.createElement("iframe");
    i.className = "r4_fp_ads";
    i.src = "about:blank";
    i.style.cssText = ist;

    //joga o html da publicidade cadastrada no banco de dados
    this.addEvent(i, "load", function () {{
        i.contentWindow.document.write({templates_key_html});
    }});
    i.onmouseenter = function() {{
        console.log("MOUSEOVER");
        this.parentElement.classList.add('r4iframehover')
    }}
    eC.onmouseleave  = function() {{
        console.log("MOUSEOUT");
        this.classList.remove('r4iframehover')
    }}
    eC.appendChild(i);

    document.body.appendChild(eC);
"""

RESPONSE_TEMPLATE = """
function R4you(){{
    this.d = !!(self.frameElement && (self.frameElement + '').indexOf('HTMLIFrameElement') > -1) ? window.top.document : window.document;
    this.b = this.d.body || this.d.getElementsByTagName("body")[0];
    this.elms = [];
    this.eshow = false;
}}

R4you.prototype.addEvent = function (o, e, f) {{
    if (o.addEventListener)
        o.addEventListener(e, f, false);
    else if (o.attachEvent)
        o.attachEvent("on" + e, f);
    else
        o["on" + e] = f;
}};

R4you.prototype.cr4 = function(){{
    {loop}
}}

R4you.prototype.checkEnabled = function(){{
    var d = new Date();
    var w = d.getDay();
    var n = d.getHours();
    var eh = {row_weekhour}>;
    console.log(eh[w][n] == 1);
    return eh[w][n] == 1;
}}

function r4getCookie(cname) {{
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i <ca.length; i++) {{
        var c = ca[i];
        while (c.charAt(0) == ' ') {{
            c = c.substring(1);
        }}
        if (c.indexOf(name) == 0) {{
            return c.substring(name.length, c.length);
        }}
    }}
    return "";
}}

R4you.prototype.showClose = function (i) {{
    var ck = r4getCookie('r4_frequency');
    if(ck){{
        var cookies = JSON.parse(ck);
        cookies["__"+i.parentElement.id]['_qt'] = cookies["__"+i.parentElement.id]['_qt'] + 1;
        var expires = 365 * 24 * 60 * 60 * 1000;
        console.log(JSON.stringify(cookies));
        document.cookie = 'r4_frequency' + "=" + JSON.stringify(cookies) + ";" + expires + ";path=/";
    }}
    var closeBtn = i.previousElementSibling;
    if(closeBtn.className == 'adsR4Close'){{
        closeBtn.style.display = 'block';
    }}
}}
R4you.prototype.hiddenIframe = function(i){{
    console.log('R4YOU-LOG: removed');
    i.parentElement.style.display = 'none';
}}

R4you.prototype.showFullScreenClose = function(i){{
    console.log('R4YOU-LOG: Create close button');
    var parentElement = i.parentElement;
    var closeBtnFullScreen = document.createElement('div');
    closeBtnFullScreen.classList.add("r4_fullscreenclose");
    closeBtnFullScreen.innerHTML = "FECHAR ANÚNCIO";
    parentElement.appendChild(closeBtnFullScreen);
    closeBtnFullScreen.onclick = function(){{
        this.parentElement.remove()
    }};
}}
R4you.prototype.showData = function(){{
    if(this.eshow == false){{
        this.eshow = true;
        for(var i=0; i<this.elms.length; i++) {{
            console.log(i, this.elms[i]);
        }}
    }}


}}

var r4Ads = new R4you();

window.onscroll = function() {{
    if(!r4Ads.eshow){{
        console.log("SHOW")
        r4Ads.eshow = true;
        r4Ads.cr4();
    }}
}}
"""