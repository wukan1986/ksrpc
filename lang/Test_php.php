<?php
function ksrpc_call($base_url, $func, $args, $kwargs, $token=null, $fmt='csv', $cache_get=true, $cache_expire=86400, $async_remote=true) {
    $url = "$base_url?func=$func&fmt=$fmt&cache_get=$cache_get&cache_expire=$cache_expire&async_remote=$async_remote";
    $postdata = json_encode(array('args' => $args,'kwargs' => $kwargs));
    $options = array(
        'http' => array(
            'method' => 'POST',
            'header' => ['Content-Type:application/json', "Authorization:Bearer $token"],
            'content' => $postdata,
            )
        );
    $context = stream_context_create($options);
    $result = file_get_contents($url, false, $context);
    return $result;
}

$token = 'secret-token-1';
$url = 'http://127.0.0.1:8000/api/post';

$res = ksrpc_call($url,'demo.div', array(1,2), array(), $token);
print_r($res);
$res = ksrpc_call($url,'demo.div', array(), array('a'=>1, 'b'=>3), $token);
print_r($res);
$res = ksrpc_call($url,'demo.test', array(), array(), $token);
print_r($res);
?>