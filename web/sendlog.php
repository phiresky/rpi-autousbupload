<?php
error_reporting(-1);
date_default_timezone_set('Europe/Berlin');

if(!isset($_POST['logdata'])) die('e: no data');

try {
	if(!is_dir("uploadlogs")) mkdir("uploadlogs");
    $data = $_POST['logdata'];
	$month = date('Y-m');
	$nextmonth = date('Y-m',time()+86400);
   file_put_contents("uploadlogs/$month.txt",$data,FILE_APPEND);
	if($month!=$nextmonth)
        file_put_contents("uploadlogs/$nextmonth.txt",$data,FILE_APPEND);
    exit('s'); // success
} catch (Exception $e) {
    die('e: '.$e->getMessage()); // error
}

?>
