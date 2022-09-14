from packages.datasources.influx import *

with open('test/mock/mockdata.yaml') as f:
    mockdata = yaml.load(f, Loader=SafeLoader)

def test_influx_getdata():
    data_store = {'url':'localhost','port':8086,'user':'admin','pass':'admin','db_name':'telegraf','measurement':'cpu' }
    start_time = '2022-09-12 08:53:00'
    end_time = '2022-09-12 08:54:00'
    prev_stime = '2022-09-12 08:50:00'
    prev_etime = '2022-09-12 08:51:00'
    prom_query = 'SELECT mean("usage_idle") *-1 +100 FROM "autogen"."cpu" WHERE ("host" = '+"'ip-172-31-31-81') AND time >= '2022-09-12 08:53:00' AND time <= '2022-09-12 08:54:00' GROUP BY time(10s)'"
    r = get_data_from_influxdb(data_store,start_time,end_time,prev_stime,prev_etime,prom_query,test=True)
    assert r == mockdata['influx_results'][1]['values']['value']

def test_influx_writedata():
    val = 500
    tim = 1650000
    write_name = 'mockname'
    data_store = {'url':'localhost','port':8086,'user':'admin','pass':'admin','db_name':'telegraf','measurement':'cpu' }
    r = write_data_to_influxdb(val,tim,write_name,data_store,test=True)
