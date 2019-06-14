<?php
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

if(!isset($_SERVER['HTTP_REFERER'])) {
    exit;
}

require 'vendor/autoload.php';
include 'connection.php';
// Mobile detect
$detect = new Mobile_Detect();
$mobileDetect = false;

if( $detect->isTablet() ){
    $mobileDetect = 'tablet';
    $querySrc = "a.tablet=1";
    $dataSelect = 'REPLACE(REPLACE(a.template_domain_tablet, "\r\n",""),"\t","") as template_domain_tablet,a.week_hour,a.frequency';
}else if($detect->isMobile()){
    $mobileDetect = 'mobile';
    $querySrc = "a.mobile=1";
    $dataSelect = 'REPLACE(REPLACE(a.template_domain_mobile, "\r\n",""),"\t","") as template_domain_mobile,a.week_hour,a.frequency';
}else{
    $mobileDetect = 'desktop';
    $querySrc = "a.desktop=1";
    $dataSelect = 'REPLACE(REPLACE(a.template_domain, "\r\n",""),"\t","") as template_domain,a.week_hour,a.frequency';
}
$cssSelect = 'REPLACE(REPLACE(c.css, "\r\n",""),"\t","") as css';
$url = parse_url($_SERVER['HTTP_REFERER']); // Pega a URL
@parse_str($url['query'], $q); // Pega variaveis da url
preg_match("/[^\.\/]+\.[^\.\/]+$/", $url['host'], $matches);
$queryParams = [
    'domain' => $matches[0],
    'id' =>(int)$_GET['r4p'],
    'dateTime' => (int)($_GET['tz']/1000)
];

//BUSCA NO REDIS
try{
    $redisClient = new Redis();
    $redisClient->connect('192.168.226.34');
    $redisClient->setOption(\Redis::OPT_SERIALIZER, \Redis::SERIALIZER_IGBINARY);
    $redisClient->select(1);
}catch(Exception $e){
    die($e->getMessage());
}

if(!$queryParams['domain'] || !$queryParams['id']){
    $rows = [];
}else{
    #die($dataSelect);
    #$rows = $redisClient->get(md5('dataFp:' . $queryParams['domain'].$queryParams['id']));
    #if($rows === false) {
        //Busca os dados do servidor
        if($queryParams['domain'] && $queryParams['id']){
            $query = $conn->prepare("SELECT $dataSelect,$cssSelect,c.identifier FROM premiums as a INNER JOIN domains as b ON a.domain_id = b.id INNER JOIN fpconfigs as c on a.fpconfig_id = c.id WHERE b.domain = :domain_name and b.status = 1 and a.status=1 and b.user_id = :user_id and $querySrc");
            $query->bindParam(':domain_name', $queryParams['domain'], PDO::PARAM_STR);
            $query->bindParam(':user_id', $queryParams['id'], PDO::PARAM_INT);
            $query->execute();
            $rows = $query->fetchAll(PDO::FETCH_ASSOC);
        }
        #$redisClient->setex(md5('dataFp:' . $queryParams['domain'].$queryParams['id']), 300, $rows);
        #exit('ENTROU AQUI');
   # }
}


//se não achar os dados
if(!count($rows)){
    ob_start();
    header('Content-Type: application/javascript');
    ?>
    console.error('R4YOU-LOG: unauthorized domain');
    <?php
    ob_end_flush();
    exit();
}

$templates = array();
foreach ($rows as $key =>  $row){
    //template iframe
    switch($mobileDetect){
        case  'mobile':
            $templates[$key]['html'] = json_encode($row['template_domain_mobile'] , JSON_HEX_TAG|JSON_HEX_APOS|JSON_HEX_QUOT|JSON_HEX_AMP);
            break;

        case 'tablet':
            $templates[$key]['html'] = json_encode($row['template_domain_tablet'] , JSON_HEX_TAG|JSON_HEX_APOS|JSON_HEX_QUOT|JSON_HEX_AMP);
            break;

        case 'desktop':
            $templates[$key]['html'] = json_encode($row['template_domain'] , JSON_HEX_TAG|JSON_HEX_APOS|JSON_HEX_QUOT|JSON_HEX_AMP);
            break;
    }

    $templates[$key]['css'] = json_encode($row['css'] , JSON_HEX_TAG|JSON_HEX_APOS|JSON_HEX_QUOT|JSON_HEX_AMP);
    $templates[$key]['identifier'] = json_encode($row['identifier'] , JSON_HEX_TAG|JSON_HEX_APOS|JSON_HEX_QUOT|JSON_HEX_AMP);
    $templates[$key]['first_view']= false;

    $frequencia = isset($_COOKIE['r4_frequency']) ? json_decode($_COOKIE['r4_frequency'], true) : [];

    $templates[$key]['show'] = true;
    //verifica se tem regra de frequencia
    if(!$row['frequency']) {
        $frequencia['__'.$row['identifier']]['_qt'] = 0;
        $frequencia['__'.$row['identifier']]['tz'] = $_GET['tz'];
        setcookie('r4_frequency', json_encode($frequencia), time() + (86400 * 30), "/"); // 86400 = 1 day

    }else{
        $frequencia_config = json_decode($row['frequency'],true);
        if(!isset($frequencia['__'.$row['identifier']]) || !isset($frequencia_config['minutos'])){
            if(!isset($frequencia_config['minutos'])){
                //não possui tempo para frequencia
                $templates[$key]['show'] = true;
            }else {
                //first view
                $templates[$key]['first_view']= true;
                $frequencia['__'.$row['identifier']]['_qt'] = 0;
                $frequencia['__'.$row['identifier']]['tz'] = $_GET['tz'];
                setcookie('r4_frequency', json_encode($frequencia), time() + (86400 * 30), "/"); // 86400 = 1 day
            }

        }else{
            //pega antigos dados de cookies
            $templates[$key]['first_view'] = true;
            $oldTz = $frequencia['__'.$row['identifier']]['tz'];
            //var_dump(( ($oldTz + ($frequencia_config['minutos'] * 60)/1000 ) > $_GET['tz']));
            if(!($oldTz + ($frequencia_config['minutos'] * 60)*1000  > $_GET['tz'])){
                //expirou
                $frequencia['__'.$row['identifier']]['_qt'] = 0;
                $frequencia['__'.$row['identifier']]['tz'] = $_GET['tz'];
                setcookie('r4_frequency', json_encode($frequencia), strtotime( '+1 year' ), "/");
            }else{

                //verifica quantidade
                if(!isset($frequencia_config['quantidade'])){
                    $templates[$key]['show'] = true;
                }
                elseif($frequencia['__'.$row['identifier']]['_qt'] >= $frequencia_config['quantidade']){
                    $templates[$key]['show'] = false;
                }

            }
        }
    }
}
ob_start();
header('Content-Type: application/javascript');
$userAgent = $_SERVER['HTTP_USER_AGENT'];
?>

