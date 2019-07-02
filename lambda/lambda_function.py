import json
import hashlib
from urllib.parse import urlparse

import redis
import mysql.connector

from config import DATABASE, CACHE
from event_model import EVENT_MODEL
from javascript_template import PHP_FUNCTION_LOOP, RESPONSE_TEMPLATE

def lambda_handler(event, context):

    print(event)

    mobile_detect = False

    print('DETECTANDO DISPOSITIVO...')

    if event['headers']['CloudFront-Is-Tablet-Viewer'] == 'true':
        mobile_detect = 'tablet'
        query_src = 'a.tablet=1'
        data_select = 'a.tablet_min_resolution_width as width, a.tablet_min_resolution_heigth as height, REPLACE(REPLACE(a.template_domain_tablet, "\r\n",""),"\t","") as template_domain_tablet,a.week_hour,a.frequency'
    elif event['headers']['CloudFront-Is-Mobile-Viewer'] == 'true':
        mobile_detect = 'mobile'
        query_src = 'a.mobile=1'
        data_select = 'a.mobile_min_resolution_width as width, a.mobile_min_resolution_heigth as height, REPLACE(REPLACE(a.template_domain_mobile, "\r\n",""),"\t","") as template_domain_mobile,a.week_hour,a.frequency'
    else:
        mobile_detect = 'desktop'
        query_src = 'a.desktop=1'
        data_select = 'a.desktop_min_resolution_width as width,a.desktop_min_resolution_heigth as height, REPLACE(REPLACE(a.template_domain, "\r\n",""),"\t","") as template_domain,a.week_hour,a.frequency'

    print(f'DISPOSITIVO DETECTADO: {mobile_detect}')

    css_select = 'REPLACE(REPLACE(c.css, "\r\n",""),"\t","") as css'

    query_params = {
        'domain': event['headers']['Referer'] or None,
        'id': event['queryStringParameters']['cliente'],
        'tz': event['queryStringParameters']['tz'],
        'width': event['queryStringParameters']['scw'],
        'height': event['queryStringParameters']['sch'],

    }

    print(f'DADOS DO CLIENTE: {query_params["domain"]} | {query_params["id"]}')

    try:
        redis_conn = redis.Redis(
            host=CACHE['host'],
            port=6379,
            db=0,
            socket_connect_timeout=1
        )
    except Exception as e:
        print(f'Falha na conexao com Redis: {e}')

    if not query_params['domain'] or not query_params['id']:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/javascript;charset=UTF-8'},
            'body': 'SAI PRA LA CAPIROTO'
        }
    else:
        domain = urlparse(event['headers']['Referer'])
        query_params['domain'] = domain.netloc

        query = f'dataFp:{query_params["domain"]}{query_params["id"]}{mobile_detect}'.encode('utf-8')

        print('RECUPERANDO DADOS DE CACHE...')

        rows = redis_conn.get(
            hashlib.md5(query).hexdigest()
        )

        if not rows:
            print('DADOS DE CACHE NÃO ENCONTRADOS')
            print('INICIANDO BUSCA NO BANCO...')
            db = mysql.connector.connect(
                host=DATABASE['host'],
                user=DATABASE['user'],
                passwd=DATABASE['passwd'],
                db=DATABASE['db'],
                connection_timeout=1
            )
            cur = db.cursor(dictionary=True, buffered=True)

            query = f'SELECT {data_select}, {css_select}, c.identifier FROM premiums as a INNER JOIN domains as b ON a.domain_id = b.id INNER JOIN fpconfigs as c ON a.fpconfig_id = c.id WHERE b.domain = "{query_params["domain"]}" AND b.status = 1 AND a.status = 1 AND user_id = {query_params["id"]} AND {query_src}'
            print(query)
            cur.execute(query)
            rows = cur.fetchall()

            if rows:
                print('DADOS ENCONTRADOS NO BANCO.')
                print('SALVANDO DADOS EM CACHE...')
                redis_conn.set(
                    hashlib.md5(
                        f'dataFp:{query_params["domain"]}{query_params["id"]}{mobile_detect}'.encode('utf-8')
                    ).hexdigest(),
                    json.dumps(rows)
                )
                print('DADOS SALVOS EM CACHE')
            else:
                print('DADOS NAO ENCONTRADOS NO BANCO')
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/javascript;charset=UTF-8'},
                    'body': 'SAI PRA LA CAPIROTO'
                }
        else:
            print('DADOS ENCONTRADOS NO CACHE')
            rows = json.loads(rows)

    templates = {}
    loop_list = []

    print('INICIANDO CRIAÇÃO DE TEMPLATE')

    for key, row in enumerate(rows):

        width = True
        height = True

        print('CHECAGEM  DE DIMENSOES...')
        if row['width']:
            width = False if query_params['width'] < row['width'] else True

        if row['height']:
            height = False if query_params['height'] < row['height'] else True

        print('CHECAGEM FEITA.')

        if height and width:
            if mobile_detect == 'mobile':
                html = json.dumps(row['template_domain_mobile'])
            elif mobile_detect == 'tablet':
                html = json.dumps(row['template_domain_tablet'])
            else:
                html = json.dumps(row['template_domain'])

            print('CRIANDO DICIONARIOS DO TEMPLATE')

            templates[key] = {
                'css': json.dumps(row['css']),
                'identifier': json.dumps(row['identifier']),
                'first_view': False,
                'show': True,
                'html': html
            }

            print('DICIONARIO CRIADO: ')
            print(templates)
            print('---------------')

            frequencia = []

            #if 'frequency' not in row:
            #    frequencia[f'__{row['identifier']}']['_qt'] = 0
            #    frequencia[f'__{row['identifier']}']['tz'] = tz
            #     # @TODO retornar cookie
            #     # r4_frequency : json.dumps(frequencia), expires 1 mes
            #else:
            #    frequencia_config = json.dumps(row['frequency'])
