install.packages("httr")

library(httr)
ksrpc_call <- function(base_url, func, args=list(), kwargs=list(), fmt="csv", cache_get = TRUE, cache_expire = 86400, async_remote = TRUE, token=NULL) {
  url<-sprintf("%s?func=%s&fmt=csv&cache_get=%d&cache_expire=%d&async_remote=%d", base_url, func, cache_get,cache_expire, async_remote)
  json_array <- list(args = args, kwargs = kwargs)
  
  body = jsonlite::toJSON(json_array, auto_unbox = T)
  r <- POST(url, body = body, add_headers(Authorization=paste("Bearer", token, sep=" ")), encode = "json", verbose())
  return(content(r))
}

TOKEN="secret-token-1"
URL = "http://127.0.0.1:8000/api/post"

#
ksrpc_call(URL, "demo.div", list(), list(a=2,b=3), token = TOKEN)
txt = ksrpc_call(URL, "demo.test", list(), list(), token = TOKEN)
csv =read.csv(text=txt)
csv