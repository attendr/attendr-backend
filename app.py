import os
from datetime import datetime

from flask import Flask, redirect, render_template, session, url_for
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_restful import Api, Resource, reqparse
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from itsdangerous import URLSafeTimedSerializer, URLSafeSerializer
from wtforms import PasswordField, StringField
from wtforms.validators import InputRequired, Length


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'thisisasecretkeymeantforgivingasenseofsecurity'


db = SQLAlchemy(app)
admin = Admin(app, name='Attendr Admin', template_mode='bootstrap3')
api = Api(app)

timed_serializer = URLSafeTimedSerializer(app.config.get('SECRET_KEY'))
serializer = URLSafeSerializer(app.config.get('SECRET_KEY'))


class LoginLogs(db.Model):
    __tablename__ = 'login_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    time_stamp = db.Column(db.DateTime)
    token_issued = db.Column(db.Text, unique=True)
    login_expired = db.Column(db.Boolean)

    def __init__(self, user_id):
        self.user_id = user_id
        self.time_stamp = datetime.now()
        self.login_expired = False
        self.token_issued = self.issue_token(user_id)

    @staticmethod
    def issue_token(user_id):
        return serializer.dumps(user_id)


class User(object):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.UnicodeText, unique=True)
    full_name = db.Column(db.UnicodeText)


courses = db.Table('courses',
                   db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True),
                   db.Column('student_id', db.Integer, db.ForeignKey('student.id'), primary_key=True)
                   )


class Teacher(db.Model, User):
    id = db.Column(db.Integer, primary_key=True)
    courses_taught = db.relationship('Course', backref='teacher', lazy=True)


class Student(db.Model, User):
    id = db.Column(db.Integer, primary_key=True)
    courses_taken = db.relationship('Course', secondary=courses, lazy='subquery',
                                    backref=db.backref('students', lazy=True))
    attendance = db.relationship('Attendance', backref='student', lazy=True)


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.UnicodeText)
    course_teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    classes = db.relationship('Class', backref='course', lazy=True)


class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    date = db.Column(db.Date)
    attendance = db.relationship('Attendance', backref='class', lazy=True)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    attended = db.Column(db.Boolean, default=False)


db.create_all()

admin.add_view(ModelView(Student, db.session))
admin.add_view(ModelView(Teacher, db.session))
admin.add_view(ModelView(Course, db.session))
admin.add_view(ModelView(Class, db.session))
admin.add_view(ModelView(Attendance, db.session))
admin.add_view(ModelView(LoginLogs, db.session))


class LoginForm(FlaskForm):
    username = StringField('User Name', validators=[InputRequired('Username is a required field'),
                                                   Length(min=4, max=32, message='Username must be 4-32 characters')])
    password = PasswordField('Password', validators=[InputRequired('Password is a required field')])


@app.route('/login', methods=['GET'])
def login_role(role):
    form = LoginForm()
    if form.validate_on_submit():
        username, password = form.username.data, form.password.data
        teacher = Teacher.query.filter_by(username=username).first()
        if teacher:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('teacher_dashboard'))
        else:
            form.username.errors.append('Unknown username')
            return render_template('teacher_login.html', form=form)
    else:
       return render_template('teacher_login.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


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


class SendQRCode(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('data', type=str, required=True, help='Parmeter data is required')
        self.parser.add_argument('student_token', type=str, required=True, help='Parmeter student_token is required')
        super()

    def post(self):
        args = self.parser.parse_args(strict=True)
        data = args.get('data')
        student_data = args.get('student_token')
        try:
            data = timed_serializer.loads(data, max_age=10)  # 10 seconds to allow for double way network latency
            student_id = serializer.loads(student_data)
            existing_attendance = Attendance.query.filter_by(course_id=data['course_id']).filter_by(class_id=data['class_id']).filter_by(student_id=student_id).first()
            if existing_attendance:
                return {
                    'sucess': True,
                    'message': 'Already marked'
                }, 202
            else:
                attendance = Attendance(data['course_id'], data['class_id'], student_id, True)
                db.session.add(attendance)
                db.session.commit()
                return {
                    'sucess': True,
                    'message': 'Attendance marked!'
                }, 200
        except:
            result = {
                'success': False,
                'error': 'QR Code expired'
            }


class MakeQRCode(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('course_id', type=str, required=True, help='Parmeter course_id is required')
        self.parser.add_argument('class_id', type=str, required=True, help='Parmeter class_id is required')
        super()

    def get(self):
        args = self.parser.parse_args(strict=True)
        try:
            data = {'course_id': args.get('course_id'), 'class_id': args.get('class_id')}
            data = timed_serializer.dumps(data)
            return {
                    'sucess': True,
                    'image_url': f'https://api.qrserver.com/v1/create-qr-code/?data={data}&size=600x600'
            }, 200
        except:
            return {
                'success': False,
                'error': 'QR Code could not be generated'
            }, 500


api.add_resource(Login, '/login')
api.add_resource(SendQRCode, '/mark')
api.add_resource(MakeQRCode, '/getqr')

if __name__ == '__main__':
    app.debug = False
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, threaded=True)
