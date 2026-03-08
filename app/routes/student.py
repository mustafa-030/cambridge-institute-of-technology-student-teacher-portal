from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import (StudentProfile, Subject, CourseRegistration, ExamRegistration,
                        FeePayment, Mark, Attendance, ProjectInternship, Assignment,
                        AssignmentSubmission, Notice)
from app.forms import ProjectForm, FeePaymentForm, AssignmentSubmissionForm, StudentProfileForm
from app.decorators import student_required

student_bp = Blueprint('student', __name__)


def get_student():
    return StudentProfile.query.filter_by(user_id=current_user.id).first_or_404()


def dept_notices(student):
    """Return notices visible to this student (dept-scoped)."""
    all_notices = Notice.query.order_by(Notice.is_pinned.desc(), Notice.created_at.desc()).all()
    return [n for n in all_notices if n.is_visible_to(current_user)]


# ─── DASHBOARD ────────────────────────────────
@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    student = get_student()
    notices = dept_notices(student)[:5]
    # only assignments for this student's dept subjects
    dept_subject_ids = [s.id for s in Subject.query.filter_by(
        department_id=student.department_id, semester=student.current_sem).all()]
    assignments = Assignment.query.filter(
        Assignment.subject_id.in_(dept_subject_ids),
        Assignment.semester == student.current_sem
    ).order_by(Assignment.due_date.asc()).limit(5).all()
    return render_template('student/dashboard.html', student=student,
                           notices=notices, assignments=assignments)


# ─── PROFILE EDIT ─────────────────────────────
@student_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@student_required
def edit_profile():
    student = get_student()
    form = StudentProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        student.phone     = form.phone.data
        student.address   = form.address.data
        student.dob       = form.dob.data
        student.gender    = form.gender.data
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('student.dashboard'))
    # pre-fill
    form.name.data    = current_user.name
    form.phone.data   = student.phone
    form.address.data = student.address
    form.dob.data     = student.dob
    form.gender.data  = student.gender
    return render_template('student/edit_profile.html', form=form, student=student)


# ─── MARKS (dept-scoped, read-only) ───────────
@student_bp.route('/marks')
@student_bp.route('/marks/<int:sem>')
@login_required
@student_required
def marks(sem=None):
    student = get_student()
    sem = sem or student.current_sem
    # Only marks for subjects in their own dept
    dept_subject_ids = [s.id for s in Subject.query.filter_by(
        department_id=student.department_id, semester=sem).all()]
    marks_data = Mark.query.filter(
        Mark.student_id == student.id,
        Mark.semester   == sem,
        Mark.subject_id.in_(dept_subject_ids)
    ).all()
    return render_template('student/marks.html', student=student,
                           marks=marks_data, active_sem=sem, semesters=range(1, 9))


# ─── ATTENDANCE (dept-scoped, read-only) ──────
@student_bp.route('/attendance')
@student_bp.route('/attendance/<int:sem>')
@login_required
@student_required
def attendance(sem=None):
    student = get_student()
    sem = sem or student.current_sem
    dept_subject_ids = {s.id for s in Subject.query.filter_by(
        department_id=student.department_id, semester=sem).all()}
    records = Attendance.query.filter(
        Attendance.student_id == student.id,
        Attendance.semester   == sem,
        Attendance.subject_id.in_(dept_subject_ids)
    ).all()
    summary = {}
    for r in records:
        sid = r.subject_id
        if sid not in summary:
            summary[sid] = {'subject': r.subject, 'present': 0, 'absent': 0, 'late': 0}
        summary[sid][r.status] = summary[sid].get(r.status, 0) + 1
    return render_template('student/attendance.html', student=student,
                           summary=summary.values(), active_sem=sem, semesters=range(1, 9))


# ─── COURSE REGISTRATION ──────────────────────
@student_bp.route('/course-registration', methods=['GET', 'POST'])
@login_required
@student_required
def course_registration():
    student = get_student()
    sem = student.current_sem
    # Subjects limited to student's own dept
    subjects = Subject.query.filter_by(semester=sem, department_id=student.department_id).all()
    registered_ids = {cr.subject_id for cr in
                      CourseRegistration.query.filter_by(student_id=student.id, semester=sem).all()}
    if request.method == 'POST':
        subject_id = request.form.get('subject_id', type=int)
        action     = request.form.get('action')
        # validate subject belongs to student's dept
        subj = Subject.query.get(subject_id)
        if not subj or subj.department_id != student.department_id:
            abort(403)
        if action == 'register' and subject_id not in registered_ids:
            db.session.add(CourseRegistration(
                student_id=student.id, subject_id=subject_id,
                semester=sem, academic_year='2025-2026'))
            db.session.commit()
            flash('Course registered!', 'success')
        elif action == 'drop' and subject_id in registered_ids:
            reg = CourseRegistration.query.filter_by(
                student_id=student.id, subject_id=subject_id, semester=sem).first()
            if reg:
                db.session.delete(reg)
                db.session.commit()
                flash('Course dropped.', 'info')
        return redirect(url_for('student.course_registration'))
    return render_template('student/course_registration.html', student=student,
                           subjects=subjects, registered_ids=registered_ids, sem=sem)


