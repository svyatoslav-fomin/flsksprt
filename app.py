#!flask/bin/python
from flask import Flask, request
import psycopg2
import os
import datetime
import json

app = Flask(__name__)
con = psycopg2.connect(dbname   = 'd8gq28isrvoolq',
                       host     = 'ec2-34-233-226-84.compute-1.amazonaws.com',
                       port     = 5432,
                       user     = 'tpjvkqwarvbnqp',
                       password = 'f5c0c0f2366b42b86ebec2ed34ecc8cf3ba336c950c8e60897ff4f68ea681cf5')

os.environ['last_inserted_income_date'] = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
os.environ['last_selected_income_date'] = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def exec_script(sql):
    con.set_session(autocommit=True)
    cur = con.cursor()
    cur.execute(sql)

def get_json_by_sql(sql_text):
    res = []
    cur = con.cursor()
    cur.execute(sql_text)
    colnames = cur.description
    rows = cur.fetchall()
    irow = 0
    for row in rows:
        json_txt = '"{0}":"{1}"'.format('row_num', irow)
        for i in range(0, len(colnames)):
            json_txt = '{0}, "{1}":"{2}",'.format(json_txt, colnames[i], row[i])
        json_txt = '{' + json_txt + '}'
        res.append(json.loads(json_txt))
        irow = irow + 1
    return str(res)

@app.route('/')
def index():
    return 'Hello world'
  
@app.route('/get_queue')
def get_queue():
    d_ins = datetime.datetime.strptime(os.environ['last_inserted_income_date'], "%Y%m%d%H%M%S")
    d_sel = datetime.datetime.strptime(os.environ['last_selected_income_date'], "%Y%m%d%H%M%S")
    #if d_ins > d_sel:
    return get_json_by_sql("""
      select token_txt, channel, user_id, info
        from sprt.bot_income
       order by dt""")
    #return ''

@app.route('/slack/slash/<name>/v1', methods=['POST'])
def test(name):
    os.environ['last_inserted_income_date'] = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    token = request.form.get('token')
    channel = request.form.get('channel_name')
    user_id = request.form.get('user_id')
    text = request.form.get('text')
    exec_script("""
      insert into sprt.bot_income
        (token_txt, channel, user_id, info)
      values
        ('{0}', '{1}', '{2}', '{3}');""".format(token, channel, user_id, text))
    return 'Hello {0}'.format(name)

if __name__ == '__main__':
    app.run()
    exec_script('delete from sprt.bot_income;')

