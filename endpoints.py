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
            courses = []
            for course in student.courses_taken:
                attendance_list = [course_class.attendance.attended for course_class in course.classes]
                attendance_percentage = 100 * attendance_list.count(True) / len(attendance_list)
                attendance_percentage = int("{0:.2f}".format(attendance_percentage))
                courses.append({'course_name': course.course_name, 'course_attendance': attendance_percentage})
            result = {
                'sucess': True,
                'auth_token': login_log.token_issued,
                'user': {
                    'username': username,
                    'no_of_courses': len(student.courses_taken),
                    'average_attendance': int("{0:.2f}".format(sum([course.attendance_percentage for course in courses]) / len(courses)))
                },
                'courses': courses
            }
            return result, 200
        else:
            result = {
                'success': False,
                'message': 'username/password mismatch'
            }
            return result, 401
