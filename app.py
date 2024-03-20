from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from urllib.parse import quote_plus
from functools import wraps
import pymongo
from bson import ObjectId
from datetime import datetime
import os
import qrcode
from collections import Counter

app = Flask(__name__)
bcrypt = Bcrypt()

# Connect to MongoDB
username = "joeltabe3"
password = "j0@lmessi"

# Escape the username and password
escaped_username = quote_plus(username)
escaped_password = quote_plus(password)

# Build the connection string with the escaped username and password
connection_string = f"mongodb+srv://{escaped_username}:{escaped_password}@cluster0.dw2mdqb.mongodb.net/"

client = MongoClient(connection_string)  # Update with your MongoDB URI
db = client["teacher_app"]  # Database name: teacher_app

# Define collections
teachers = db["teachers"]
students = db["students"]
courses = db["courses"]
attendance_records = db["attendance_records"]
courses.update_many({}, {"$set": {"enrolled_students": []}})

# Custom middleware to check if the user is authenticated and authorized
def login_required_teacher(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            flash("You need to log in first.", "danger")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return decorated_function

# Custom middleware to check if the user is authenticated and authorized as a student
def login_required_student(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            flash("You need to log in first.", "danger")
            return redirect(url_for("login"))
        elif not students.find_one({"username": session["username"]}):
            flash("Access denied. You are not authorized as a student.", "danger")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return decorated_function

# Calculate attendance percentage for a course
def get_attendance_percentage(course_code):
    course_attendance_records = list(attendance_records.find({"course_code": course_code}))
    total_classes = len(course_attendance_records)
    attended_classes = sum(1 for record in course_attendance_records if record["status"] == "Present")
    attendance_percentage = (attended_classes / total_classes) * 100 if total_classes > 0 else 0
    return attendance_percentage


@app.route("/generate_qr_code/<course_id>")
def generate_qr_code(course_id):
    # Your code to generate QR code for the given course_id
    return "QR code generation logic goes here"

@app.route("/attendance_data")
@login_required_teacher
def get_attendance_data():
    # Fetch teacher's username from session
    teacher_username = session.get("username")

    # Fetch courses taught by the teacher
    teacher_courses = courses.find({"teacher": teacher_username})

    # Initialize dictionary to store attendance data
    attendance_data = {}

    # Populate attendance data for each course
    for course in teacher_courses:
        attendance_data[course["name"]] = get_attendance_percentage(course["code"])

    return jsonify(attendance_data)

# Route for teacher registration
@app.route("/register_teacher", methods=["GET", "POST"])
def register_teacher():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check if the username already exists
        if teachers.find_one({"username": username}):
            flash("Username already exists. Please choose a different username.", "danger")
            return redirect(url_for("register_teacher"))

        # Hash the password before storing it
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # Insert the teacher data into the database
        teachers.insert_one({"username": username, "password": hashed_password})
        flash("Registration successful. You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        # Check if it's a teacher login
        teacher = teachers.find_one({"username": username})
        if teacher and bcrypt.check_password_hash(teacher["password"], password):
            session["username"] = username
            flash("You are now logged in.", "success")
            return redirect(url_for("dashboard"))  # Redirect teacher to their dashboard
        else:
            # Check if it's a student login
            student = students.find_one({"username": username})
            if student and bcrypt.check_password_hash(student["password"], password):
                session["username"] = username
                flash("You are now logged in.", "success")
                # Redirect student to their dashboard or any other page
                return redirect(url_for("student_dashboard"))
            else:
                flash("Invalid username or password. Please try again.", "danger")
    return render_template("login.html")

@app.route("/student_dashboard")
@login_required_student
def student_dashboard():
    student_username = session.get("username")
    
    # Fetch student information including matricule
    student_info = students.find_one({"username": student_username})

    # Fetch courses in which the student is enrolled
    enrolled_courses = courses.find({"students": student_info["matricule"]})

    # Fetch attendance records for the student across all courses
    student_attendance_records = attendance_records.find({"student_id": student_info["matricule"]})
    
    return render_template("dashboard_student.html", student_info=student_info, student_courses=enrolled_courses, student_attendance=student_attendance_records)

@app.route("/")
@login_required_teacher
def dashboard():
    teacher_username = session.get("username")
    teacher_courses = list(courses.find({"teacher": teacher_username}))  # Fetch courses for the logged-in teacher
    total_students = students.count_documents({})
    student_attendance_count = Counter(record["student_id"] for record in attendance_records.find({"course_code": {"$in": [course["code"] for course in teacher_courses]}}))
    top_present_student_id = student_attendance_count.most_common(1)[0][0] if student_attendance_count else None
    most_absent_student_id = student_attendance_count.most_common()[-1][0] if student_attendance_count else None
    top_present_student = students.find_one({"_id": ObjectId(top_present_student_id)}) if top_present_student_id else None
    most_absent_student = students.find_one({"matricule": most_absent_student_id}) if most_absent_student_id else None
    top_present_student_name = top_present_student.get("name", "Unknown") if top_present_student else "Unknown"
    most_absent_student_name = most_absent_student.get("name", "Unknown") if most_absent_student else "Unknown"
    teacher_courses_data = [{"name": course["name"], "attendance_percentage": get_attendance_percentage(course["code"])} for course in teacher_courses]

    # Fetch attendance history for each course
    attendance_history = {}
    for course in teacher_courses:
        attendance_history[course["code"]] = list(attendance_records.find({"course_code": course["code"]}))

    return render_template("dashboard.html", teacher_courses=teacher_courses_data, total_students=total_students, student_information={"top_student": top_present_student_name, "most_absent_student": most_absent_student_name}, attendance_history=attendance_history)

@app.route("/courses")
@login_required_teacher
def view_courses():
    # Retrieve all courses and their corresponding total number of enrolled students
    courses_data = []
    for course in courses.find():
        total_students = len(course.get("students", []))
        # Check if 'code' field is present in the course document
        if 'code' in course:
            course_code = course["code"]
        else:
            course_code = None  # Assign None if 'code' field is missing
        courses_data.append({
            "code": course_code,
            "name": course["name"],
            "total_students": total_students
        })
    return render_template("courses.html", courses=courses_data)



# Sort Courses
@app.route("/sort_courses/<criteria>")
@login_required_teacher
def sort_courses(criteria):
    if criteria == "name":
        sorted_courses = courses.find().sort("name", pymongo.ASCENDING)
    elif criteria == "total_students":
        sorted_courses = sorted(courses.find(), key=lambda x: len(x.get("students", [])), reverse=True)
    else:
        sorted_courses = courses.find()  # Default sorting
    
    courses_data = [{"name": course["name"], "total_students": len(course.get("students", []))} for course in sorted_courses]
    return render_template("courses.html", courses=courses_data)

# Add Course
@app.route("/add_course", methods=["GET", "POST"])
@login_required_teacher
def add_course():
    if request.method == "POST":
        course_name = request.form.get("course_name")
        course_code = request.form.get("course_code")  # Retrieve course code from form data
        teacher_username = session.get("username")
        
        if not course_name:
            flash("Course name is required.", "danger")
            return redirect(url_for("add_course"))
        
        if not course_code:
            flash("Course code is required.", "danger")  # Validate if course code is provided
            return redirect(url_for("add_course"))
        
        # Check if the course with the same code already exists for the current teacher
        existing_course = courses.find_one({"code": course_code, "teacher": teacher_username})
        if existing_course:
            flash("Course with the same code already exists.", "danger")
            return redirect(url_for("add_course"))
        
        new_course = {
            "name": course_name,
            "code": course_code,  # Include course code in the new course document
            "teacher": teacher_username,
            "students": []  # Initially, no students are enrolled
        }
        courses.insert_one(new_course)
        flash("Course added successfully.", "success")
        return redirect(url_for("view_courses"))
    return render_template("add_course.html")



# Modify the delete_course route to use course code
@app.route("/delete_course/<course_code>", methods=["GET", "POST"])
def delete_course(course_code):
    # Ensure that the course exists before attempting to delete
    course = courses.find_one({"code": course_code})
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("view_courses"))
    # Delete attendance records related to the course
    attendance_records.delete_many({"course_code": course_code})
    # Delete the course document
    courses.delete_one({"code": course_code})
    flash("Course deleted successfully.", "success")
    return redirect(url_for("view_courses"))  # Redirect to the view_courses route


@app.route("/assign_students", methods=["GET", "POST"])
@login_required_teacher
def assign_students():
    if request.method == "POST":
        # Get the selected course ID and list of selected student matricules from the form
        course_id = request.form.get("course_id")
        student_matricules = request.form.getlist("student_matricule")
        
        # Validate form data
        if not course_id or not student_matricules:
            flash("Invalid form data. Please select a course and at least one student.", "danger")
            return redirect(url_for("assign_students"))

        # Update the course document in the database to assign selected students
        result = courses.update_one(
            {"_id": ObjectId(course_id)},
            {"$set": {"students": student_matricules}}
        )
        
        if result.modified_count == 0:
            flash("Failed to assign students to the course. Please try again.", "danger")
        else:
            flash("Students assigned to the course successfully.", "success")
        
        return redirect(url_for("view_courses"))  # Redirect to the view_courses route or wherever appropriate

    # Fetch all courses and students from the database
    all_courses = courses.find()
    all_students = students.find()

    return render_template("assign_students.html", courses=all_courses, students=all_students)

@app.route("/get_enrolled_students", methods=["POST"])
@login_required_teacher
def get_enrolled_students():
    if request.method == "POST":
        course_code = request.json.get("course_code")
        # Fetch the course document based on the course_code
        course = courses.find_one({"code": course_code})
        if not course:
            return jsonify({"error": "Course not found"}), 404

        # Fetch enrolled students for the course
        enrolled_students = students.find({"_id": {"$in": [ObjectId(student_id) for student_id in course["students"]]}})
        student_list = [{"_id": str(student["_id"]), "name": student["name"]} for student in enrolled_students]
        return jsonify(student_list)


# Collect Attendance

@app.route("/collect_attendance/<course_code>", methods=["GET", "POST"])
@login_required_teacher
def collect_attendance(course_code):
    # Retrieve the course details
    course = courses.find_one({"code": course_code})
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("view_courses"))

    if request.method == "POST":
        # Get attendance data from the form submission
        attendance_data = request.form.to_dict()
        # Get the current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        # Update attendance records in the database
        for student_id, status in attendance_data.items():
            # Ensure the student is enrolled in the course
            if student_id in course["students"]:
                # Insert or update attendance record for the student in the course
                attendance_records.update_one(
                    {"student_id": student_id, "course_code": course_code},  # Use student ID
                    {"$set": {"status": status, "date": current_date}},  # Include date in the record
                    upsert=True
                )

        flash("Attendance collected successfully.", "success")
        return redirect(url_for("view_courses"))

    # Fetch enrolled students for the course with their names
    enrolled_students = []
    for student_id in course["students"]:
        student = students.find_one({"matricule": student_id})
        if student:
            enrolled_students.append({"matricule": student_id, "name": student["name"]})

    return render_template("collect_attendance.html", course=course, students=enrolled_students)

@app.route("/view_attendance/<course_code>", methods=["GET", "POST"])
@login_required_teacher
def view_attendance(course_code):
    # Retrieve the course details
    course = courses.find_one({"code": course_code})
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("view_courses"))

    # Fetch attendance records for the course
    attendance_records_course = list(attendance_records.find({"course_code": course_code}))

    # Fetch student names from student matricules
    for record in attendance_records_course:
        student = students.find_one({"matricule": record["student_id"]})
        if student:
            record["student_name"] = student["username"]  # Add student's name to the record

    if request.method == "POST":
        selected_date = request.form.get("selected_date")
        if selected_date:
            selected_date = datetime.strptime(selected_date, "%Y-%m-%d")
            attendance_records_course = [record for record in attendance_records_course if record.get("date") == selected_date.date()]

    return render_template("view_attendance.html", course=course, attendance_records=attendance_records_course)

