
def tablize(jsondata):
    data = []
    headers = []
    if len(jsondata) > 0:
        headers = list(jsondata[0].keys())
        for item in jsondata:
            data.append(list(item.values()))
    return data, headers

