"""
seed.py — Run once after db init to create:
  - Admin user
  - Sample departments
  - Sample subjects

Usage:
  flask shell
  >>> from seed import seed_all; seed_all()

Or directly:
  python seed.py
"""

from app import create_app, db
from app.models import User, StudentProfile, TeacherProfile, Department, Subject

app = create_app()


def seed_all():
    with app.app_context():
        db.create_all()

        # ── Admin ──────────────────────────────────
        if not User.query.filter_by(email='admin@abccollege.edu').first():
            admin = User(name='Super Admin', email='admin@abccollege.edu', role='admin')
            admin.set_password('admin1234')
            db.session.add(admin)
            print('[+] Admin user created: admin@abccollege.edu / admin1234')

        # ── Departments ────────────────────────────
        depts_data = [
            ('Computer Science & Engineering', 'CSE'),
            ('Electronics & Electrical Engineering', 'EEE'),
            ('Mechanical Engineering', 'ME'),
            ('Civil Engineering', 'CE'),
            ('Information Science', 'IS'),
        ]
        depts = {}
        for name, code in depts_data:
            d = Department.query.filter_by(code=code).first()
            if not d:
                d = Department(name=name, code=code)
                db.session.add(d)
                db.session.flush()
                print(f'[+] Dept: {code}')
            depts[code] = d

        db.session.flush()

        # ── Subjects (CSE – Semesters 1-4) ────────
        cse_subjects = [
            # Sem 1
            ('Engineering Mathematics I', 'MA101', 1, 4),
            ('Engineering Physics', 'PH101', 1, 4),
            ('Programming in C', 'CS101', 1, 4),
            # Sem 2
            ('Engineering Mathematics II', 'MA201', 2, 4),
            ('Digital Electronics', 'CS201', 2, 4),
            ('Data Structures', 'CS202', 2, 4),
            # Sem 3
            ('Design & Analysis of Algorithms', 'CS301', 3, 4),
            ('Computer Organisation', 'CS302', 3, 4),
            ('Discrete Mathematics', 'MA301', 3, 4),
            # Sem 4
            ('Operating Systems', 'CS401', 4, 4),
            ('Database Management Systems', 'CS402', 4, 4),
            ('Computer Networks', 'CS403', 4, 4),
        ]
        for name, code, sem, credits in cse_subjects:
            if not Subject.query.filter_by(code=code).first():
                s = Subject(name=name, code=code,
                            department_id=depts['CSE'].id,
                            semester=sem, credits=credits)
                db.session.add(s)

        db.session.commit()
        print('[✓] Seed complete!')
        print('\nLogin credentials:')
        print('  Admin  → admin@abccollege.edu / admin1234')
        print('\nRegister students and teachers from /auth/register')


if __name__ == '__main__':
    seed_all()
