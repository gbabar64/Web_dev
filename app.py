from flask import Flask,jsonify
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
import json
from werkzeug.exceptions import HTTPException
from flask import make_response
from flask_restful import Resource
from flask_restful import marshal_with, fields, reqparse

#Initiating db browser and flask_restful for insomnia
db = SQLAlchemy()
app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///api_database.sqlite3"
db.init_app(app)
api = Api(app)
app.app_context().push()

#Defining models
class Course(db.Model):
    __tablename__ = 'course'
    course_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    course_name = db.Column(db.String, nullable=False)
    course_code = db.Column(db.String, unique=True, nullable=False)
    course_description = db.Column(db.String)
    #articles = relationship('Article', secondary="article_author")

class Student(db.Model):
    __tablename__ = 'student'
    student_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    roll_number = db.Column(db.String, unique=True)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String)
    #last_name = db.relationship("User", secondary='article_author')

class Enrollment(db.Model): #association table
    __tablename__ = 'enrollment'
    enrollment_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.student_id"), primary_key=True, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("course.course_id"), primary_key=True, nullable=False)

#Defining Error Handlers
class NotFoundError(HTTPException):
    def __init__(self,status_code):
        self.response = make_response('',status_code)

class BusinessValidationError(HTTPException):
    def __init__(self,status_code,error_code,error_message):
        message = {"error_code":error_code, "error_message":error_message}
        self.response = make_response(json.dumps(message),status_code)

#Defining classes for operations on student,course and enrollment table

course_parser = reqparse.RequestParser()
course_parser.add_argument('course_name')
course_parser.add_argument('course_code')
course_parser.add_argument('course_description')

#operation on course
class CourseApi(Resource):
    def get(self, course_id):
        course_data = Course.query.filter_by(course_id=course_id).first()
        if course_data is None:
            raise NotFoundError(status_code=404)
        return {
  "course_id": course_data.course_id,
  "course_name": course_data.course_name,
  "course_code": course_data.course_code,
  "course_description": course_data.course_description
},200
    def put(self, course_id):
        #Get course details corresponding to course_id and raise error if not found
        course_data = Course.query.filter_by(course_id=course_id).first()
        if course_data is None:
            raise NotFoundError(status_code=404)

        #get data which has to update
        args = course_parser.parse_args()
        course_name_toupdate = args.get('course_name',None)
        course_code_toupdate = args.get('course_code', None)
        course_description_toupdate = args.get('course_description', None)

        #checking nullability
        if course_name_toupdate is None:
            raise BusinessValidationError(status_code=400,error_code="COURSE001",error_message="Course Name is required")
        if course_code_toupdate is None:
            raise BusinessValidationError(status_code=400,error_code="COURSE002",error_message="Course Code is required")

        # check whether course_code repeated,if yes then raise error
        course_code_repeat = Course.query.filter_by(course_code=course_code_toupdate).first()
        if course_code_repeat:
            raise BusinessValidationError(status_code=400,error_code="",error_message="course_code already exists")

        #update data
        course_data.course_code = course_code_toupdate
        course_data.course_name = course_name_toupdate
        course_data.course_description = course_description_toupdate
        db.session.add(course_data)
        db.session.commit()
        return {
  "course_id": course_data.course_id,
  "course_name": course_data.course_name,
  "course_code": course_data.course_code,
  "course_description": course_data.course_description
},200

    def delete(self, course_id):
        course_todelete = Course.query.filter_by(course_id=course_id).first()

        #check course exist or not,if no then throw error
        if course_todelete is None:
            raise NotFoundError(status_code=404)

        #delete course
        db.session.delete(course_todelete)
        db.session.commit()
        return "",200
    def post(self):
        #Get course_data to create resource
        args = course_parser.parse_args()
        course_name_toadd = args.get('course_name', None)
        course_code_toadd = args.get('course_code', None)
        course_description_toadd = args.get('course_description', None)

        # checking nullability
        if course_name_toadd is None:
            raise BusinessValidationError(status_code=400, error_code="COURSE001",
                                          error_message="Course Name is required")
        if course_code_toadd is None:
            raise BusinessValidationError(status_code=400, error_code="COURSE002",
                                          error_message="Course Code is required")

        # check whether course_code repeated(need to be unique),if yes then raise error
        course_code_repeat = Course.query.filter_by(course_code=course_code_toadd).first()
        if course_code_repeat:
            raise NotFoundError(status_code=409)

        #adding new_course
        new_course = Course(course_name=course_name_toadd, course_code=course_code_toadd,
                            course_description=course_description_toadd)
        db.session.add(new_course)
        db.session.commit()
        return {
  "course_name": course_name_toadd,
  "course_code": course_code_toadd,
  "course_description": course_description_toadd
},201

#Operation on Student

