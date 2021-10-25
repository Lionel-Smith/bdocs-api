from flask import Flask, request, jsonify
from flask_cors import CORS,cross_origin
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_migrate import Migrate
from config import OracleDB, JWTConfig
from datetime import timedelta
import os
import glob
import importlib
from flask_migrate import Migrate,upgrade
import cx_Oracle
from src.database.setup import DBSetup

app = Flask(__name__, template_folder="templates")
CORS(app)

app.config['JSON_AS_ASCII'] = False
app.config['JWT_SECRET_KEY'] = JWTConfig.secret
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)

jwt = JWTManager(app)

if not DBSetup().schemaExists():
    DBSetup().initializeDB()
    upgrade(directory=os.path.join(os.path.dirname(os.path.dirname(__file__)),"migrations"))
    
app.config['SQLALCHEMY_DATABASE_URI'] = f"oracle://{OracleDB.userName}:{OracleDB.password}@{OracleDB.connectionString}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(app,metadata=metadata)

from src.database.baseModel import BaseModel
from src.models import *

migrate = Migrate(app,db)

#Dynamically add *_controller.py files to flask application
for f in glob.glob(os.path.dirname(__file__) + "/**/*_controller.py",recursive=True):
    spec = importlib.util.spec_from_file_location(os.path.basename(f)[:-3],f)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)