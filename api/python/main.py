# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import Flask, abort, request
from flask_restplus import Api
import helpers.flask
import helpers.metadata
import helpers.iap
import helpers.json

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.json_encoder = helpers.json.CustomJSONEncoder

from versions.alpha import bp as alpha
app.register_blueprint(alpha)

@app.before_request
def validate_iap_authn():
    if not app.debug:
        header = request.headers['x-goog-iap-jwt-assertion']
        project_number = helpers.metadata.get('project/numeric-project-id')
        project_id = helpers.metadata.get('project/project-id')
        (user_id, user_email, error_str) = helpers.iap.validate_iap_jwt_from_app_engine(header, project_number, project_id)
        if error_str:
            app.logger.error(error_str)
        if not user_id:
            abort(401)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

