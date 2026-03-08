from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import TeacherProfile, User, Subject, SubjectAssignment, Department
from app.forms import TeacherRoleForm, SubjectAssignmentForm, SubjectForm
from app.decorators import hod_required

hod_bp = Blueprint('hod', __name__)


def get_hod_teacher():
    return TeacherProfile.query.filter_by(user_id=current_user.id).first_or_404()


# ─── DASHBOARD ────────────────────────────────
@hod_bp.route('/dashboard')
@login_required
@hod_required
def dashboard():
    hod = get_hod_teacher()
    dept = Department.query.get(hod.department_id)
    teacher_count = TeacherProfile.query.filter_by(department_id=hod.department_id).count()
    subject_count = Subject.query.filter_by(department_id=hod.department_id).count()
    return render_template('hod/dashboard.html', hod=hod, dept=dept,
                           teacher_count=teacher_count, subject_count=subject_count)


# ─── TEACHER ROSTER ───────────────────────────
@hod_bp.route('/teachers')
@login_required
@hod_required
def teachers():
    hod = get_hod_teacher()
    teacher_profiles = TeacherProfile.query.filter_by(department_id=hod.department_id).all()
    return render_template('hod/teachers.html', hod=hod, teacher_profiles=teacher_profiles)


@hod_bp.route('/teachers/<int:teacher_id>/edit', methods=['GET', 'POST'])
@login_required
@hod_required
def edit_teacher(teacher_id):
    hod = get_hod_teacher()
    tp = TeacherProfile.query.get_or_404(teacher_id)
    user = tp.user
    form = TeacherRoleForm()

    if form.validate_on_submit():
        user.role = form.role.data
        tp.designation = form.designation.data
        db.session.commit()
        flash(f'{user.name}\'s role updated to {form.role.data}.', 'success')
        return redirect(url_for('hod.teachers'))

    form.role.data = user.role
    form.designation.data = tp.designation
    return render_template('hod/edit_teacher.html', hod=hod, tp=tp, user=user, form=form)


# ─── SUBJECT ASSIGNMENTS ──────────────────────
@hod_bp.route('/subject-assignments', methods=['GET', 'POST'])
@login_required
@hod_required
def subject_assignments():
    hod = get_hod_teacher()
    form = SubjectAssignmentForm()

    teachers_in_dept = TeacherProfile.query.filter_by(department_id=hod.department_id).all()
    subjects_in_dept = Subject.query.filter_by(department_id=hod.department_id).all()

    form.teacher_id.choices = [(t.id, t.user.name) for t in teachers_in_dept]
    form.subject_id.choices = [(s.id, f'{s.code} – {s.name} (Sem {s.semester})') for s in subjects_in_dept]

    if form.validate_on_submit():
        existing = SubjectAssignment.query.filter_by(
            teacher_id=form.teacher_id.data,
            subject_id=form.subject_id.data).first()
        if existing:
            flash('This assignment already exists.', 'warning')
        else:
            sa = SubjectAssignment(
                teacher_id=form.teacher_id.data,
                subject_id=form.subject_id.data,
                academic_year=form.academic_year.data)
            db.session.add(sa)
            db.session.commit()
            flash('Subject assigned!', 'success')
        return redirect(url_for('hod.subject_assignments'))

    all_assignments = (SubjectAssignment.query
                       .join(Subject)
                       .filter(Subject.department_id == hod.department_id)
                       .all())
    return render_template('hod/subject_assignments.html', hod=hod, form=form,
                           all_assignments=all_assignments)


@hod_bp.route('/subject-assignments/<int:sa_id>/delete', methods=['POST'])
@login_required
@hod_required
def delete_subject_assignment(sa_id):
    sa = SubjectAssignment.query.get_or_404(sa_id)
    db.session.delete(sa)
    db.session.commit()
    flash('Assignment removed.', 'info')
    return redirect(url_for('hod.subject_assignments'))


# ─── SUBJECT MANAGEMENT (HOD) ─────────────────
@hod_bp.route('/subjects', methods=['GET', 'POST'])
@login_required
@hod_required
def subjects():
    hod = get_hod_teacher()
    form = SubjectForm()
    # Only show this dept in the dropdown, pre-selected
    form.department_id.choices = [(hod.department_id,
        Department.query.get(hod.department_id).name)]

    if form.validate_on_submit():
        # Check for duplicate code
        existing = Subject.query.filter_by(code=form.code.data.upper()).first()
        if existing:
            flash('A subject with this code already exists.', 'danger')
        else:
            db.session.add(Subject(
                name=form.name.data,
                code=form.code.data.upper(),
                department_id=hod.department_id,
                semester=form.semester.data,
                credits=form.credits.data))
            db.session.commit()
            flash('Subject added!', 'success')
        return redirect(url_for('hod.subjects'))

    all_subjects = Subject.query.filter_by(
        department_id=hod.department_id).order_by(
        Subject.semester, Subject.name).all()
    return render_template('hod/subjects.html', hod=hod, form=form,
                           subjects=all_subjects)


@hod_bp.route('/subjects/<int:subject_id>/edit', methods=['GET', 'POST'])
@login_required
@hod_required
def edit_subject(subject_id):
    hod = get_hod_teacher()
    subject = Subject.query.get_or_404(subject_id)
    if subject.department_id != hod.department_id:
        abort(403)
    form = SubjectForm()
    form.department_id.choices = [(hod.department_id,
        Department.query.get(hod.department_id).name)]
    if form.validate_on_submit():
        subject.name          = form.name.data
        subject.code          = form.code.data.upper()
        subject.semester      = form.semester.data
        subject.credits       = form.credits.data
        db.session.commit()
        flash('Subject updated!', 'success')
        return redirect(url_for('hod.subjects'))
    form.name.data          = subject.name
    form.code.data          = subject.code
    form.semester.data      = subject.semester
    form.credits.data       = subject.credits
    form.department_id.data = hod.department_id
    return render_template('hod/edit_subject.html', hod=hod, form=form, subject=subject)


@hod_bp.route('/subjects/<int:subject_id>/delete', methods=['POST'])
@login_required
@hod_required
def delete_subject(subject_id):
    hod = get_hod_teacher()
    subject = Subject.query.get_or_404(subject_id)
    if subject.department_id != hod.department_id:
        abort(403)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted.', 'warning')
    return redirect(url_for('hod.subjects'))
