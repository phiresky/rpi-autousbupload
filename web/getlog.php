<?php
header("Content-Type: text/plain");
/*function tail($filename, $lines = 10) {
	$data = '';
	$fp = fopen($filename, "r");
	$block = 4096;
	$max = filesize($filename);

	for($len = 0; $len < $max; $len += $block) {
		$seekSize = ($max - $len > $block) ? $block : $max - $len;
		fseek($fp, ($len + $seekSize) * -1, SEEK_END);
		$data = fread($fp, $seekSize) . $data;

		if(substr_count($data, "\n") >= $lines + 1) {
			/* Make sure that the last line ends with a '\n' * /
			if(substr($data, strlen($data)-1, 1) !== "\n") {
				$data .= "\n";
			}

			preg_match("!(.*?\n){". $lines ."}$!", $data, $match);
			fclose($fp);
			return $match[0];
		}
	}
	fclose($fp);
	return $data; 
}*/
$date = date("Y-m");
//$linecount = isset($_GET['limit'])?$_GET['limit']:0;
if(isset($_GET['date'])) $date = preg_replace('/[^0-9-]/','', $_GET['date']);
$begin = 0;
if(isset($_GET['begin'])) $begin = intval($_GET['begin']);
$fname = "uploadlogs/$date.txt";
if(is_file($fname)) {
	$file = new SplFileObject($fname);
	$file->seek($begin);
	print($file->current());
	$file->fpassthru();
}
?>
