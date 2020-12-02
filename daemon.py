#! /usr/bin/python3

'''
 Copyright 2020-present SK Telecom
 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at
     http://www.apache.org/licenses/LICENSE-2.0
 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
'''

from flask import Flask, request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

from router import *

app = Flask(__name__)
auth = HTTPBasicAuth()

users = {
    "onos": generate_password_hash("rocks")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username

@app.route('/api/v1/router/<name>', methods = ['POST', 'DELETE'])
@auth.login_required
def create(name):
    if request.method == 'POST':
        create_bridge(name)
        run_router(name)
        config_pipework(name)
        config_nat(name)
        return 'create %s' % name
    elif request.method == 'DELETE':
        delete_bridge(name)
        stop_router(name)
        return 'delete %s' % name

@app.route('/api/v1/', methods = ['GET'])
def default():
    return "It works!"

if __name__ == '__main__':
    app.run(debug=True)
