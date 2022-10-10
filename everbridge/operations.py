""" Copyright start
  Copyright (C) 2008 - 2022 Fortinet Inc.
  All rights reserved.
  FORTINET CONFIDENTIAL & FORTINET PROPRIETARY SOURCE CODE
  Copyright end """

import requests, datetime, time, base64, json
from connectors.core.connector import ConnectorError, get_logger
from .constant import *

logger = get_logger('everbridge')


class Everbridge(object):
    def __init__(self, config, *args, **kwargs):
        self.username = config.get('username')
        self.password = config.get('password')
        url = config.get('server_url').strip('/')
        if not url.startswith('https://') and not url.startswith('http://'):
            self.url = 'https://{0}/rest/'.format(url)
        else:
            self.url = url + '/rest/'
        self.verify_ssl = config.get('verify_ssl')
        self.token = generate_token(self.username, self.password)

    def make_rest_call(self, url, method, data=None, params=None, json=None):
        try:
            url = self.url + url
            headers = {
                'Authorization': 'Basic {0}'.format(self.token),
                'Content-Type': 'application/json'
            }
            logger.debug("Endpoint {0}".format(url))
            response = requests.request(method, url, data=data, params=params, json=json, headers=headers,
                                        verify=self.verify_ssl)
            logger.debug("response_content {0}:{1}".format(response.status_code, response.content))
            if response.ok or response.status_code == 204:
                logger.info('Successfully got response for url {0}'.format(url))
                if 'json' in str(response.headers):
                    return response.json()
                else:
                    return response.text
            elif response.status_code == 404:
                return response.json()
            else:
                logger.error("{0}".format(errors.get(response.status_code, '')))
                raise ConnectorError("{0}".format(errors.get(response.status_code, response.text)))
        except requests.exceptions.SSLError:
            raise ConnectorError('SSL certificate validation failed')
        except requests.exceptions.ConnectTimeout:
            raise ConnectorError('The request timed out while trying to connect to the server')
        except requests.exceptions.ReadTimeout:
            raise ConnectorError(
                'The server did not send any data in the allotted amount of time')
        except requests.exceptions.ConnectionError:
            raise ConnectorError('Invalid endpoint or credentials')
        except Exception as err:
            raise ConnectorError(str(err))


def generate_token(username, password):
    user_pass = "{0}:{1}".format(username, password)
    b64_val = base64.b64encode(bytes(user_pass, 'utf-8')).decode('utf-8')
    return b64_val


def check_payload(payload):
    updated_payload = {}
    for key, value in payload.items():
        if isinstance(value, dict):
            nested = check_payload(value)
            if len(nested.keys()) > 0:
                updated_payload[key] = nested
        elif value:
            updated_payload[key] = value
    return updated_payload


def convert_datetime_to_epoch(date_time):
    d1 = time.strptime(date_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    epoch = datetime.datetime.fromtimestamp(time.mktime(d1)).strftime('%s')
    return epoch


def get_organizations_list(config, params):
    eb = Everbridge(config)
    endpoint = '/organizations'
    response = eb.make_rest_call(endpoint, 'GET')
    return response


def get_incident_list(config, params):
    eb = Everbridge(config)
    endpoint = '/incidents/{0}'.format(params.get('organizationId'))
    date_type = params.get('dateType')
    start_time = params.get('startTime')
    end_time = params.get('endTime')
    if 'T' in start_time:
        params.update({'startTime': convert_datetime_to_epoch(start_time)})
    if 'T' in end_time:
        params.update({'endTime': convert_datetime_to_epoch(start_time)})
    if date_type:
        params.update({'dateType': Incident_date_type.get(date_type)})
    payload = check_payload(params)
    response = eb.make_rest_call(endpoint, 'GET', params=payload)
    return response


def get_incident_details(config, params):
    eb = Everbridge(config)
    endpoint = '/incidents/{0}/{1}'.format(params.get('organizationId'), params.get('incidentId'))
    response = eb.make_rest_call(endpoint, 'GET')
    return response


def update_incident(config, params):
    eb = Everbridge(config)
    endpoint = '/incidents/{0}/{1}'.format(params.get('organizationId'), params.get('incidentId'))
    payload = {
        'incident': {
            'name': params.get('name'),
            'incidentStatus': params.get('incidentStatus'),
            'incidentType': params.get('incidentType'),
            'incidentMode': params.get('incidentMode'),
            'closeBy': params.get('closeBy')
        }
    }
    additional_fields = params.get('additional_fields')
    if additional_fields:
        payload['incident'].update(additional_fields)
    payload = check_payload(payload)
    response = eb.make_rest_call(endpoint, 'PUT', data=json.dumps(payload))
    return response


def get_assets_list(config, params):
    eb = Everbridge(config)
    endpoint = '/assets/{0}'.format(params.get('organizationId'))
    payload = check_payload(params)
    response = eb.make_rest_call(endpoint, 'GET', params=payload)
    return response


def get_asset_details(config, params):
    eb = Everbridge(config)
    endpoint = '/assets/{0}/{1}'.format(params.get('organizationId'), params.get('id'))
    response = eb.make_rest_call(endpoint, 'GET')
    return response


def update_asset(config, params):
    eb = Everbridge(config)
    endpoint = '/assets/{0}/{1}'.format(params.get('organizationId'), params.get('id'))
    payload = {
        'asset': {
            'name': params.get('name'),
            'address': {
                'roomNo': params.get('roomNo'),
                'floorNo': params.get('floorNo'),
                'street': params.get('street'),
                'city': params.get('city'),
                'state': params.get('state'),
                'country': params.get('country'),
                'countryFullName': params.get('countryFullName'),
                'postalCode': params.get('postalCode')
            }
        },
        'autoGeoCoding': params.get('autoGeoCoding')
    }
    payload = check_payload(payload)
    response = eb.make_rest_call(endpoint, 'PUT', data=json.dumps(payload))
    return response


def _check_health(config):
    try:
        response = get_organizations_list(config, params={})
        if response:
            return True
    except Exception as err:
        raise ConnectorError("{0}".format(str(err)))


operations = {
    'get_organizations_list': get_organizations_list,
    'get_incident_list': get_incident_list,
    'get_incident_details': get_incident_details,
    'update_incident': update_incident,
    'get_assets_list': get_assets_list,
    'get_asset_details': get_asset_details,
    'update_asset': update_asset
}
