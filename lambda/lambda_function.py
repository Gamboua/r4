import json

def lambda_handler(event, context):

    detect = Mobile_Detect()
    mobile_detect = False

    if detect.is_tablet():
        mobile_detect = 'tablet'
        query_src = 'a.tablet=1'
        data_select = 'REPLACE(REPLACE(a.template_domain_tablet, "\r\n",""),"\t","") as template_domain_tablet,a.week_hour,a.frequency'
    elif detect.is_mobile():
        mobile_detect = 'mobile'
        query_src = 'a.mobile=1'
        data_select = 'REPLACE(REPLACE(a.template_domain_mobile, "\r\n",""),"\t","") as template_domain_mobile,a.week_hour,a.frequency'
    else:
        mobile_detect = 'desktop'
        query_src = 'a.desktop=1'
        data_select = 'REPLACE(REPLACE(a.template_domain, "\r\n",""),"\t","") as template_domain,a.week_hour,a.frequency'

    cssSelect = 'REPLACE(REPLACE(c.css, "\r\n",""),"\t","") as css'
    url = 

    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
        
    }
