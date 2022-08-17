

def prometheus(query):
    """Gets data from prometheus using the http api.

    Parameters
    ----------
    query: proemtheus query for the metric

    Returns
    -------
    values: Result from prometheus
    """

    result = json.loads(requests.get(query).text)
    value = result['data']['result']
    status=result['status']
    # if value:
    #     logger("Fetching data from prometheus - Succes","warning")
    # else:
    #     logger("Fetching data from prometheus - Failed","warning")
    return value



with open('../mock/prom.yaml') as f:
    data = yaml.load(f, Loader=SafeLoader)


def test_answer():
    assert prometheus("http://localhost:9090/api/v1/query_range?query=sum+by(instance)+(irate(node_cpu_seconds_total{instance=%22node-exporter:9100%22}[24h]))&start=1659948386&end=1659948738&step=30s") == data["result"]