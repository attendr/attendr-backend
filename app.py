from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_restful import Api
import os


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_CHANGES'] = False

db = SQLAlchemy(app)
admin = Admin(app)
api = Api(app)


from models import *
import endpoints

db.create_all()

api.add_resource(endpoints.Login, '/login')

