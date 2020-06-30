#!flask/bin/python
from flask import Flask
import psycopg2

app = Flask(__name__)
con = psycopg2.connect(dbname   = 'd8gq28isrvoolq',
                       host     = 'ec2-34-233-226-84.compute-1.amazonaws.com',
                       port     = 5432,
                       user     = 'tpjvkqwarvbnqp',
                       password = 'f5c0c0f2366b42b86ebec2ed34ecc8cf3ba336c950c8e60897ff4f68ea681cf5')

def exec_script(sql):
    con.set_session(autocommit=True)
    cur = con.cursor()
    cur.execute(sql)

@app.route('/')
def index():
    return 'Hello world'

@app.route('/slack/slash/<name>/v1', methods=['POST'])
def test(name):
    exec_script("insert into sprt.bot_income (info) values ('test');")
    return 'Hello {0}'.format(name)

if __name__ == '__main__':
    app.run(debug=True)

