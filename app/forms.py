from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SelectField, SelectMultipleField,
                     TextAreaField, IntegerField, FloatField, DateField,
                     BooleanField, SubmitField)
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange
from wtforms.widgets import ListWidget, CheckboxInput


class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


# ─── AUTH ─────────────────────────────────────
class LoginForm(FlaskForm):
    email    = StringField('Email',    validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit   = SubmitField('Login')


class RegisterForm(FlaskForm):
    name          = StringField('Full Name',  validators=[DataRequired(), Length(3, 120)])
    email         = StringField('Email',      validators=[DataRequired(), Email()])
    password      = PasswordField('Password', validators=[DataRequired(), Length(6, 50)])
    confirm       = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role          = SelectField('I am a', choices=[('student', 'Student'), ('teacher', 'Teacher')],
                                validators=[DataRequired()])
    department_id = SelectField('Department', coerce=int, validators=[Optional()])
    # Student-only
    usn           = StringField('USN',         validators=[Optional(), Length(max=20)])
    # Teacher-only
    employee_id   = StringField('Employee ID', validators=[Optional(), Length(max=20)])
    submit        = SubmitField('Create Account')


# ─── STUDENT PROFILE EDIT ──────────────────────
class StudentProfileForm(FlaskForm):
    name      = StringField('Full Name',  validators=[DataRequired(), Length(3, 120)])
    phone     = StringField('Phone',      validators=[Optional(), Length(max=15)])
    address   = TextAreaField('Address',  validators=[Optional()])
    dob       = DateField('Date of Birth',validators=[Optional()])
    gender    = SelectField('Gender', choices=[('', '— Select —'),
                                               ('male', 'Male'),
                                               ('female', 'Female'),
                                               ('other', 'Other')],
                            validators=[Optional()])
    submit    = SubmitField('Save Changes')


# ─── MARKS ────────────────────────────────────
class MarkForm(FlaskForm):
    student_id     = IntegerField('Student ID', validators=[DataRequired()])
    subject_id     = SelectField('Subject', coerce=int, validators=[DataRequired()])
    semester       = SelectField('Semester', coerce=int,
                                 choices=[(i, f'Sem {i}') for i in range(1, 9)],
                                 validators=[DataRequired()])
    exam_type      = SelectField('Exam Type',
                                 choices=[('internal1', 'Internal 1'),
                                          ('internal2', 'Internal 2'),
                                          ('final',     'Final')],
                                 validators=[DataRequired()])
    marks_obtained = FloatField('Marks Obtained', validators=[DataRequired(), NumberRange(0, 100)])
    max_marks      = FloatField('Max Marks',       validators=[DataRequired(), NumberRange(1, 100)])
    submit         = SubmitField('Save Marks')


# ─── ATTENDANCE ───────────────────────────────
class AttendanceForm(FlaskForm):
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    semester   = SelectField('Semester', coerce=int,
                             choices=[(i, f'Sem {i}') for i in range(1, 9)])
    date       = DateField('Date', validators=[DataRequired()])
    submit     = SubmitField('Mark Attendance')


# ─── NOTICE (admin-level, multi-dept) ─────────
class NoticeForm(FlaskForm):
    title         = StringField('Title', validators=[DataRequired(), Length(3, 200)])
    content       = TextAreaField('Content', validators=[DataRequired()])
    target_role   = SelectField('Send To',
                                choices=[('all',     'Everyone'),
                                         ('student', 'Students Only'),
                                         ('teacher', 'Teachers Only')])
    # JS will show/hide this based on whether specific depts are chosen
    dept_scope    = SelectField('Department Scope',
                                choices=[('all',      'All Departments'),
                                         ('specific', 'Specific Department(s)')],
                                validators=[Optional()])
    # populated dynamically in the route
    department_ids = MultiCheckboxField('Select Departments', coerce=int, validators=[Optional()])
    is_pinned      = BooleanField('📌 Pin this notice')
    submit         = SubmitField('Post Notice')


# ─── ASSIGNMENT ───────────────────────────────
class AssignmentForm(FlaskForm):
    title       = StringField('Title',       validators=[DataRequired(), Length(3, 200)])
    description = TextAreaField('Description', validators=[Optional()])
    subject_id  = SelectField('Subject',     coerce=int, validators=[DataRequired()])
    semester    = SelectField('Semester',    coerce=int,
                              choices=[(i, f'Sem {i}') for i in range(1, 9)])
    due_date    = DateField('Due Date',      validators=[Optional()])
    attachment  = StringField('Google Drive Link (optional)', validators=[Optional(), Length(max=500)])
    submit      = SubmitField('Post Assignment')


class AssignmentSubmissionForm(FlaskForm):
    content    = TextAreaField('Your Answer / Notes', validators=[Optional()])
    file_link  = StringField('Google Drive Link (optional)', validators=[Optional(), Length(max=500)])
    submit  = SubmitField('Submit Assignment')


# ─── PROJECT / INTERNSHIP ─────────────────────
class ProjectForm(FlaskForm):
    title       = StringField('Title',       validators=[DataRequired(), Length(3, 200)])
    type        = SelectField('Type',        choices=[('project', 'Project'), ('internship', 'Internship')])
    description = TextAreaField('Description', validators=[Optional()])
    company_org = StringField('Company / Organisation', validators=[Optional(), Length(max=150)])
    start_date  = DateField('Start Date',    validators=[Optional()])
    end_date    = DateField('End Date',      validators=[Optional()])
    status      = SelectField('Status',      choices=[('ongoing', 'Ongoing'), ('completed', 'Completed')])
    submit      = SubmitField('Save')


# ─── FEE PAYMENT ──────────────────────────────
class FeePaymentForm(FlaskForm):
    amount         = FloatField('Amount (₹)',   validators=[DataRequired()])
    fee_type       = SelectField('Fee Type',
                                 choices=[('tuition', 'Tuition Fee'),
                                          ('exam',    'Exam Fee'),
                                          ('hostel',  'Hostel Fee'),
                                          ('other',   'Other')])
    semester       = SelectField('Semester',    coerce=int,
                                 choices=[(i, f'Sem {i}') for i in range(1, 9)])
    academic_year  = StringField('Academic Year', validators=[DataRequired()])
    transaction_id = StringField('Transaction / UTR No.', validators=[DataRequired()])
    submit         = SubmitField('Submit Payment')


# ─── HOD – Teacher Management ─────────────────
class TeacherRoleForm(FlaskForm):
    role        = SelectField('Role', choices=[('teacher', 'Teacher'), ('hod', 'HOD')])
    designation = StringField('Designation', validators=[Optional(), Length(max=100)])
    submit      = SubmitField('Update')


class SubjectAssignmentForm(FlaskForm):
    teacher_id    = SelectField('Teacher',      coerce=int, validators=[DataRequired()])
    subject_id    = SelectField('Subject',      coerce=int, validators=[DataRequired()])
    academic_year = StringField('Academic Year', validators=[DataRequired()])
    submit        = SubmitField('Assign')


# ─── ADMIN – Department / Subject ─────────────
class DepartmentForm(FlaskForm):
    name   = StringField('Department Name', validators=[DataRequired(), Length(3, 100)])
    code   = StringField('Code',            validators=[DataRequired(), Length(2, 20)])
    submit = SubmitField('Save')


class SubjectForm(FlaskForm):
    name          = StringField('Subject Name', validators=[DataRequired(), Length(3, 150)])
    code          = StringField('Code',         validators=[DataRequired(), Length(2, 20)])
    department_id = SelectField('Department',   coerce=int, validators=[DataRequired()])
    semester      = SelectField('Semester',     coerce=int,
                                choices=[(i, f'Sem {i}') for i in range(1, 9)])
    credits       = IntegerField('Credits',     validators=[NumberRange(1, 10)], default=4)
    submit        = SubmitField('Save')
