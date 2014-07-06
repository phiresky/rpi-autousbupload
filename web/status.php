<!doctype html>
<html lang=de ng-app="raspberries">
<meta charset="utf-8">
<title>Raspberries upload status</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel=stylesheet href="https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap.min.css">
<style>body{padding-top:90px;} .marg{margin:1em;}
.nav, .pagination, .carousel, .panel-title a { cursor: pointer; }
</style>
<div class="navbar navbar-default navbar-fixed-top" role="navigation">
<div class="container"><h2>Raspberry upload status</h2></div>
</div>
<div class="container" ng-controller="RaspberryController as ctrl">
    <accordion>
        <accordion-group ng-repeat="rasp in raspberries" heading="{{rasp.name}}" is-open="true">
            <div class="well row marg" ng-repeat="upload in rasp.uploads">
                <div class="col-xs-6 col-md-4">
                    <p>Upload {{rasp.uploads.length-$index}} / {{rasp.uploads.length}}:</p>
                    <p>Begun: {{upload.begin|date:"medium"}}</p>
                    <p ng-if="upload.complete">Completed: {{upload.complete|date:"medium"}}</p>
                    <p>Files: {{upload.files|xofy}}</p>
                    <p>Label: {{upload.label}}</p>
                </div>
                <div class="col-xs-6 col-md-8">
                    <progressbar ng-if="!upload.error" max="upload.bytes.total" class="{{(!upload.complete?'active':'')+' progress-striped'}}" value="upload.bytes.current">{{upload.bytes|xofy:'bytes'}}</progressbar>
                    <div ng-if="!upload.complete&&!upload.error" class="alert alert-info">
                        Upload in progress
                    </div>
                    <alert ng-if="upload.complete" type="'success'">Upload complete!</alert>
                    <alert ng-if="upload.error" type="'danger'">Upload error: <pre>{{upload.error}}</pre></alert>
                </div>
            </div>
		</accordion-group>
    </accordion>
    <div ng-hide="logPointer" class="alert alert-info">No raspberries were found</div>
</div>

<script src="https://ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.7.0/moment.min.js"></script>
<script src="https://ajax.googleapis.com/ajax/libs/angularjs/1.3.0-beta.14/angular.min.js"></script>
<script src="//cdnjs.cloudflare.com/ajax/libs/angular-ui-bootstrap/0.10.0/ui-bootstrap-tpls.min.js"></script>
<script>
var app = angular.module("raspberries",['ui.bootstrap']);

var LL = {
	'TIME':0,
	'NAME':1,
	'TYPE':2,
	'WHAT':3,
	'INFO':4
}
function parseAscDate(inp) {
	var argArr = [null].concat("2014-07-05 23:01:10,454".split(/[^0-9]/))
	var constructor = Date.bind.apply(Date, argArr);
	return new constructor();	
}
function Raspberry(name) {
	this.log = [];
	this.name = name;
	this.uploads = [];
}

Raspberry.prototype.getStatus = function() {
	return this.log[this.log.length-1][3];
}
Raspberry.prototype.logAdd = function(line) {
	this.log.push(line);
	if(line[LL.TYPE]==="ERROR") {
		if(this.uploads[0]) this.uploads[0].error = line.join("|");
		this.error = line.join("|");

	}
	switch(line[LL.WHAT]) {
	case "uploadBegin": 
		this.uploads.unshift({
			begin:parseAscDate(line[LL.TIME]),
			bytes:{current:0,total:line[LL.INFO+3]},
			files:{current:0,total:line[LL.INFO+2]},
			label:line[LL.INFO+1]
		});
	break;
	case "uploadProgress": 
		var progress = line[LL.INFO+1].split("/");
		var files = line[LL.INFO].split("/");
		this.uploads[0].bytes = {current:progress[0],total:progress[1]}
		this.uploads[0].files = {current:files[0],total:files[1]}
	break;
	case "uploadComplete": 
		this.uploads[0].complete = parseAscDate(line[LL.TIME]);
		this.uploads[0].bytes.current=line[LL.INFO+1];
	break;
	}
}
app.filter('xofy', function($filter) {
	return function(obj,filter) {
		if(filter===undefined) return obj.current + " / " + obj.total;
		return $filter(filter)(obj.current) + " / " + $filter(filter)(obj.total);
	}
});

app.filter('bytes', function() {
	return function(bytes, precision) {
		if (bytes === 0) return "0 bytes";
		if (isNaN(parseFloat(bytes)) || !isFinite(bytes)) return '-';
		if (typeof precision === 'undefined') precision = 1;
		var units = ['bytes', 'kB', 'MB', 'GB', 'TB', 'PB'],
			number = Math.floor(Math.log(bytes) / Math.log(1024));
		return (bytes / Math.pow(1024, Math.floor(number))).toFixed(precision) +  ' ' + units[number];
	}
});
String.prototype.endsWith = function(suffix) {
    return this.indexOf(suffix, this.length - suffix.length) !== -1;
};

app.controller('RaspberryController', function($scope, $interval, $http) {
	$scope.raspberries={};
	$scope.logPointer=0;
	$scope.lastUpdate=null;
	function updateGet() {
		$http.get("getlog.php?begin="+encodeURIComponent($scope.logPointer)).success(function(resp) {
			$scope.lastUpdate=new Date();
			var lines = resp.split("\n");
			lines.pop();
			var line = [];
			var multiline = false;
			for(var l=0;l<lines.length;l++) {
				if(!lines[l].endsWith("|END|")) {
					if(!multiline) line=[];
					multiline = true;
					if(line.length==0) line = lines[l].split("|");
					else line[line.length-1]+="\n"+lines[l];
					continue;
				}
				if(multiline) line[line.length-1] += "\n"+lines[l];
				else line = lines[l].split("|");
				multiline = false;
				//if(line.length<3) continue;
				if(!$scope.raspberries[line[LL.NAME]]) $scope.raspberries[line[LL.NAME]] = new Raspberry(line[LL.NAME]);
				$scope.raspberries[line[LL.NAME]].logAdd(line);
			}
			$scope.logPointer += lines.length; 
		});
	};
	updateGet();
	$interval(updateGet,10*1000);
	_a=$scope;
});

</script>
