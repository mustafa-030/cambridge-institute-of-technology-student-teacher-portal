from flask import Blueprint, render_template, redirect, url_for, flash, request, session, abort
from flask_login import login_required, current_user
from app import db
from app.models import User, Department, Subject, StudentProfile, TeacherProfile, Notice, Mark, Attendance
from app.forms import DepartmentForm, SubjectForm, NoticeForm
from app.decorators import admin_required

admin_bp = Blueprint('admin', __name__)

ADMIN_DEPT_KEY = 'admin_viewing_dept'  # session key for branch switcher


def get_viewing_dept():
    """Return the Department the admin is currently browsing (or None = all)."""
    dept_id = session.get(ADMIN_DEPT_KEY)
    if dept_id:
        return Department.query.get(dept_id)
    return None


# ─── BRANCH SWITCHER ──────────────────────────
@admin_bp.route('/switch-branch', methods=['POST'])
@login_required
@admin_required
def switch_branch():
    dept_id = request.form.get('dept_id', type=int)
    if dept_id:
        session[ADMIN_DEPT_KEY] = dept_id
    else:
        session.pop(ADMIN_DEPT_KEY, None)
    next_url = request.form.get('next') or url_for('admin.dashboard')
    return redirect(next_url)


# ─── DASHBOARD ────────────────────────────────
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    viewing_dept = get_viewing_dept()
    all_depts = Department.query.order_by(Department.name).all()

    if viewing_dept:
        user_count    = (StudentProfile.query.filter_by(department_id=viewing_dept.id).count() +
                         TeacherProfile.query.filter_by(department_id=viewing_dept.id).count())
        student_count = StudentProfile.query.filter_by(department_id=viewing_dept.id).count()
        teacher_count = TeacherProfile.query.filter_by(department_id=viewing_dept.id).count()
        subject_count = Subject.query.filter_by(department_id=viewing_dept.id).count()
    else:
        user_count    = User.query.count()
        student_count = StudentProfile.query.count()
        teacher_count = TeacherProfile.query.count()
        subject_count = Subject.query.count()

    dept_count = Department.query.count()
    return render_template('admin/dashboard.html',
                           user_count=user_count, student_count=student_count,
                           teacher_count=teacher_count, dept_count=dept_count,
                           subject_count=subject_count,
                           all_depts=all_depts, viewing_dept=viewing_dept)


# ─── USER MANAGEMENT ──────────────────────────
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    viewing_dept = get_viewing_dept()
    all_depts    = Department.query.order_by(Department.name).all()

    if viewing_dept:
        student_ids = [s.user_id for s in StudentProfile.query.filter_by(department_id=viewing_dept.id).all()]
        teacher_ids = [t.user_id for t in TeacherProfile.query.filter_by(department_id=viewing_dept.id).all()]
        all_users   = User.query.filter(User.id.in_(student_ids + teacher_ids)).order_by(User.name).all()
    else:
        all_users   = User.query.order_by(User.name).all()

    return render_template('admin/users.html', users=all_users,
                           all_depts=all_depts, viewing_dept=viewing_dept)


