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