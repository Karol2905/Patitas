import json


def armar_evento(metodo, path, body=None, query=None, path_params=None):
    if isinstance(body, (dict, list)):
        body = json.dumps(body)
    return {
        "httpMethod": metodo,
        "path": path,
        "body": body,
        "queryStringParameters": query,
        "pathParameters": path_params,
    }
