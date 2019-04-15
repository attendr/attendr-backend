from app import api, db
from models import LoginLogs, Student
from flask_restful import Resource, reqparse


class Login(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('username', type=str, required=True, help='Parmeter username is required')
        self.parser.add_argument('password', type=str, required=True, help='Parameter password is required')
        super()

    def post(self):
        args = self.parser.parse_args(strict=True)
        username, password = args.get('username'), args.get('password')
        student = Student.query.filter_by(username=username).first()
        login_log = LoginLogs(student.id)
        db.session.add(login_log)
        db.session.commit()
        if login_log.token_issued:

            result = {
                'sucess': True,
                'auth_token': login_log.token_issued,
                'user': {
                    'username': username,
                    'no_of_courses': len(student.courses_taken),
                    'average_attendance': 
                }
                'courses': []
            }
            return result, 200
        else:
            result = {
                'success': False,
                'message': 'username/password mismatch'
            }
            return result, 401

class Classes(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('username', type=str, required=True, help='Parmeter username is required')
        self.parser.add_argument('password', type=str, required=True, help='Parameter password is required')
        super()

    def post(self):
        args = self.parser.parse_args(strict=True)
        username, password = args.get('username'), args.get('password')
        student = Student.query.filter_by(username=username).first()
        login_log = LoginLogs(student.id)
        db.session.add(login_log)
        db.session.commit()
        if login_log.token_issued:
            result = {
                'sucess': True,
                'auth_token': login_log.token_issued,
                'user': {
                    'username': username
                }
            }
            return result, 200
        else:
            result = {
                'success': False,
                'message': 'username/password mismatch'
            }
            return result, 401
