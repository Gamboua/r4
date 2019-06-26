import json
import hashlib

import MySQLdb
import redis

from config import DATABASE
from event_model import EVENT_MODEL

def lambda_handler(event, context):

    mobile_detect = False

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

    css_select = 'REPLACE(REPLACE(c.css, "\r\n",""),"\t","") as css'

    query_params = {
        'domain': event['headers']['Host'],
        'id': event['queryStringParameters']['cliente'],
        'date_time': event['requestContext']['requestTime'],
        'width': event['queryStringParameters']['scw'],
        'height': event['queryStringParameters']['sch']
    }

    # @TODO extrair timezone do horario
    tz = query_params['date_time']

    redis_conn = redis.Redis(
        host='localhost',
        port=6379,
        db=0
    )

    if not query_params['domain'] or not query_params['id']:
        rows = []
    else:
        query = f'dataFp:{query_params['domain']}{query_params['id']}{mobile_detect}'.encode('utf-8')

        rows = redis_conn.get(
            hashlib.md5(query).hexdigest()
        )

        if not rows:
            db = MySQLdb.connect(
                host=DATABASE['host'],
                user=DATABASE['user'],
                passwd=DATABASE['passwd'],
                db=DATABASE['db']
            )
            cur = db.cursor()

            query = f'SELECT {data_select}, {css_select}, c.identifier FROM premiums as a INNER JOIN domains as b ON a.domain_id = b.id INNER JOIN fpconfigs as c ON a.fpconfig_id = c.id WHERE b.domain = "{query_params['domain']}" AND b.status = 1 AND a.status = 1 AND user_id = {query_params['id']} AND {query_src}'

            cur.execute(query)
            rows = cur.fetchall()

            width, height, template_domain, week_hour, frequency, css, identifier = rows[0]

            redis_conn.set(
                hashlib.md5(
                    f'dataFp:{query_params['domain']}{query_params['id']}{mobile_detect}'.encode('utf-8')
                ).hexdigest(),
                json.dumps({
                    'template_domain': template_domain,
                    'week_hour': week_hour,
                    'frequency': frequency,
                    'css': css,
                    'identifier': identifier
                })
            )

    if not rows:
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/javascript;charset=UTF-8'},
            'body': json.dumps('Hello from Lambda!')
        }

    templates = {}

    for key, row in enumerate(rows):
        result = {
            'width': row[0],
            'height': row[1],
            'template_domain': row[2],
            'week_hour': row[3],
            'frequency': row[4],
            'css': row[5],
            'identifier': row[6]
        }

        width = False if query_params['width'] < result['width'] else False
        height = False if query_params['height'] < result['height'] else False

        if height and width:
            # TODO precisa ter um exemplo com a chave template_domain_mobile
            if mobile_detect == 'mobile':
                templates[key]['html'] = json.dumps()

            templates[key]['css'] = json.dumps(result['css'])
            templates[key]['identifier'] = json.dumps(result['identifier'])
            templates[key]['first_view'] = False
            frequencia = []
            templates[key]['show'] = True

            if not frequency:
                frequencia[f'__{result['identifier']}']['_qt'] = 0
                frequencia[f'__{result['identifier']}']['tz'] = tz
                # @TODO retornar cookie
                # r4_frequency : json.dumps(frequencia), expires 1 mes
            else:
                frequencia_config = json.dumps(result['frequency'])

                if not frequencia[f'__{result['identifier']}'] || not frequencia_config['minutos']:
                    if not frequencia_config['minutos']:
                        templates[key]['show'] = True
                    else:
                        templates[key]['first_view'] = True
                        frequencia[f'__{query_params['identifier']}']['_qt'] = 0
                        frequencia[f'__{query_params['identifier']}']['tz'] = tz
                        # @TODO retornar cookie
                        # r4_frequency : json.dumps(frequencia), expires 1 mes
                else:
                    temapltes[key]['first_view'] = True
                    old_tz = frequencia[f'__{query_params['identifier']}']['tz']

                    if not (old_tz + frequencia_config['minutos'] * 60) * 1000 > tz:
                        frequencia[f'__{query_params['identifier']}']['_qt'] = 0
                        frequencia[f'__{query_params['identifier']}']['tz'] = tz
                        # @TODO retornar cookie
                        # r4_frequency : json.dumps(frequencia), expires 1 ano
                    else:
                        if not frequencia_config['quantidade']:
                            templates[key]['show'] = True
                        elif frequencia[f'__{row['identifier']}']['_qt'] >= frequencia_config['quantidade']:
                            templates[key]['show'] = False
        else:
            del rows[key]

    user_agent = event['headers']['User-Agent']

    return {
        # 'Cookie': cookie,
        'statusCode': 200,
        'headers': {'Content-Type': 'application/javascript;charset=UTF-8'},
        'body': json.dumps('Hello from Lambda!')
    }


if __name__ == '__main__':
    lambda_handler(event=EVENT_MODEL, context=[])
