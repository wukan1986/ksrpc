using System;
using System.Net.Http;
using System.Threading.Tasks;
using System.Text.Json;
using System.Collections.Generic;
using System.Text;
using System.Collections;
using System.Net.Http.Headers;

namespace Test_CShape
{
    class Program
    {
        /// <summary>
        /// 网络请求
        /// </summary>
        /// <param name="client">HttpClient实例</param>
        /// <param name="base_url">服务地址</param>
        /// <param name="func">调用函数名</param>
        /// <param name="args">位置参数</param>
        /// <param name="kwargs">关键字参数</param>
        /// <param name="fmt">响应格式 csv 或 json </param>
        /// <param name="cache_get">是否从缓存中获取</param>
        /// <param name="cache_expire">缓存过期时间</param>
        /// <param name="token">Token</param>
        /// <returns>csv或json
        /// 当rsp_fmt=csv时，数据为DataFrame等格式时，返回csv，其它情况返回json
        /// 当rsp_fmt=
        /// </returns>
        async static Task<string> ksrpc_call(
            HttpClient client,
            string base_url,
            string func, IEnumerable args = null, IDictionary kwargs = null,
            string fmt = "csv", // csv或json
            bool cache_get = true, int cache_expire = 86400,
            bool async_remote = true,
            string token = null)
        {
            if (args == null)
                args = new List<object> { };
            if (kwargs == null)
                kwargs = new Dictionary<string, object> { };

            if (token != null)
            {
                client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
            }

            var url = $"{base_url}?func={func}&fmt={fmt}&cache_get={cache_get}&cache_expire={cache_expire}&async_remote={async_remote}";
            var jsonString = JsonSerializer.Serialize(new { args = args, kwargs = kwargs });
            var content = new StringContent(jsonString, Encoding.UTF8, "application/json");

            var response = await client.PostAsync(url, content);
            // 判断服务器响应代码是否为 2XX
            response.EnsureSuccessStatusCode();
            var result = await response.Content.ReadAsStringAsync();
            // 数据有csv与json两种格式，需按需求处理
            return result;
        }

        static async Task Main(string[] args)
        {
            var token = "secret-token-1";
            var client = new HttpClient();
            const string base_url = "http://127.0.0.1:8000/api/post";

            {
                var x = await ksrpc_call(client, base_url, "demo.div", new List<int> { 5, 6 }, null, cache_get: true, cache_expire: 86400, token: token);
                Console.WriteLine(x);
            }

            {
                var x = await ksrpc_call(client, base_url, "demo.div", null, new Dictionary<string, object> { { "a", 2 }, { "b", 3 } }, cache_get: true, cache_expire: 86400, token: token);
                Console.WriteLine(x);
            }
            {
                var x = await ksrpc_call(client, base_url, "demo.test", null, null, fmt: "json", cache_get: true, cache_expire: 86400, token: token);
                Console.WriteLine(x);
            }
        }
    }
}
