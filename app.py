import os
import sys
from flask import jsonify, request,json
from config import Flask
from werkzeug.exceptions import HTTPException
from datetime import date

ROOT_PATH = os.path.dirname(os.path.realpath(__file__))
os.environ.update({'ROOT_PATH': ROOT_PATH})
sys.path.append(os.path.join(ROOT_PATH, 'src'))

from src import app

@app.errorhandler(HTTPException)
def handle_exception(e):
    response = e.get_response()
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"
    return response

@app.route('/')
def index():
    return jsonify("Hello World"), 200

if __name__ == '__main__':
    app.run(host=Flask.host, port=Flask.port,debug=True)