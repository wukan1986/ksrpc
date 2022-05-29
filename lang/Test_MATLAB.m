clear 

url = 'http://127.0.0.1:8000/api/post';
token = 'secret-token-1';

data= ksrpc_call(url,'demo.div',[2,3],struct(),'csv',true,86400,true,token);
disp(data)
data= ksrpc_call(url,'demo.div',[],struct('a',2,'b',3),'csv',true,86400,true,token);
disp(data)
data = ksrpc_call(url,'demo.test',[],struct(),'csv',true,86400,true,token);
disp(data)


function result = ksrpc_call(base_url, func, args, kwargs, fmt, cash_get, cache_expire, async_remote, token)
url = sprintf('%s?func=%s&fmt=%s&cache_get=%d&cache_expire=%d&async_remote=%d',base_url,func,fmt,cash_get,cache_expire,async_remote);
body = jsonencode(struct('args',args,'kwargs',kwargs));
headers = {'Authorization',sprintf('Bearer %s',token)};
options = weboptions('RequestMethod','post','HeaderField',headers,'MediaType','application/json');
result = webwrite(url,body,options);
end