function R4you(){
    this.d = !!(self.frameElement && (self.frameElement + '').indexOf('HTMLIFrameElement') > -1) ? window.top.document : window.document;
    this.b = this.d.body || this.d.getElementsByTagName("body")[0];
    this.elms = [];
    this.eshow = false;
}

R4you.prototype.addEvent = function (o, e, f) {
    if (o.addEventListener)
        o.addEventListener(e, f, false);
    else if (o.attachEvent)
        o.attachEvent("on" + e, f);
    else
        o["on" + e] = f;
};

R4you.prototype.cr4 = function(){

        <?php foreach($rows as $key=> $row): if($templates[$key]['show']): ?>
            if(this.checkEnabled()){
                //adiciona o css na página
                var css = <?php echo $templates[$key]['css']; ?>;
                var styleEl = document.createElement('style');
                styleEl.type = 'text/css';
                styleEl.appendChild(document.createTextNode(css));
                document.getElementsByTagName("head")[0].appendChild(styleEl);
                //cria div container
                var eC = document.createElement('div');
                eC.id = <?php echo $templates[$key]['identifier']; ?>;
                //botao de fechar
                 var closeBtn = document.createElement('div');
                 closeBtn.classList.add("adsR4Close");
                 closeBtn.innerHTML = "X";
                 eC.appendChild(closeBtn);
                 closeBtn.onclick = function(){
                    this.parentElement.remove()
                 };
                //iframe publicidade
                var ist = "height:100%;border: 0px;";
                var i = this.d.createElement("iframe");
                i.className = "r4_fp_ads";
                i.src = "about:blank";
                i.style.cssText = ist;

                //joga o html da publicidade cadastrada no banco de dados
                this.addEvent(i, "load", function () {
                    i.contentWindow.document.write(<?php echo $templates[$key]['html']; ?>);
                });
                i.onmouseenter = function() {
                    console.log("MOUSEOVER");
                    this.parentElement.classList.add('r4iframehover')
                }
                eC.onmouseleave  = function() {
                    console.log("MOUSEOUT");
                   this.classList.remove('r4iframehover')
                }
                eC.appendChild(i);
                
                document.body.appendChild(eC);
            }
        <?php endif; endforeach; ?>
}

R4you.prototype.checkEnabled = function(){
    var d = new Date();
    var w = d.getDay();
    var n = d.getHours();
    var eh = <?php echo $row['week_hour'] ?>;
    console.log(eh[w][n] == 1);
    return eh[w][n] == 1;
}

function r4getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i <ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

R4you.prototype.showClose = function (i) {
    var ck = r4getCookie('r4_frequency');
    if(ck){
        var cookies = JSON.parse(ck);
        cookies["__"+i.parentElement.id]['_qt'] = cookies["__"+i.parentElement.id]['_qt'] + 1;
        var expires = 365 * 24 * 60 * 60 * 1000;
        console.log(JSON.stringify(cookies));
        document.cookie = 'r4_frequency' + "=" + JSON.stringify(cookies) + ";" + expires + ";path=/";
    }
    var closeBtn = i.previousElementSibling;
    if(closeBtn.className == 'adsR4Close'){
        closeBtn.style.display = 'block';
    }
}
R4you.prototype.hiddenIframe = function(i){
    console.log('R4YOU-LOG: removed');
    i.parentElement.style.display = 'none';
}

R4you.prototype.showFullScreenClose = function(i){
    console.log('R4YOU-LOG: Create close button');
    var parentElement = i.parentElement;
    var closeBtnFullScreen = document.createElement('div');
    closeBtnFullScreen.classList.add("r4_fullscreenclose");
    closeBtnFullScreen.innerHTML = "FECHAR ANÚNCIO";
    parentElement.appendChild(closeBtnFullScreen);
    closeBtnFullScreen.onclick = function(){
        this.parentElement.remove()
    };
}
R4you.prototype.showData = function(){
    if(this.eshow == false){
        this.eshow = true;
        for(var i=0; i<this.elms.length; i++) {
            console.log(i, this.elms[i]);
        }
    }


}

var r4Ads = new R4you();

window.onscroll = function() {
    if(!r4Ads.eshow){
        console.log("SHOW")
        r4Ads.eshow = true;
        r4Ads.cr4();
    }
}
<?php ob_end_flush(); ?>