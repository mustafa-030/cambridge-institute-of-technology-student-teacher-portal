from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


ROLE_STUDENT = 'student'
ROLE_TEACHER = 'teacher'
ROLE_HOD     = 'hod'
ROLE_ADMIN   = 'admin'

SEMESTERS = [1, 2, 3, 4, 5, 6, 7, 8]


# ─────────────────────────────────────────────
# USER
# ─────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20), nullable=False, default=ROLE_STUDENT)
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    teacher_profile = db.relationship('TeacherProfile', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_student(self):   return self.role == ROLE_STUDENT
    def is_teacher(self):   return self.role in [ROLE_TEACHER, ROLE_HOD]
    def is_hod(self):       return self.role == ROLE_HOD
    def is_admin(self):     return self.role == ROLE_ADMIN

    def get_department_id(self):
        if self.student_profile:
            return self.student_profile.department_id
        if self.teacher_profile:
            return self.teacher_profile.department_id
        return None

    def __repr__(self):
        return f'<User {self.email} [{self.role}]>'


# ─────────────────────────────────────────────
# DEPARTMENT
# ─────────────────────────────────────────────
class Department(db.Model):
    __tablename__ = 'departments'

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)

    students = db.relationship('StudentProfile', backref='department', lazy='dynamic')
    teachers = db.relationship('TeacherProfile', backref='department', lazy='dynamic')
    subjects = db.relationship('Subject', backref='department', lazy='dynamic')

    def __repr__(self):
        return f'<Department {self.code}>'


# ─────────────────────────────────────────────
# STUDENT PROFILE
# ─────────────────────────────────────────────
class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    usn           = db.Column(db.String(20), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    current_sem   = db.Column(db.Integer, default=1)
    batch_year    = db.Column(db.Integer)
    phone         = db.Column(db.String(15))
    address       = db.Column(db.Text)
    dob           = db.Column(db.Date)
    gender        = db.Column(db.String(10))
    photo_url     = db.Column(db.String(255))

    attendances          = db.relationship('Attendance',         backref='student', lazy='dynamic')
    marks                = db.relationship('Mark',               backref='student', lazy='dynamic')
    course_registrations = db.relationship('CourseRegistration', backref='student', lazy='dynamic')
    exam_registrations   = db.relationship('ExamRegistration',   backref='student', lazy='dynamic')
    fee_payments         = db.relationship('FeePayment',         backref='student', lazy='dynamic')
    projects             = db.relationship('ProjectInternship',  backref='student', lazy='dynamic')


# ─────────────────────────────────────────────
# TEACHER PROFILE
# ─────────────────────────────────────────────
class TeacherProfile(db.Model):
    __tablename__ = 'teacher_profiles'

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    employee_id    = db.Column(db.String(20), unique=True, nullable=False)
    department_id  = db.Column(db.Integer, db.ForeignKey('departments.id'))
    designation    = db.Column(db.String(100))
    phone          = db.Column(db.String(15))
    specialization = db.Column(db.String(200))

    subject_assignments = db.relationship('SubjectAssignment', backref='teacher', lazy='dynamic')


# ─────────────────────────────────────────────
# SUBJECT
# ─────────────────────────────────────────────
class Subject(db.Model):
    __tablename__ = 'subjects'

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(150), nullable=False)
    code          = db.Column(db.String(20), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))
    semester      = db.Column(db.Integer, nullable=False)
    credits       = db.Column(db.Integer, default=4)

    subject_assignments = db.relationship('SubjectAssignment', backref='subject', lazy='dynamic')
    marks               = db.relationship('Mark',              backref='subject', lazy='dynamic')
    attendances         = db.relationship('Attendance',        backref='subject', lazy='dynamic')


# ─────────────────────────────────────────────
# SUBJECT ASSIGNMENT (teacher ↔ subject)
# ─────────────────────────────────────────────
class SubjectAssignment(db.Model):
    __tablename__ = 'subject_assignments'

    id            = db.Column(db.Integer, primary_key=True)
    teacher_id    = db.Column(db.Integer, db.ForeignKey('teacher_profiles.id'), nullable=False)
    subject_id    = db.Column(db.Integer, db.ForeignKey('subjects.id'),         nullable=False)
    academic_year = db.Column(db.String(20))


# ─────────────────────────────────────────────
# ATTENDANCE
# ─────────────────────────────────────────────
class Attendance(db.Model):
    __tablename__ = 'attendance'

    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'),         nullable=False)
    date       = db.Column(db.Date,    nullable=False)
    status     = db.Column(db.String(10), nullable=False)
    semester   = db.Column(db.Integer)
    marked_by  = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
# MARKS
# ─────────────────────────────────────────────
class Mark(db.Model):
    __tablename__ = 'marks'

    id             = db.Column(db.Integer, primary_key=True)
    student_id     = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    subject_id     = db.Column(db.Integer, db.ForeignKey('subjects.id'),         nullable=False)
    semester       = db.Column(db.Integer, nullable=False)
    exam_type      = db.Column(db.String(30))
    marks_obtained = db.Column(db.Float)
    max_marks      = db.Column(db.Float)
    updated_by     = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ─────────────────────────────────────────────
