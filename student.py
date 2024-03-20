from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from urllib.parse import quote_plus
from flask import Blueprint

student_bp = Blueprint('student', __name__)

# Connect to MongoDB
username = "joeltabe3"
password = "j0@lmessi"

# Escape the username and password
escaped_username = quote_plus(username)
escaped_password = quote_plus(password)

# Build the connection string with the escaped username and password
connection_string = f"mongodb+srv://{escaped_username}:{escaped_password}@cluster0.dw2mdqb.mongodb.net/"

client = MongoClient(connection_string)  
db = client["teacher_app"]  # Database name: teacher_app
students = db["students"]

bcrypt = Bcrypt()

# Student Login
@student_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        student = students.find_one({"email": email})
        if student and bcrypt.check_password_hash(student["password"], password):
            session["email"] = email
            flash("You are now logged in.", "success")
            return redirect(url_for("student.dashboard"))
        else:
            flash("Invalid email or password. Please try again.", "danger")
    return render_template("student/login.html")

# Student Registration
@student_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        existing_student = students.find_one({"email": email})
        if existing_student:
            flash("Email already registered. Please use a different email.", "danger")
            return redirect(url_for("student.register"))

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        students.insert_one({"name": name, "email": email, "password": hashed_password})
        flash("Registration successful. You can now log in.", "success")
        return redirect(url_for("student.login"))

    return render_template("student/register.html")
