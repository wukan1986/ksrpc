var request = require('request');
var util = require('util');

function ksrpc_call(base_url, func, args, kwargs, fmt, cache_get, cache_expire, async_remote, token) {
	var url= util.format("%s?func=%s&fmt=%s&cache_get=%d&cache_expire=%d&async_remote=%d",
	    base_url, func, fmt, cache_get,cache_expire, async_remote);
	var data = {"args": args, "kwargs": kwargs};
  
	request({
		url: url,
		method: "POST",
		headers: {'Authorization': 'Bearer '+token},
		body:JSON.stringify(data)
		}, function(error, response, body) {
		    console.log(body)
	});
}
var TOKEN="secret-token-1";
var URL = "http://127.0.0.1:8000/api/post";
ksrpc_call(URL, "demo.div", [], {'a':2,'b':3}, "csv", true, 86400, true, TOKEN)
ksrpc_call(URL, "demo.test", [], {}, "csv", true, 86400, true, TOKEN)