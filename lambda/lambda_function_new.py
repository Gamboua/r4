import logging
from urllib.parse import urlparse
import hashlib

logger = logging.getLogger()


def lambda_handler(event, context):

    if not has_referer(event['headers']):
        logger.error(
            'Could not find referer on request.'
        )
        return response_error()

    params = extract_request_params(event)

    domain_data = get_domain_on_cache(params['domain'])

    if not domain_data:

        domain_data = get_domain_on_database(params)

        if domain_data:
            save_on_cache(domain_data)
        else:
            logger.error(
                f'Domain not found on database.'
            )
            return response_error()

    response = render_response(domain_data)

    return {
        # 'Cookie': cookie,
        'statusCode': 200,
        'headers': make_headers(),
        'body': response
    }

def has_referer(headers: dict) -> bool:
    return True if 'Referer' in headers else False

def extract_request_params(event: dict) -> dict:
    params = {
        'domain': get_domain(event['headers']['Referer']),
        'id': event['queryStringParameters']['cliente'],
        'tz': event['queryStringParameters']['tz'],
        'width': event['queryStringParameters']['scw'],
        'height': event['queryStringParameters']['sch'],
        'query': get_display_info(event['headers'])
    }

    return params

def get_domain(domain: str) -> str:
    domain = urlparse(domain)
    return domain.netloc

def get_display_info(headers: dict) -> dict:
    if event['headers']['CloudFront-Is-Tablet-Viewer'] == 'true':
        display_info = {
            'mobile_detect': 'tablet',
            'query_src': 'a.tablet=1',
            'column': 'template_domain_tablet',
            'data_select': DATASELECT_QUERY
        }
    elif event['headers']['CloudFront-Is-Mobile-Viewer'] == 'true':
        display_info = {
            'mobile_detect': 'mobile',
            'query_src': 'a.mobile=1',
            'column': 'template_domain_tablet',
            'data_select': DATASELECT_QUERY
        }
    else:
        display_info = {
            mobile_detect: 'desktop',
            query_src: 'a.desktop=1',
            column: 'template_domain',
            data_select: DATASELECT_QUERY
        }

    return display_info

DATASELECT_QUERY = (
    f'a.{mobile_detect}_min_resolution_width as width, '
    f'a.{mobile_detect}_min_resolution_heigth as height, '
    f'REPLACE(REPLACE(a.{column}, "\r\n",""),"\t","") '
    'as template_domain,a.week_hour,a.frequency'
)


def get_domain_on_cache(params: dict) -> dict:
    # CRIA QUERY DE CONSULTA
    query = hashlib.md5(CACHE_QUERY).hexdigest()

    # BUSCA NO CACHE
    result = get_domain_from_cache(query)

    # EXISTE NO CACHE?
        # SIM
            # RETORNA DICIONARIO
        # NAO
            # RETORNA NONE

CACHE_QUERY = (
    f'dataFp:{params["domain"]}'
    f'{params["id"]}
    f'{params["query"]["mobile_detect"]}'
).encode('utf-8')

def get_domain_from_cache(query: str) -> dict:


def get_domain_on_database(params: dict) -> dict:
    pass

def save_on_cache(domain_data: dict):
    pass

def response_error(message: str) -> dict:
    pass

def render_response(domain_data: dict, params: dict) -> str:
    pass

def make_headers() -> dict:
    pass


if __name__ == '__main__':
    lambda_handler(event=EVENT_MODEL, context=[])
