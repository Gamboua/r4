import json
import hashlib

import MySQLdb
import redis

from event_model import EVENT_MODEL

def lambda_handler(event, context):

    mobile_detect = False

    if event['headers']['CloudFront-Is-Tablet-Viewer'] == 'true':
        mobile_detect = 'tablet'
        query_src = 'a.tablet=1'
        data_select = 'REPLACE(REPLACE(a.template_domain_tablet, "\r\n",""),"\t","") as template_domain_tablet,a.week_hour,a.frequency'
    elif event['headers']['CloudFront-Is-Mobile-Viewer'] == 'true':
        mobile_detect = 'mobile'
        query_src = 'a.mobile=1'
        data_select = 'REPLACE(REPLACE(a.template_domain_mobile, "\r\n",""),"\t","") as template_domain_mobile,a.week_hour,a.frequency'
    else:
        mobile_detect = 'desktop'
        query_src = 'a.desktop=1'
        data_select = 'REPLACE(REPLACE(a.template_domain, "\r\n",""),"\t","") as template_domain,a.week_hour,a.frequency'

    css_select = 'REPLACE(REPLACE(c.css, "\r\n",""),"\t","") as css'

    domain, id, date_time, width, height = (
        event['headers']['Host'],
        event['queryStringParameters']['cliente'],
        event['requestContext']['requestTime'],
        event['queryStringParameters']['scw'],
        event['queryStringParameters']['sch']
    )

    @TODO extrair timezone do horario
    tz = date_time

    redis_conn = redis.Redis(
        host='localhost',
        port=6379,
        db=0
    )

    if not domain or not id:
        rows = []
    else:
        query = f'dataFp:{domain}{id}{mobile_detect}'.encode('utf-8')

        rows = redis_conn.get(
            hashlib.md5(query).hexdigest()
        )

        breakpoint()

        if not rows:
            cur = db.cursor()

            query = f'SELECT {data_select}, {css_select}, c.identifier FROM premiums as a INNER JOIN domains as b ON a.domain_id = b.id INNER JOIN fpconfigs as c ON a.fpconfig_id = c.id WHERE b.domain = "{domain}" AND b.status = 1 AND a.status = 1 AND user_id = {id} AND {query_src}'

            cur.execute(query)

            rows = cur.fetchall()

            template_domain, week_hour, frequency, css, identifier = rows[0]

            redis_conn.set(
                hashlib.md5(
                    f'dataFp:{domain}{id}{mobile_detect}'.encode('utf-8')
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
        template_domain, week_hour, frequency, css, identifier = rows

        width = True
        height = True

        if height and width:

            #if mobile_detect == 'mobile':
            #    templates['key']['html'] = 

        templates[key]['css'] = json.dumps(css)
        templates[key]['identifier'] = json.dumps(identifier)
        templates[key]['first_view'] = False
        frequencia = []
        templates[key]['show'] = True

        if not frequency:
            frequencia[f'__{identifier}']['_qt'] = 0
            frequencia[f'__{identifier}']['tz'] = tz
            @TODO retornar cookie
            # r4_frequency : json.dumps(frequencia), expires 1 mes
        else: # linha 115
            # frequencia_config = 

    user_agent = event['headers']['User-Agent']

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/javascript;charset=UTF-8'},
        'body': json.dumps('Hello from Lambda!')
    }


if __name__ == '__main__':
    lambda_handler(event=EVENT_MODEL, context=[])
