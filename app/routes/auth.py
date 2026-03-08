from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, StudentProfile, TeacherProfile, Department
from app.forms import LoginForm, RegisterForm

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(request.args.get('next') or url_for('auth.dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    form = RegisterForm()
    departments = Department.query.order_by(Department.name).all()
    form.department_id.choices = [(0, '— Select your Department —')] + [(d.id, f'{d.code} – {d.name}') for d in departments]

    if form.validate_on_submit():
        dept_id = form.department_id.data
        if not dept_id:
            flash('Please select a department.', 'danger')
            return render_template('auth/register.html', form=form)

        existing = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if existing:
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html', form=form)

        user = User(
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        if form.role.data == 'student':
            usn = form.usn.data.strip().upper() if form.usn.data else f'USN{user.id:04d}'
            profile = StudentProfile(user_id=user.id, usn=usn, department_id=dept_id)
            db.session.add(profile)
        else:
            emp_id = form.employee_id.data.strip() if form.employee_id.data else f'EMP{user.id:04d}'
            profile = TeacherProfile(user_id=user.id, employee_id=emp_id, department_id=dept_id)
            db.session.add(profile)

        db.session.commit()
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard')
@login_required
def dashboard():
    role = current_user.role
    if role == 'student':
        return redirect(url_for('student.dashboard'))
    elif role in ('teacher', 'hod'):
        return redirect(url_for('teacher.dashboard'))
    elif role == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('auth.login'))
