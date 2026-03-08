# ABC College Student Portal

A full-featured role-based college student portal built with Flask, PostgreSQL, Jinja2, and vanilla HTML/CSS/JS.

---

## 🗂 Project Structure

```
college_portal/
├── run.py                  ← Entry point (python run.py)
├── seed.py                 ← DB seed script (run once after init)
├── requirements.txt
├── .env.example            ← Copy to .env and fill in
│
└── app/
    ├── __init__.py         ← App factory, extensions
    ├── models.py           ← All SQLAlchemy models
    ├── forms.py            ← All WTForms
    ├── decorators.py       ← Role-based access decorators
    │
    ├── routes/
    │   ├── auth.py         ← Login, Register, Dashboard router
    │   ├── student.py      ← Student-only pages
    │   ├── teacher.py      ← Teacher pages (marks, attendance, assignments)
    │   ├── hod.py          ← HOD pages (roster, subject assignments)
    │   ├── admin.py        ← Admin pages (users, depts, subjects)
    │   └── notices.py      ← Shared notice board
    │
    ├── templates/
    │   ├── base.html       ← Master layout with sidebar
    │   ├── auth/           ← login.html, register.html
    │   ├── student/        ← All student pages
    │   ├── teacher/        ← All teacher pages
    │   ├── hod/            ← All HOD pages
    │   ├── admin/          ← All admin pages
    │   └── shared/         ← Notices (visible to all roles)
    │
    └── static/
        ├── css/main.css    ← Blue & white theme
        └── js/main.js      ← Alert auto-dismiss, confirm prompts
```

---

## ⚙️ Setup Instructions

### 1. Prerequisites
- Python 3.10+
- PostgreSQL installed and running
- pip

### 2. Clone / copy the project
```bash
cd college_portal
```

### 3. Create a virtual environment
```bash
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Set up PostgreSQL
```sql
-- In psql:
CREATE DATABASE college_portal;
CREATE USER portal_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE college_portal TO portal_user;
```

### 6. Configure environment
```bash
cp .env.example .env
```
Edit `.env`:
```
SECRET_KEY=some-random-long-string
DATABASE_URL=postgresql://portal_user:yourpassword@localhost:5432/college_portal
FLASK_APP=run.py
FLASK_ENV=development
```

### 7. Initialize the database
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 8. Seed the database (creates admin + sample data)
```bash
python seed.py
```

### 9. Run the app
```bash
python run.py
```
Visit: **http://localhost:5000/auth/login**

---

## 🔑 Default Credentials

| Role   | Email                      | Password   |
|--------|----------------------------|------------|
| Admin  | admin@abccollege.edu       | admin1234  |

Register additional students and teachers via **/auth/register**

To make a teacher a HOD:
- Log in as Admin → Users → Change their role to `HOD`

---

## 🔐 Role Permissions

| Feature                    | Student | Teacher | HOD | Admin |
|----------------------------|:-------:|:-------:|:---:|:-----:|
| View marks                 | ✅      | —       | —   | ✅   |
| Edit marks                 | —       | ✅      | ✅  | ✅   |
| View attendance            | ✅      | —       | —   | ✅   |
| Mark attendance            | —       | ✅      | ✅  | ✅   |
| Course registration        | ✅      | —       | —   | ✅   |
| Exam registration          | ✅      | —       | —   | ✅   |
| Fee payment                | ✅      | —       | —   | ✅   |
| Projects/Internships       | ✅      | —       | —   | ✅   |
| Post assignments           | —       | ✅      | ✅  | ✅   |
| Submit assignments         | ✅      | —       | —   | —    |
| Post notices               | —       | ✅      | ✅  | ✅   |
| View notices               | ✅      | ✅      | ✅  | ✅   |
| Manage teacher roster      | —       | —       | ✅  | ✅   |
| Assign subjects to teachers| —       | —       | ✅  | ✅   |
| Manage users               | —       | —       | —   | ✅   |
| Manage departments         | —       | —       | —   | ✅   |
| Manage subjects            | —       | —       | —   | ✅   |

---

## 🔗 URL Structure

```
/auth/login             ← Login page
/auth/register          ← Registration
/auth/logout
/auth/dashboard         ← Redirects to role-specific dashboard

/student/dashboard
/student/marks/<sem>
/student/attendance/<sem>
/student/course-registration
/student/exam-registration
/student/fee-payment
/student/projects
/student/assignments
/student/assignments/<id>/submit

/teacher/dashboard
/teacher/marks/<sem>
/teacher/marks/<sem>/subject/<id>
/teacher/attendance/<sem>
/teacher/attendance/<sem>/subject/<id>
/teacher/assignments
/teacher/assignments/<id>/submissions

/hod/dashboard
/hod/teachers
/hod/teachers/<id>/edit
/hod/subject-assignments

/admin/dashboard
/admin/users
/admin/departments
/admin/subjects

/notices/               ← Notice board (all roles)
/notices/post
/notices/<id>
```

---

## 🛠 Adding Features Later

- **File uploads** for assignments: Add `Flask-Uploads` or store to S3
- **Email notifications**: Add `Flask-Mail`  
- **Timetable**: Create a new `Timetable` model + routes
- **Exam timetable**: `ExamTimetable` model linked to `ExamRegistration`
- **Revaluation / I-Grade**: New models + student-facing forms
- **Photocopy history**: New model + student route

---

## 📦 Tech Stack

| Layer     | Tech                          |
|-----------|-------------------------------|
| Backend   | Python 3 + Flask              |
| ORM       | SQLAlchemy (Flask-SQLAlchemy) |
| DB        | PostgreSQL                    |
| Auth      | Flask-Login                   |
| Forms     | Flask-WTF + WTForms           |
| Migrations| Flask-Migrate (Alembic)       |
| Templates | Jinja2                        |
| Frontend  | HTML5 + CSS3 + Vanilla JS     |
| Fonts     | Google Fonts (DM Sans + Syne) |
