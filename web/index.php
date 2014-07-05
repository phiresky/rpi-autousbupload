Log:
<pre>
<?php
function tail($filename, $lines = 10) {
	$data = '';
	$fp = fopen($filename, "r");
	$block = 4096;
	$max = filesize($filename);

	for($len = 0; $len < $max; $len += $block) {
		$seekSize = ($max - $len > $block) ? $block : $max - $len;
		fseek($fp, ($len + $seekSize) * -1, SEEK_END);
		$data = fread($fp, $seekSize) . $data;

		if(substr_count($data, "\n") >= $lines + 1) {
			/* Make sure that the last line ends with a '\n' */
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
}
print(tail("uploadlogs/".date("Y-m-d").".txt", 20)); 
?>
</pre>
