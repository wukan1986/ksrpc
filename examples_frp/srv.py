# pip install dnspython
import dns.rdatatype
import dns.rdtypes.IN.SRV
import dns.resolver


def query_srv_record(service, protocol, domain):
    """
    查询SRV记录
    格式: _service._protocol.domain
    例如: _sip._tcp.example.com
    """
    srv_domain = f"_{service}._{protocol}.{domain}"

    try:
        resolver = dns.resolver.Resolver()

        # 设置DNS服务器（可选）
        # resolver.nameservers = ['8.8.8.8']

        # 查询SRV记录
        answer = resolver.resolve(srv_domain, 'SRV')

        results = []
        for rdata in answer:
            # SRV记录包含：优先级、权重、端口、目标主机
            srv_info = {
                'priority': rdata.priority,
                'weight': rdata.weight,
                'port': rdata.port,
                'target': rdata.target.to_text().rstrip('.')
            }
            results.append(srv_info)

        # 按优先级和权重排序
        results.sort(key=lambda x: (x['priority'], -x['weight']))
        return results

    except dns.resolver.NoAnswer:
        print(f"没有找到SRV记录: {srv_domain}")
        return []
    except dns.resolver.NXDOMAIN:
        print(f"域名不存在: {srv_domain}")
        return []
    except Exception as e:
        print(f"查询失败: {e}")
        return []


# 使用示例
srv_records = query_srv_record('frp', 'tcp', 'frp.example.com')
for record in srv_records:
    print(f"目标: {record['target']}:{record['port']} (优先级: {record['priority']}, 权重: {record['weight']})")

toml = """
serverAddr = "{target}"
serverPort = {port}
auth.token = "frp.example.com"

[[proxies]]
name = "ksrpc_tcp"
type = "tcp"
localIP = "127.0.0.1"
localPort = 8080
remotePort = 7001

"""

toml = toml.format(target=srv_records[0]['target'], port=srv_records[0]['port'])
print(toml)

with open("frpc.toml", 'w', encoding='utf-8') as f:
    f.write(toml)
