#!flask/bin/python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello world'

@app.route('/slack/slash/<name>/v1')
def test(name):
    return 'Hello {0}'.format(name)

if __name__ == '__main__':
    app.run(debug=True)
