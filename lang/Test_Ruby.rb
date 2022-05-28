require 'uri'
require 'net/https'
require 'json'
def ksrpc_call(base_url, func, args, kwargs, fmt, cache_get, cache_expire, async_remote, token)
    uri = URI.parse("#{base_url}")
    https = Net::HTTP.new(uri.host, uri.port)
    req = Net::HTTP::Post.new("#{uri.path}?func=#{func}&fmt=#{fmt}&cache_get=#{cache_get}&cache_expire=#{cache_expire}&async_remote=#{async_remote}",
        {'Content-Type' =>'application/json', 'Authorization'=>"Bearer #{token}"})
    req.body = {"args" => args,"kwargs" => kwargs}.to_json
    res = https.request(req)
    return res.body
end

TOKEN = 'secret-token-1';
URL = 'http://127.0.0.1:8000/api/post'
res = ksrpc_call(URL, 'demo.test', [], {}, 'csv', true, 86400, true, TOKEN)
puts res
res = ksrpc_call(URL, 'demo.div', [1,2], {}, 'csv', true, 86400, true, TOKEN)
puts res
res = ksrpc_call(URL, 'demo.div', [], {'a'=>1, 'b'=> 3}, 'csv', true, 86400, true, TOKEN)
puts res
