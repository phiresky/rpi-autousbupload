<?php
error_reporting(-1);
date_default_timezone_set('Europe/Berlin');

if(!isset($_POST['logdata'])) die('e: no data');

try {
	if(!is_dir("uploadlogs")) mkdir("uploadlogs");
    $data = $_POST['logdata'];
    file_put_contents('uploadlogs/'.date('Y-m').'.txt',$data,FILE_APPEND);
    exit('s'); // success
} catch (Exception $e) {
    die('e: '.$e->getMessage()); // error
}

?>
