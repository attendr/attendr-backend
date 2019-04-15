from app import db
from datetime import datetime
from secrets import token_urlsafe


class LoginLogs(db.Model):
    __tablename__ = 'login_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    time_stamp = db.Column(db.DateTime)
    token_issued = db.Column(db.Text, unique=True)
    login_expired = db.Column(db.Boolean)

    def __init__(self, user_id):
        self.user_id = user_id
        self.time_stamp = datetime.now()
        self.login_expired = False
        self.token_issued = self.issue_token()

    @staticmethod
    def issue_token():
        return token_urlsafe(16)

    def __repr__(self):
        return f'<LoginLog(username={self.user.username}, timestamp={self.time})>'


class User(object):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.UnicodeText, unique=True)
    full_name = db.Column(db.UnicodeText)


class Teacher(db.Model, User):
    id = db.Column(db.Integer, primary_key=True)
    courses_taught = db.relationship('Course', backref='teacher', lazy=True)
    courses = db.Table('courses',
                   db.Column('course_id', db.Integer, db.ForeignKey('course.id'), primary_key=True),
                   db.Column('student_id', db.Integer, db.ForeignKey('student.id'), primary_key=True)
                   )


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
