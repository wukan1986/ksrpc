# HTTP、WebSocket接口文档
## 3个基本参数
1. func: 函数全名。str。含模块名的全名，例如：pandas.read_csv、builtins.print
2. args: 位置参数。list或tuple
3. kwargs: 关键字参数。dict

细节
1. 由于args的参数顺序无法在URL地址中直接进行表达，只能在POST请求的BODY区传输
2. args和kwargs中的参数是复杂类型，只能在BODY区使用JSON格式，而不能使用FORM方式
3. func放在URL的QUERY部分，方便网络日志和监控工具对用户请求进行跟踪

## 4个控制参数
1. fmt: 响应格式约定。
    1. json: 为了能完整的还原DataFrame，还为了不占用太多流量，使用的tight模式。
    2. csv: 可能部分语言处理json比较麻烦，所以遇到DataFrame时将输出csv格式。其他情况还是输出json
    3. pkl.gz: 仅用于Python下的一种二进制格式。无法跨语言
2. cache_get: 是否默认从缓存中获取数据
3. cache_expire: 指定当前查询数据是否放入缓存，生命周期是多长。单位秒
    1. 交易日历、历史行情等没有必要每次下载，超时可以设成1个月或以上
4. token: 授权认证。可选
    1. HTTP，通过Header，进行Bearer认证
    2. WebSocket，如果所用语言的库支持添加Header，进行Bearer认证，否则使用QUERY区
    
## 总结
1. HTTP
    1. 使用POST请求，地址为http://127.0.0.1:8000/api/post
    2. args与kwargs走BODY区，以JSON格式提交
    3. token使用Header方式提供
    4. 其它参数都走QUERY区
2. WebSocket
    1. 地址为ws://127.0.0.1:8000/ws/json
    2. token优先使用Header，然后是QUERY区
    3. 除token外的其它参数都打包成json统一发送，包括func、args、fmt、cache_get等

## 文档+测试
http://127.0.0.1:8000/docs
1. 跨语言调用仅看POST即可
2. GET功能弱，仅于用在浏览器中演示，跨语言调用没必要实现
    
## 示例
```shell script
curl -X 'POST' \
  'http://localhost:8000/api/post?func=demo.div&fmt=csv&cache_get=true&cache_expire=86400' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "args": [1,2],
  "kwargs": {}
}'

```

```json
{
  "status": 200,
  "datetime": "2022-05-25T14:04:49.605084",
  "func": "demo.div",
  "args": [
    1,
    2
  ],
  "kwargs": {},
  "type": "float",
  "data": 0.5
}
```

```html
http://localhost:8000/api/get?func=demo.test&fmt=csv&cache_get=true&cache_expire=86400
```

```text
,A,B,C,D
2000-01-03,1.4029520495007188,-0.030461041710199775,-0.17509076668316406,-0.5319406092927923
2000-01-04,0.6683877175160576,0.4563825933616125,1.558515141157523,0.9829046296226965
2000-01-05,-1.21018945447475,-0.4110709733721518,0.5898486695659203,0.11777513118966493
2000-01-06,-0.8661291789701833,0.7405674721951274,-1.0071222579732984,0.09598946290817247
```