student_parser = reqparse.RequestParser()
student_parser.add_argument('roll_number')
student_parser.add_argument('first_name')
student_parser.add_argument('last_name')
class StudentApi(Resource):
    def get(self, student_id):
        student_data = Student.query.filter_by(student_id=student_id).first()
        if student_data is None:
            raise NotFoundError(status_code=404)
        return {
            "student_id": student_data.student_id,
            "roll_number": student_data.roll_number,
            "first_name": student_data.first_name,
            "last_name": student_data.last_name
        },200

    def put(self, student_id):
        # Get course details corresponding to student_id and raise error if not found
        student_data = Student.query.filter_by(student_id=student_id).first()
        if student_data is None:
            raise NotFoundError(status_code=404)

        # get data which has to update
        args = student_parser.parse_args()
        rollno_toupdate = args.get('roll_number', None)
        first_name_toupdate = args.get('first_name', None)
        last_name_toupdate = args.get('last_name', None)

        # checking nullability
        if rollno_toupdate is None:
            raise BusinessValidationError(status_code=400, error_code="STUDENT001",
                                          error_message="Roll Number required")
        if first_name_toupdate is None:
            raise BusinessValidationError(status_code=400, error_code="STUDENT002",
                                          error_message="First Name is required")

        # check whether roll_no repeated,if yes then raise error
        rollno_repeat = Student.query.filter_by(roll_number=rollno_toupdate).first()
        if rollno_repeat:
            raise BusinessValidationError(status_code=400, error_code="Rollno1", error_message="Roll Number already exists")

        # update data
        student_data.roll_number = rollno_toupdate
        student_data.first_name = first_name_toupdate
        student_data.last_name = last_name_toupdate
        db.session.add(student_data)
        db.session.commit()
        return {
            "student_id": student_data.student_id,
            "roll_number": student_data.roll_number,
            "first_name": student_data.first_name,
            "last_name": student_data.last_name
        }, 200
    def delete(self, student_id):
        student_todelete = Student.query.filter_by(student_id=student_id).first()

        # check student exist or not,if no then throw error
        if student_todelete is None:
            raise NotFoundError(status_code=404)

        # delete student
        db.session.delete(student_todelete)
        db.session.commit()
        return "", 200
    def post(self):
        # Get student_data to create student
        args = student_parser.parse_args()
        rollno_toadd = args.get('roll_number', None)
        first_name_toadd = args.get('first_name', None)
        last_name_toadd = args.get('last_name', None)

        # checking nullability
        if rollno_toadd is None:
            raise BusinessValidationError(status_code=400, error_code="STUDENT001",
                                          error_message="Roll Number required")
        if first_name_toadd is None:
            raise BusinessValidationError(status_code=400, error_code="STUDENT002",
                                          error_message="First Name is required")

        # check whether roll_no repeated,if yes then raise error
        rollno_repeat = Student.query.filter_by(roll_number=rollno_toadd).first()
        if rollno_repeat:
            raise NotFoundError(status_code=409)

        # adding new_student
        new_student = Student(roll_number=rollno_toadd, first_name=first_name_toadd,
                            last_name=last_name_toadd)
        db.session.add(new_student)
        db.session.commit()
        return {
            "roll_number": rollno_toadd,
            "first_name": first_name_toadd,
            "last_name": last_name_toadd
        },201

#operation on enroolments
enrollment_field={
   'enrollment_id': fields.Integer,
   'student_id': fields.Integer,
   'course_id': fields.Integer,
}
class EnrollmentApi(Resource):
    @marshal_with(enrollment_field)
    def get(self, student_id):
        #check student_id valid or not
        student_valid = Student.query.filter_by(student_id=student_id).first()
        if student_valid is None:
            raise BusinessValidationError(status_code=400,error_code="ENROLLMENT002",error_message="Student does not exist")
        #check student exists or not
        enrollments = Enrollment.query.filter_by(student_id=student_id).all()
        print(enrollments,Enrollment.query.filter_by(student_id=student_id).all())
        if len(enrollments)==0:
            raise NotFoundError(status_code=404)
        #Get all enrollments of student
        enroll_lis =[]
        for enrollment in enrollments:
            enrollment_dict = {
                'enrollment_id': enrollment.enrollment_id,
                'student_id': enrollment.student_id,
                'course_id': enrollment.course_id,
            }
            enroll_lis.append(enrollment_dict)
        return enroll_lis,200
    def post(self, student_id):
        #check student exists or not
        student = Student.query.filter_by(student_id=student_id).first()
        if student is None:
            raise BusinessValidationError(status_code=400,error_code="ENROLLMENT002",error_message="Student does not exist.")

        course_parser.add_argument('course_id')
        args = course_parser.parse_args()
        course_id = args.get('course_id',None)

        #check nullability
        if course_id is None:
           raise BusinessValidationError(status_code=400,error_code='Error1',error_message="course_id is required")

        #check course_id exist or not
        course_ids = Course.query.filter_by(course_id=course_id).first()
        if course_ids is None:
            raise BusinessValidationError(status_code=400,error_code="ENROLLMENT001",error_message="course_id does not exist")

        #check enrollment already exist or not
        enrollment = Enrollment.query.filter_by(student_id=student_id,course_id=course_ids.course_id).first()
        if enrollment:
            raise BusinessValidationError(status_code=400,error_code="Error2",error_message="enrollment already exists")

        #add enrollment
        new_enrollment = Enrollment(student_id=student_id, course_id=course_ids.course_id)
        db.session.add(new_enrollment)
        db.session.commit()
        return "",201

    def delete(self, student_id, course_id):
        #check student_id and course_id exists or not
        student = Student.query.filter_by(student_id=student_id).first()
        course = Course.query.filter_by(course_id=course_id).first()
        if student is None or course is None:
            raise BusinessValidationError(status_code=400,error_code="Error23",error_message="Invalid Student Or Course ID")
        # check enrollment for student
        enrollment_todelete = Enrollment.query.filter_by(student_id=student_id,course_id=course_id).first()
        if enrollment_todelete is None:
            raise NotFoundError(status_code=404)
        #delete enrollment
        db.session.delete(enrollment_todelete)
        db.session.commit()
        return "",200

api.add_resource(CourseApi,'/api/course','/api/course/<int:course_id>')
api.add_resource(StudentApi,'/api/student','/api/student/<int:student_id>')
api.add_resource(EnrollmentApi,'/api/student/<int:student_id>/course','/api/student/<int:student_id>/course/<int:course_id>')


if __name__ == "__main__":
    app.run(debug=True,port=5000)

