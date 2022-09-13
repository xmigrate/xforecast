from packages.datasources.prometheus import *


with open('test/mock/mockdata.yaml') as f:
    mockdata = yaml.load(f, Loader=SafeLoader)

def test_prom():
    query = 'http://192.168.1.9:9090/api/v1/query_range?query=100 - ((node_memory_MemAvailable_bytes{instance="node-exporter:9100"} * 100) / node_memory_MemTotal_bytes{instance="node-exporter:9100"})&start=1662978840&end=1662978900&step=15s'
    r = prometheus(query,test=True)
    assert r == mockdata['prom_results'][1]['values']['value']
def test_getdata():
    prom_query = '100 - ((node_memory_MemAvailable_bytes{instance="node-exporter:9100"} * 100) / node_memory_MemTotal_bytes{instance="node-exporter:9100"})'
    start_time = 1662978840
    end_time = 1662978900
    url = 'http://localhost:9090'
    r=get_data_from_prometheus(prom_query,start_time,end_time,url,test=True)
    assert r == mockdata['getdata_results'][1]['data_points']['data_point']
def test_writedata():
    val = 5000
    tim = 1600000
    write_name = "name"
    prom_url = "localhost:9090"
    write_to_prometheus(val,tim,write_name,prom_url,test=True)