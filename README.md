# Teacher-Student Attendance Management System

This project is a web-based application developed using Flask for managing attendance records of both teachers and students.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## Introduction

The Teacher-Student Attendance Management System is designed to streamline the process of recording and tracking attendance for teachers and students. It is suitable for educational institutions, training centers, or any organization that requires an efficient attendance management system.

## Features

- Teacher and student registration
- Course management
- Attendance recording and tracking
- QR code generation for attendance
- Dashboard for teachers and students

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Joeltabe/attendance-system.git
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   export FLASK_APP=app.py
   export FLASK_ENV=development
   ```

4. Initialize the database:
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

5. Run the Flask application:
   ```bash
   flask run
   ```

## Usage

1. Open a web browser and navigate to `http://localhost:5000`.
2. Log in as a teacher or student using the provided credentials.
3. Navigate through the dashboard to view courses, record attendance, or manage profiles.

## Configuration

The application can be configured by modifying environment variables or configuration files. Refer to the documentation for detailed configuration instructions.

## Contributing

Contributions to this project are welcome! To contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Make your changes and commit them (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new pull request.

## License

This project is licensed under the [MIT License](LICENSE).

## Usage Disclaimer

This project is provided as-is and without warranty. The developers are not liable for any damages or losses resulting from the use of this software.


## Contact

For support or inquiries, please contact [Project Developer](mailto:joeltabe3@example.com).
