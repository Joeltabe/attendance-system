from flask import Flask
from flask_bcrypt import Bcrypt
from teacher import teacher_bp
from student import student_bp
import threading

app_teacher = Flask(__name__)
app_student = Flask(__name__)

# Initialize Flask-Bcrypt for both apps
bcrypt_teacher = Bcrypt(app_teacher)
bcrypt_student = Bcrypt(app_student)

# Register teacher module with '/teacher' prefix
app_teacher.register_blueprint(teacher_bp, url_prefix='/teacher')

# Register student module with '/student' prefix
app_student.register_blueprint(student_bp, url_prefix='/student')

def run_app(app, port):
    app.run(port=port)

if __name__ == '__main__':
    # Start each app in a separate thread
    teacher_thread = threading.Thread(target=run_app, args=(app_teacher, 5000))
    student_thread = threading.Thread(target=run_app, args=(app_student, 5001))

    teacher_thread.start()
    student_thread.start()