@app.route("/register_student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        matricule = request.form.get("matricule")  # Retrieve matricule from form data

        # Check if the username already exists
        if students.find_one({"username": username}):
            flash("Username already exists. Please choose a different username.", "danger")
            return redirect(url_for("register_student"))

        # Hash the password before storing it
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        # Insert the student data into the database
        students.insert_one({"username": username, "password": hashed_password, "matricule": matricule})  # Include matricule
        flash("Registration successful. You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("register_student.html")

@app.route("/available_courses", methods=["GET", "POST"])
@login_required_student
def available_courses():
    if request.method == "POST":
        # Get the selected course ID from the form
        course_id = request.form.get("course_id")
        
        # Fetch the course document from the database
        course = courses.find_one({"_id": ObjectId(course_id)})
        
        if not course:
            flash("Course not found.", "danger")
            return redirect(url_for("available_courses"))
        
        # Check if the student is already enrolled in the course
        student_username = session.get("username")
        student = students.find_one({"username": student_username})
        if student and student["matricule"] in course.get("students", []):  # Update here to use matricule
            flash("You are already enrolled in this course.", "warning")
            return redirect(url_for("available_courses"))
        
        # Add the student to the list of enrolled students for the course
        courses.update_one({"_id": ObjectId(course_id)}, {"$push": {"students": student["matricule"]}})  # Update here to use matricule
        
        flash("Enrolled in the course successfully.", "success")
        return redirect(url_for("available_courses"))
    
    # Fetch all available courses from the database
    all_courses = courses.find()
    
    return render_template("available_courses.html", courses=all_courses)

@app.route("/profile", methods=["GET", "POST"])
@login_required_student
def student_profile():
    student_username = session.get("username")
    student = students.find_one({"username": student_username})
    
    if request.method == "POST":
        # Retrieve form data
        new_username = request.form.get("username")
        new_password = request.form.get("password")
        new_matricule = request.form.get("matricule")

        # Update student information in the database
        update_data = {}
        if new_username:
            update_data["username"] = new_username
        if new_matricule:
            update_data["matricule"] = new_matricule
        if new_password:
            # Hash the new password before storing it
            hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")
            update_data["password"] = hashed_password
        
        students.update_one({"username": student_username}, {"$set": update_data})
        flash("Profile updated successfully.", "success")
        # Redirect to the profile page to reflect the changes
        return redirect(url_for("student_profile"))
    
    return render_template("profile_student.html", student=student)

# Logout route
@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("You are now logged out.", "success")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.secret_key = "super_secret_key"
    app.run(debug=True)