@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'User {"activated" if user.is_active else "deactivated"}.', 'info')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/role', methods=['POST'])
@login_required
@admin_required
def change_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role in ['student', 'teacher', 'hod', 'admin']:
        user.role = new_role
        db.session.commit()
        flash(f'Role updated for {user.name}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    all_depts = Department.query.order_by(Department.name).all()
    if request.method == 'POST':
        user.name = request.form.get('name', user.name).strip()
        new_role  = request.form.get('role')
        if new_role in ['student', 'teacher', 'hod', 'admin']:
            user.role = new_role
        dept_id = request.form.get('dept_id', type=int)
        if user.student_profile and dept_id:
            user.student_profile.department_id = dept_id
            sem = request.form.get('current_sem', type=int)
            if sem and 1 <= sem <= 8:
                user.student_profile.current_sem = sem
        elif user.teacher_profile and dept_id:
            user.teacher_profile.department_id  = dept_id
            user.teacher_profile.designation    = request.form.get('designation', '')
        db.session.commit()
        flash('User updated.', 'success')
        return redirect(url_for('admin.users'))
    return render_template('admin/edit_user.html', user=user, all_depts=all_depts)


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted.', 'warning')
    return redirect(url_for('admin.users'))


# ─── MARKS (admin browse by branch) ───────────
@admin_bp.route('/marks')
@admin_bp.route('/marks/<int:sem>')
@login_required
@admin_required
def marks(sem=1):
    viewing_dept = get_viewing_dept()
    all_depts    = Department.query.order_by(Department.name).all()

    if viewing_dept:
        subjects = Subject.query.filter_by(department_id=viewing_dept.id, semester=sem).all()
        students = StudentProfile.query.filter_by(department_id=viewing_dept.id, current_sem=sem).all()
        marks_data = Mark.query.join(StudentProfile, Mark.student_id == StudentProfile.id).filter(
            StudentProfile.department_id == viewing_dept.id,
            Mark.semester == sem).all()
    else:
        subjects   = Subject.query.filter_by(semester=sem).all()
        students   = StudentProfile.query.filter_by(current_sem=sem).all()
        marks_data = Mark.query.filter_by(semester=sem).all()

    return render_template('admin/marks.html',
                           subjects=subjects, students=students, marks_data=marks_data,
                           active_sem=sem, semesters=range(1, 9),
                           all_depts=all_depts, viewing_dept=viewing_dept)


# ─── DEPARTMENTS ──────────────────────────────
@admin_bp.route('/departments', methods=['GET', 'POST'])
@login_required
@admin_required
def departments():
    form = DepartmentForm()
    if form.validate_on_submit():
        db.session.add(Department(name=form.name.data, code=form.code.data.upper()))
        db.session.commit()
        flash('Department added!', 'success')
        return redirect(url_for('admin.departments'))
    depts = Department.query.order_by(Department.name).all()
    return render_template('admin/departments.html', form=form, departments=depts)


@admin_bp.route('/departments/<int:dept_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    form = DepartmentForm()
    if form.validate_on_submit():
        dept.name = form.name.data
        dept.code = form.code.data.upper()
        db.session.commit()
        flash('Department updated.', 'success')
        return redirect(url_for('admin.departments'))
    form.name.data = dept.name
    form.code.data = dept.code
    return render_template('admin/edit_department.html', form=form, dept=dept)


@admin_bp.route('/departments/<int:dept_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    db.session.delete(dept)
    db.session.commit()
    flash('Department deleted.', 'warning')
    return redirect(url_for('admin.departments'))


# ─── SUBJECTS ─────────────────────────────────
@admin_bp.route('/subjects', methods=['GET', 'POST'])
@login_required
@admin_required
def subjects():
    viewing_dept = get_viewing_dept()
    all_depts    = Department.query.order_by(Department.name).all()
    form = SubjectForm()
    form.department_id.choices = [(d.id, f'{d.code} – {d.name}') for d in all_depts]

    if form.validate_on_submit():
        db.session.add(Subject(
            name=form.name.data, code=form.code.data.upper(),
            department_id=form.department_id.data,
            semester=form.semester.data, credits=form.credits.data))
        db.session.commit()
        flash('Subject added!', 'success')
        return redirect(url_for('admin.subjects'))

    if viewing_dept:
        all_subjects = Subject.query.filter_by(department_id=viewing_dept.id).order_by(
            Subject.semester, Subject.name).all()
    else:
        all_subjects = Subject.query.order_by(Subject.semester, Subject.name).all()

    return render_template('admin/subjects.html', form=form, subjects=all_subjects,
                           all_depts=all_depts, viewing_dept=viewing_dept)


@admin_bp.route('/subjects/<int:subject_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    form = SubjectForm()
    depts = Department.query.order_by(Department.name).all()
    form.department_id.choices = [(d.id, f'{d.code} – {d.name}') for d in depts]
    if form.validate_on_submit():
        subject.name          = form.name.data
        subject.code          = form.code.data.upper()
        subject.department_id = form.department_id.data
        subject.semester      = form.semester.data
        subject.credits       = form.credits.data
        db.session.commit()
        flash('Subject updated.', 'success')
        return redirect(url_for('admin.subjects'))
    form.name.data          = subject.name
    form.code.data          = subject.code
    form.department_id.data = subject.department_id
    form.semester.data      = subject.semester
    form.credits.data       = subject.credits
    return render_template('admin/edit_subject.html', form=form, subject=subject)


@admin_bp.route('/subjects/<int:subject_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted.', 'warning')
    return redirect(url_for('admin.subjects'))


# ─── ADMIN NOTIFICATIONS ──────────────────────
@admin_bp.route('/notifications', methods=['GET', 'POST'])
@login_required
@admin_required
def notifications():
    form = NoticeForm()
    depts = Department.query.order_by(Department.name).all()
    form.department_ids.choices = [(d.id, f'{d.code} – {d.name}') for d in depts]

    if form.validate_on_submit():
        notice = Notice(
            title=form.title.data,
            content=form.content.data,
            author_id=current_user.id,
            target_role=form.target_role.data,
            is_pinned=form.is_pinned.data,
        )
        db.session.add(notice)
        db.session.flush()

        if form.dept_scope.data == 'specific' and form.department_ids.data:
            for dept_id in form.department_ids.data:
                dept = Department.query.get(dept_id)
                if dept:
                    notice.target_departments.append(dept)

        db.session.commit()
        flash('Notification sent!', 'success')
        return redirect(url_for('admin.notifications'))

    recent = Notice.query.filter_by(author_id=current_user.id).order_by(
        Notice.created_at.desc()).limit(10).all()
    return render_template('admin/notifications.html', form=form, depts=depts, recent=recent)
