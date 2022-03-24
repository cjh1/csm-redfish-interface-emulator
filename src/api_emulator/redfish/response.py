import json

def success_response(msg, status, jsonify=False):
    data = {
        'code': status,
        'message': '{}'.format(msg)
    }
    if jsonify:
        data = json.dumps(data, indent=4)
    return data, status

def simple_error_response(msg, status, jsonify=False):
    data = {
        'Status': status,
        'Message': '{}'.format(msg)
    }
    if jsonify:
        data = json.dumps(data, indent=4)
    return data, status

def error_404_response(path, jsonify=False):
    data = {
        'error': {
            '@Message.ExtendedInfo': [
                {
                    '@odata.type': '#Message.v1_0_5.Message',
                    'Message': 'The resource at the URI {} was not found.'.format(path),
                    'MessageArgs': [
                        '{}'.format(path)
                    ],
                    'MessageId': 'Base.1.4.ResourceMissingAtURI',
                    'Resolution': 'Place a valid resource at the URI or correct the URI and resubmit the request.',
                    'Severity': 'Critical'
                }
            ],
            'code': 'Base.1.4.ResourceMissingAtURI',
            'message': 'The resource at the URI {} was not found.'.format(path)
        }
    }
    if jsonify:
        data = json.dumps(data, indent=4)
    return data, 404
    
    
def error_not_allowed_response(path, method, headers, jsonify=False):
    data = {
        'error': {
            '@Message.ExtendedInfo': [
                {
                    '@odata.type': '#Message.v1_0_5.Message',
                    'Message': 'The method {} is not allowed for the URI {}'.format(method, path),
                    'MessageArgs': [
                        '{}'.format(method),
                        '{}'.format(path)
                    ],
                    'MessageId': 'HttpStatus.1.0.MethodNotAllowed',
                    'Resolution': 'Use a method listed in the Allow header',
                    'Severity': 'Critical'
                }
            ],
            'code': 'HttpStatus.1.0.MethodNotAllowed',
            'message': 'The method {} is not allowed for the URI {}'.format(method, path)
        }
    }
    if jsonify:
        data = json.dumps(data, indent=4)
    return data, 405, headers