#
            #    if not frequencia[f'__{row['identifier']}'] || not frequencia_config['minutos']:
            #        if not frequencia_config['minutos']:
            #            templates[key]['show'] = True
            #         else:
            #            templates[key]['first_view'] = True
            #            frequencia[f'__{query_params['identifier']}']['_qt'] = 0
            #            frequencia[f'__{query_params['identifier']}']['tz'] = tz
            #            # @TODO retornar cookie
            #            # r4_frequency : json.dumps(frequencia), expires 1 mes
            #     else:
            #        temapltes[key]['first_view'] = True
            #        old_tz = frequencia[f'__{query_params['identifier']}']['tz']
#
            #        if not (old_tz + frequencia_config['minutos'] * 60) * 1000 > tz:
            #            frequencia[f'__{query_params['identifier']}']['_qt'] = 0
            #            frequencia[f'__{query_params['identifier']}']['tz'] = tz
            #            # @TODO retornar cookie
            #            # r4_frequency : json.dumps(frequencia), expires 1 ano
            #        else:
            #            if not frequencia_config['quantidade']:
            #                templates[key]['show'] = True
            #            elif frequencia[f'__{row['identifier']}']['_qt'] >= frequencia_config['quantidade']:
            #                templates[key]['show'] = False
        else:
            del rows[key]

        if 'show' in templates[key]:
            data = {
                'templates_key_css': templates[key]['css'],
                'templates_key_identifier': templates[key]['identifier'],
                'templates_key_html': templates[key]['html']
            }

            print('INTERPOLANDO HTML ')

            loop_list.append(
                PHP_FUNCTION_LOOP.format(**data)
            )
            
            print('INTERPOLAÇÃO CONCLUIDA')

    data = {
        'loop': ''.join(loop_list),
        'row_weekhour': row['week_hour']
    }

    print('ADICIONANDO HTML NO TEMPLATE')
    response_template = RESPONSE_TEMPLATE.format(**data)

    print('DONE. RETORNANDO TEMPLATE.')

    return {
        # 'Cookie': cookie,
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/javascript;charset=UTF-8',
        },
        'body': response_template
    }


if __name__ == '__main__':
    lambda_handler(event=EVENT_MODEL, context=[])
