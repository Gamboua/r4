<?php
$host = '127.0.0.1'; // Database hostname
$db = 'platform'; // Database name
$username = 'sysuser';// Database username
$password = 'w!#jp3c5FHmR2';// Database password

$conn = new PDO("mysql:host={$host};dbname={$db}", $username, $password, [
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_NUM,
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::MYSQL_ATTR_INIT_COMMAND => 'SET NAMES utf8'
]);
