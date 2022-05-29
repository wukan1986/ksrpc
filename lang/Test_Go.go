package main
import (
    "encoding/json"
    "fmt"
    "io/ioutil"
    "net/http"
    "strings"
)
func ksrpc_call(base_url string, func_ string, args interface{}, kwargs map[string]interface{}, fmt_ string, cache_get bool, cache_expire int, async_remote bool, token string) string {
    url := fmt.Sprintf("%s?func=%s&fmt=%s&cache_get=%t&cache_expire=%d&async_remote=%t", base_url, func_, fmt_, cache_get, cache_expire, async_remote)

    body := map[string]interface{}{"args": args, "kwargs": kwargs}
    bodyStr, err := json.Marshal(body)
    client := &http.Client{}
    req, err := http.NewRequest("POST", url, strings.NewReader(string(bodyStr)))
    req.Header.Set("Authorization", "Bearer "+token)
    
    resp, err := client.Do(req)
    defer resp.Body.Close()
    res, err := ioutil.ReadAll(resp.Body)
    if err != nil {
        fmt.Println(err)
    }
    return string(res)
}

func main() {
    TOKEN:="secret-token-1"
    URL:="http://127.0.0.1:8000/api/post"
    
    {
        args := [...]interface{}{}
        kwargs :=map[string]interface{}{}

        res := ksrpc_call(URL, "demo.test", args, kwargs, "csv", true,86400,true,TOKEN)
        fmt.Println(res)
    }
    {
        args := [...]interface{}{1,2}
        kwargs :=map[string]interface{}{}

        res := ksrpc_call(URL, "demo.div", args, kwargs, "csv", true,86400,true,TOKEN)
        fmt.Println(res)
    }
        {
        args := [...]interface{}{}
        kwargs :=map[string]interface{}{"a":1, "b":3}

        res := ksrpc_call(URL, "demo.div", args, kwargs, "csv", true,86400,true,TOKEN)
        fmt.Println(res)
    }
}