# ─── EXAM REGISTRATION ────────────────────────
@student_bp.route('/exam-registration', methods=['GET', 'POST'])
@login_required
@student_required
def exam_registration():
    student = get_student()
    sem = student.current_sem
    registered_subjects = CourseRegistration.query.filter_by(
        student_id=student.id, semester=sem).all()
    exam_registered_ids = {er.subject_id for er in
                           ExamRegistration.query.filter_by(student_id=student.id, semester=sem).all()}
    if request.method == 'POST':
        subject_id = request.form.get('subject_id', type=int)
        subj = Subject.query.get(subject_id)
        if not subj or subj.department_id != student.department_id:
            abort(403)
        if subject_id and subject_id not in exam_registered_ids:
            db.session.add(ExamRegistration(
                student_id=student.id, subject_id=subject_id,
                semester=sem, academic_year='2025-2026'))
            db.session.commit()
            flash('Exam registration submitted!', 'success')
        return redirect(url_for('student.exam_registration'))
    return render_template('student/exam_registration.html', student=student,
                           registered_subjects=registered_subjects,
                           exam_registered_ids=exam_registered_ids)


# ─── FEE PAYMENT ──────────────────────────────
@student_bp.route('/fee-payment', methods=['GET', 'POST'])
@login_required
@student_required
def fee_payment():
    student = get_student()
    form = FeePaymentForm()
    payments = FeePayment.query.filter_by(student_id=student.id).order_by(
        FeePayment.payment_date.desc()).all()
    if form.validate_on_submit():
        db.session.add(FeePayment(
            student_id=student.id, amount=form.amount.data,
            fee_type=form.fee_type.data, semester=form.semester.data,
            academic_year=form.academic_year.data,
            transaction_id=form.transaction_id.data, status='paid'))
        db.session.commit()
        flash('Payment recorded!', 'success')
        return redirect(url_for('student.fee_payment'))
    return render_template('student/fee_payment.html', student=student,
                           form=form, payments=payments)


# ─── PROJECTS / INTERNSHIPS ───────────────────
@student_bp.route('/projects', methods=['GET', 'POST'])
@login_required
@student_required
def projects():
    student = get_student()
    form = ProjectForm()
    items = ProjectInternship.query.filter_by(student_id=student.id).order_by(
        ProjectInternship.submitted_at.desc()).all()
    if form.validate_on_submit():
        db.session.add(ProjectInternship(
            student_id=student.id, title=form.title.data,
            type=form.type.data, description=form.description.data,
            company_org=form.company_org.data, start_date=form.start_date.data,
            end_date=form.end_date.data, status=form.status.data))
        db.session.commit()
        flash('Entry added!', 'success')
        return redirect(url_for('student.projects'))
    return render_template('student/projects.html', student=student, form=form, items=items)


@student_bp.route('/projects/<int:proj_id>/edit', methods=['GET', 'POST'])
@login_required
@student_required
def edit_project(proj_id):
    student = get_student()
    proj = ProjectInternship.query.get_or_404(proj_id)
    if proj.student_id != student.id:
        abort(403)
    form = ProjectForm()
    if form.validate_on_submit():
        proj.title       = form.title.data
        proj.type        = form.type.data
        proj.description = form.description.data
        proj.company_org = form.company_org.data
        proj.start_date  = form.start_date.data
        proj.end_date    = form.end_date.data
        proj.status      = form.status.data
        db.session.commit()
        flash('Entry updated!', 'success')
        return redirect(url_for('student.projects'))
    form.title.data       = proj.title
    form.type.data        = proj.type
    form.description.data = proj.description
    form.company_org.data = proj.company_org
    form.start_date.data  = proj.start_date
    form.end_date.data    = proj.end_date
    form.status.data      = proj.status
    return render_template('student/edit_project.html', form=form, proj=proj)


@student_bp.route('/projects/<int:proj_id>/delete', methods=['POST'])
@login_required
@student_required
def delete_project(proj_id):
    student = get_student()
    proj = ProjectInternship.query.get_or_404(proj_id)
    if proj.student_id != student.id:
        abort(403)
    db.session.delete(proj)
    db.session.commit()
    flash('Entry deleted.', 'info')
    return redirect(url_for('student.projects'))


# ─── ASSIGNMENTS (dept-scoped) ────────────────
@student_bp.route('/assignments')
@login_required
@student_required
def assignments():
    student = get_student()
    sem = student.current_sem
    dept_subject_ids = [s.id for s in Subject.query.filter_by(
        department_id=student.department_id, semester=sem).all()]
    assignments_list = Assignment.query.filter(
        Assignment.subject_id.in_(dept_subject_ids),
        Assignment.semester == sem
    ).order_by(Assignment.due_date.asc()).all()
    submitted_ids = {s.assignment_id for s in
                     AssignmentSubmission.query.filter_by(student_id=student.id).all()}
    return render_template('student/assignments.html', student=student,
                           assignments=assignments_list, submitted_ids=submitted_ids)


@student_bp.route('/assignments/<int:assignment_id>/submit', methods=['GET', 'POST'])
@login_required
@student_required
def submit_assignment(assignment_id):
    student = get_student()
    assignment = Assignment.query.get_or_404(assignment_id)
    # Ensure this assignment is for student's dept
    if assignment.subject.department_id != student.department_id:
        abort(403)
    form = AssignmentSubmissionForm()
    existing = AssignmentSubmission.query.filter_by(
        assignment_id=assignment_id, student_id=student.id).first()
    if form.validate_on_submit():
        link = form.file_link.data.strip() if form.file_link.data else None
        if existing:
            existing.content      = form.content.data
            existing.submitted_at = db.func.now()
            if link:
                existing.file_url = link
        else:
            db.session.add(AssignmentSubmission(
                assignment_id=assignment_id,
                student_id=student.id,
                content=form.content.data,
                file_url=link))
        db.session.commit()
        flash('Assignment submitted!', 'success')
        return redirect(url_for('student.assignments'))
    if existing:
        form.content.data = existing.content
    return render_template('student/submit_assignment.html',
                           form=form, assignment=assignment, existing=existing)