# COURSE REGISTRATION
# ─────────────────────────────────────────────
class CourseRegistration(db.Model):
    __tablename__ = 'course_registrations'

    id            = db.Column(db.Integer, primary_key=True)
    student_id    = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    subject_id    = db.Column(db.Integer, db.ForeignKey('subjects.id'),         nullable=False)
    semester      = db.Column(db.Integer, nullable=False)
    academic_year = db.Column(db.String(20))
    status        = db.Column(db.String(20), default='registered')
    registered_at = db.Column(db.DateTime,  default=datetime.utcnow)
    subject       = db.relationship("Subject", backref="course_registrations")


# ─────────────────────────────────────────────
# EXAM REGISTRATION
# ─────────────────────────────────────────────
class ExamRegistration(db.Model):
    __tablename__ = 'exam_registrations'

    id             = db.Column(db.Integer, primary_key=True)
    student_id     = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    subject_id     = db.Column(db.Integer, db.ForeignKey('subjects.id'),         nullable=False)
    semester       = db.Column(db.Integer, nullable=False)
    academic_year  = db.Column(db.String(20))
    exam_date      = db.Column(db.Date)
    hall_ticket_no = db.Column(db.String(30))
    status         = db.Column(db.String(20), default='pending')
    registered_at  = db.Column(db.DateTime,  default=datetime.utcnow)
    subject        = db.relationship("Subject", backref="exam_registrations")


# ─────────────────────────────────────────────
# FEE PAYMENT
# ─────────────────────────────────────────────
class FeePayment(db.Model):
    __tablename__ = 'fee_payments'

    id             = db.Column(db.Integer, primary_key=True)
    student_id     = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    amount         = db.Column(db.Float,   nullable=False)
    fee_type       = db.Column(db.String(50))
    semester       = db.Column(db.Integer)
    academic_year  = db.Column(db.String(20))
    payment_date   = db.Column(db.DateTime, default=datetime.utcnow)
    transaction_id = db.Column(db.String(100))
    status         = db.Column(db.String(20), default='pending')


# ─────────────────────────────────────────────
# PROJECT / INTERNSHIP
# ─────────────────────────────────────────────
class ProjectInternship(db.Model):
    __tablename__ = 'projects_internships'

    id              = db.Column(db.Integer, primary_key=True)
    student_id      = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    title           = db.Column(db.String(200), nullable=False)
    type            = db.Column(db.String(20))
    description     = db.Column(db.Text)
    company_org     = db.Column(db.String(150))
    start_date      = db.Column(db.Date)
    end_date        = db.Column(db.Date)
    status          = db.Column(db.String(30), default='ongoing')
    certificate_url = db.Column(db.String(255))
    submitted_at    = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────
# NOTICE  — multi-dept targeting
# ─────────────────────────────────────────────
notice_departments = db.Table(
    'notice_departments',
    db.Column('notice_id', db.Integer, db.ForeignKey('notices.id'),     primary_key=True),
    db.Column('dept_id',   db.Integer, db.ForeignKey('departments.id'), primary_key=True),
)


class Notice(db.Model):
    __tablename__ = 'notices'

    id            = db.Column(db.Integer, primary_key=True)
    title         = db.Column(db.String(200), nullable=False)
    content       = db.Column(db.Text,        nullable=False)
    author_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_role   = db.Column(db.String(20),  default='all')   # all | student | teacher
    is_pinned     = db.Column(db.Boolean,     default=False)
    created_at    = db.Column(db.DateTime,    default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime,    default=datetime.utcnow, onupdate=datetime.utcnow)

    author             = db.relationship('User',       backref='notices',  foreign_keys=[author_id])
    target_departments = db.relationship('Department', secondary=notice_departments,
                                         backref='notices', lazy='dynamic')

    def is_visible_to(self, user):
        """True if this notice should be shown to user."""
        if user.role == 'admin':
            return True
        # role check (hod counts as teacher)
        if self.target_role != 'all':
            effective = 'teacher' if user.role == 'hod' else user.role
            if self.target_role != effective:
                return False
        # dept check: if notice has specific depts, user must belong to one
        dept_ids = {d.id for d in self.target_departments}
        if dept_ids:
            user_dept = user.get_department_id()
            if user_dept not in dept_ids:
                return False
        return True


# ─────────────────────────────────────────────
# ASSIGNMENT
# ─────────────────────────────────────────────
class Assignment(db.Model):
    __tablename__ = 'assignments'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    subject_id  = db.Column(db.Integer, db.ForeignKey('subjects.id'),  nullable=False)
    posted_by   = db.Column(db.Integer, db.ForeignKey('users.id'),     nullable=False)
    due_date    = db.Column(db.DateTime)
    semester    = db.Column(db.Integer)
    attachment  = db.Column(db.String(255))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    subject     = db.relationship('Subject', backref='course_assignments')
    teacher     = db.relationship('User',    backref='posted_assignments', foreign_keys=[posted_by])
    submissions = db.relationship('AssignmentSubmission', backref='assignment', lazy='dynamic')


# ─────────────────────────────────────────────
# ASSIGNMENT SUBMISSION
# ─────────────────────────────────────────────
class AssignmentSubmission(db.Model):
    __tablename__ = 'assignment_submissions'

    id            = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignments.id'),      nullable=False)
    student_id    = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    submitted_at  = db.Column(db.DateTime, default=datetime.utcnow)
    content       = db.Column(db.Text)
    file_url      = db.Column(db.String(255))
    original_name = db.Column(db.String(255))
    grade         = db.Column(db.String(5))
    feedback      = db.Column(db.Text)

    student = db.relationship('StudentProfile', backref='submissions')
