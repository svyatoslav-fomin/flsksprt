#!flask/bin/python
from flask import Flask, request, make_response
import requests
import psycopg2
import os
import datetime
import json

app = Flask(__name__)
con = psycopg2.connect(dbname   = os.environ['BD_NAME'],
                       host     = os.environ['BD_HOST'],
                       port     = os.environ['BD_PORT'],
                       user     = os.environ['BD_USER'],
                       password = os.environ['BD_USER_PASSWORD'])

def get_dialogs_list():
    res = {}
    cur = con.cursor()
    cur.execute('select * from sprt.bot_dialogs')
    rows = cur.fetchall()
    for row in rows:
        res[row[0]] = row[1].replace('\r\n', '')
    return res
dialogs = get_dialogs_list()

slack_api_dialog_url = 'https://slack.com/api/dialog.open'

sbot_name = os.environ['SBOT_NAME']
sbot_token = os.environ['SBOT_TOKEN']
sbot_token2 = os.environ['SBOT_TOKEN2']
sbot_channel = os.environ['SBOT_CHANNEL']
sbot_token3 = os.environ['SBOT_TOKEN3']
sbot_qq_token = os.environ['SBOT_QQ_TOKEN']

os.environ['last_inserted_income_date'] = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
os.environ['last_selected_income_date'] = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def post_message_to_slack(text, blocks = None):
    return requests.post('https://slack.com/api/chat.postMessage', {
        'token': sbot_token,
        'channel': sbot_channel,
        'text': text,
        'username': sbot_name,
        'blocks': json.dumps(blocks) if blocks else None
    }).json()

def exec_script(sql):
    cur = con.cursor()
    cur.execute(sql)

def get_queue_json_by_sql(sql_text):
    res = []
    cur = con.cursor()
    cur.execute(sql_text)
    colnames = cur.description
    rows = cur.fetchall()
    irow = 0
    for row in rows:
        json_txt = '"{0}":"{1}"'.format('row_num', irow)
        for i in range(0, len(colnames)):
            json_txt = '{0}, "{1}":"{2}"'.format(json_txt, colnames[i][0], row[i])
        json_txt = '{' + json_txt + '}'
        res.append(json.loads(json_txt))
        irow = irow + 1
    return res

@app.route('/')
def index():
    return 'Hello world'

@app.route('/get_queue')
def get_queue():
    d_ins = datetime.datetime.strptime(os.environ['last_inserted_income_date'], "%Y%m%d%H%M%S")
    d_sel = datetime.datetime.strptime(os.environ['last_selected_income_date'], "%Y%m%d%H%M%S")
    if d_ins > d_sel:
      os.environ['last_selected_income_date'] = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
      qq = get_queue_json_by_sql("""
                with del as (delete from sprt.bot_income
                              where id = (select min(t.id)
                                            from sprt.bot_income t
                                           where t.dt = (select min(x.dt)
                                                           from sprt.bot_income x))
                             returning token_txt, channel, user_id, info, trigger_id)
                select token_txt, channel, user_id, info, trigger_id
                  from del""")
      if len(qq)>0:
        return qq[0]
    return ''

def insert_bot_income(token, channel, user_id, text, trigger_id):
    exec_script("""
      insert into sprt.bot_income
        (token_txt, channel, user_id, info, trigger_id)
      values
        ('{0}', '{1}', '{2}', '{3}', '{4}');""".format(
            token.replace("'", "''"),
            channel.replace("'", "''"),
            user_id.replace("'", "''"),
            text.replace("'", "''"),
            trigger_id.replace("'", "''"))) 
    os.environ['last_inserted_income_date'] = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    #post_message_to_slack("check")
    #post_message_to_slack(""""token":"{0}", "channel":"{1}", "user_id":"{2}", "text":"{3}", "trigger_id":"{4}"""".format(
    #                        token.replace("'", "''"),
    #                        channel.replace("'", "''"),
    #                        user_id.replace("'", "''"),
    #                        text.replace("'", "''"),
    #                        trigger_id.replace("'", "''")))
  
@app.route('/slack/slash/<name>/v1', methods=['POST'])
def slash(name):
    token = request.form.get('token')
    channel = request.form.get('channel_name')
    user_id = request.form.get('user_id')
    text =  request.form.get('text')
    trigger_id = request.values['trigger_id']
    
    insert_bot_income(token, channel, user_id, text, trigger_id)

    api_data = {
        "token": sbot_token2,
        "trigger_id": trigger_id,
        "dialog": json.dumps(json.loads(dialogs[name])) #json.dumps(dialog_test)
    }
    res = requests.post(slack_api_dialog_url, data=api_data)
    
    return 'Загрузка...'

@app.route('/slack/interactive/v1', methods=['POST'])
def interactive():
    response_text = 'test'
    #interactive_action = json.loads(request.values['payload'])

    #try:
    #    if interactive_action['type'] == 'interactive_message':
    #        pass
    #    elif interactive_action['type'] == 'dialog_submission':
    #        pass
    #except Exception as ex:
    #    response_text = 'Error: {0}'.format(ex)

    return response_text
  
@app.route('/slack/interactive/qq', methods=['POST'])
def interactive_qq():
    response_text = 'test'
    slack_req = json.loads(request.values['payload'])

    try:
        #if slack_req['type'] == 'shortcut':
        #    pass
        #elif slack_req['type'] == 'dialog_submission':
            data_info = {
                                'token'     : sbot_qq_token,
                                'channel'   : '#home',
                                'text'      : slack_req["user"]["id"] + ', ' + slack_req['type'] + slack_req['message_ts']
                             }
            r = requests.post('https://slack.com/api/chat.postMessage', data_info).json()
    except Exception as ex:
        response_text = 'Error: {0}'.format(ex)

    return make_response(response_text, 200)
  
@app.route('/slack/slash/bcalc', methods=['POST'])
def bcalc():
    token = request.form.get('token')
    channel = request.form.get('channel_name')
    user_id = request.form.get('user_id')
    text =  request.form.get('text')
    trigger_id = request.values['trigger_id']
    
    insert_bot_income(token, channel, user_id, text, trigger_id)
    
    dialog_bcalc = {
        "callback_id": "bcalc_id",
        "title": "Калькулятор досок",
        "submit_label": "Ok",
        "elements": [
          {
            "type": "text",
            "label": "Длина (см)",
            "name": "xlength",
            "value": "600"
          },
          {
            "type": "text",
            "label": "Ширина (см)",
            "name": "xwidth",
            "value": "20"
          },
          {
            "type": "text",
            "label": "Высота (см)",
            "name": "xheight",
            "value": "4"
          },
          {
            "type": "text",
            "label": "Кол-во досок",
            "name": "xcount",
            "value": "40"
          },
          {
            "type": "text",
            "label": "Цена",
            "name": "xprice",
            "value": "9500"
          }
        ]
      }

    api_data = {
        "token": sbot_qq_token,
        "trigger_id": trigger_id,
        "dialog": json.dumps(dialog_bcalc) #json.dumps(json.loads(dialog_bcalc))
    }
    res = requests.post(slack_api_dialog_url, data=api_data)
    
    return trigger_id 

if __name__ == '__main__':
    con.set_session(autocommit=True)
    exec_script('delete from sprt.bot_income;')
    app.run()

