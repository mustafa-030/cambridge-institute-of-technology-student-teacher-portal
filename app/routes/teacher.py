from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import (TeacherProfile, StudentProfile, Subject, SubjectAssignment,
                        Mark, Attendance, Assignment, AssignmentSubmission)
from app.forms import AssignmentForm
from app.decorators import teacher_required
from datetime import date

teacher_bp = Blueprint('teacher', __name__)


def get_teacher():
    return TeacherProfile.query.filter_by(user_id=current_user.id).first_or_404()


def dept_subjects(teacher, sem=None):
    """Subjects assigned to this teacher, optionally filtered by semester."""
    q = (Subject.query
         .join(SubjectAssignment)
         .filter(SubjectAssignment.teacher_id == teacher.id))
    if sem:
        q = q.filter(Subject.semester == sem)
    return q.all()


def dept_students(department_id, sem):
    """All students in a department + semester."""
    return StudentProfile.query.filter_by(
        department_id=department_id, current_sem=sem).all()


# ─── DASHBOARD ────────────────────────────────
@teacher_bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    teacher = get_teacher()
    subjects = dept_subjects(teacher)
    return render_template('teacher/dashboard.html', teacher=teacher, subjects=subjects)


# ─── MARKS ────────────────────────────────────
@teacher_bp.route('/marks')
@teacher_bp.route('/marks/<int:sem>')
@login_required
@teacher_required
def marks(sem=1):
    teacher = get_teacher()
    subjects = dept_subjects(teacher, sem)
    return render_template('teacher/marks.html', teacher=teacher,
                           subjects=subjects, active_sem=sem, semesters=range(1, 9))


@teacher_bp.route('/marks/<int:sem>/subject/<int:subject_id>', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_marks(sem, subject_id):
    teacher = get_teacher()
    subject = Subject.query.get_or_404(subject_id)
    # Ensure teacher is assigned to this subject
    if not SubjectAssignment.query.filter_by(teacher_id=teacher.id, subject_id=subject_id).first():
        abort(403)
    students = dept_students(subject.department_id, sem)

    if request.method == 'POST':
        exam_type = request.form.get('exam_type')
        max_marks = float(request.form.get('max_marks', 100))
        for s in students:
            val = request.form.get(f'marks_{s.id}', '').strip()
            if val:
                mark = Mark.query.filter_by(
                    student_id=s.id, subject_id=subject_id,
                    semester=sem, exam_type=exam_type).first()
                if mark:
                    mark.marks_obtained = float(val)
                    mark.max_marks      = max_marks
                    mark.updated_by     = current_user.id
                else:
                    db.session.add(Mark(
                        student_id=s.id, subject_id=subject_id,
                        semester=sem, exam_type=exam_type,
                        marks_obtained=float(val), max_marks=max_marks,
                        updated_by=current_user.id))
        db.session.commit()
        flash('Marks saved!', 'success')
        return redirect(url_for('teacher.edit_marks', sem=sem, subject_id=subject_id))

    all_marks = Mark.query.filter_by(subject_id=subject_id, semester=sem).all()
    existing_marks = {}
    existing_marks_json = {}
    for m in all_marks:
        existing_marks[(m.student_id, m.exam_type)] = m.marks_obtained
        existing_marks_json[f'{m.student_id}_{m.exam_type}'] = m.marks_obtained

    return render_template('teacher/edit_marks.html',
                           teacher=teacher, subject=subject, students=students,
                           sem=sem, existing_marks=existing_marks, all_marks=all_marks,
                           existing_marks_json=existing_marks_json,
                           exam_types=['internal1', 'internal2', 'final'])


# ─── DELETE SINGLE MARK ───────────────────────
@teacher_bp.route('/marks/delete/<int:mark_id>', methods=['POST'])
@login_required
@teacher_required
def delete_mark(mark_id):
    teacher = get_teacher()
    mark = Mark.query.get_or_404(mark_id)
    # check subject is assigned to teacher
    if not SubjectAssignment.query.filter_by(teacher_id=teacher.id, subject_id=mark.subject_id).first():
        abort(403)
    sem = mark.semester
    sid = mark.subject_id
    db.session.delete(mark)
    db.session.commit()
    flash('Mark entry deleted.', 'info')
    return redirect(url_for('teacher.edit_marks', sem=sem, subject_id=sid))


# ─── ATTENDANCE ───────────────────────────────
@teacher_bp.route('/attendance')
@teacher_bp.route('/attendance/<int:sem>')
@login_required
@teacher_required
def attendance(sem=1):
    teacher = get_teacher()
    subjects = dept_subjects(teacher, sem)
    return render_template('teacher/attendance.html', teacher=teacher,
                           subjects=subjects, active_sem=sem, semesters=range(1, 9))


@teacher_bp.route('/attendance/<int:sem>/subject/<int:subject_id>', methods=['GET', 'POST'])
@login_required
@teacher_required
def mark_attendance(sem, subject_id):
    teacher = get_teacher()
    subject = Subject.query.get_or_404(subject_id)
    if not SubjectAssignment.query.filter_by(teacher_id=teacher.id, subject_id=subject_id).first():
        abort(403)
    students = dept_students(subject.department_id, sem)

    # For GET: preload existing attendance for selected date
    selected_date = request.args.get('date') or str(date.today())

    if request.method == 'POST':
        att_date = request.form.get('date') or str(date.today())
        for s in students:
            status = request.form.get(f'status_{s.id}', 'absent')
            existing = Attendance.query.filter_by(
                student_id=s.id, subject_id=subject_id, date=att_date).first()
            if existing:
                existing.status    = status
                existing.marked_by = current_user.id
            else:
                db.session.add(Attendance(
                    student_id=s.id, subject_id=subject_id,
                    date=att_date, status=status, semester=sem,
                    marked_by=current_user.id))
        db.session.commit()
        flash('Attendance saved!', 'success')
        return redirect(url_for('teacher.attendance', sem=sem))

    # Load existing statuses for the selected_date
    existing_att = {a.student_id: a.status for a in
                    Attendance.query.filter_by(subject_id=subject_id, date=selected_date).all()}

    return render_template('teacher/mark_attendance.html',
                           teacher=teacher, subject=subject, students=students,
                           sem=sem, today=str(date.today()),
                           selected_date=selected_date, existing_att=existing_att)


# ─── ASSIGNMENTS ──────────────────────────────
@teacher_bp.route('/assignments', methods=['GET', 'POST'])
@login_required
@teacher_required
def assignments():
    teacher = get_teacher()
    form = AssignmentForm()
    assigned_subjects = SubjectAssignment.query.filter_by(teacher_id=teacher.id).all()
    form.subject_id.choices = [(a.subject_id, f'{a.subject.code} – {a.subject.name}')
                                for a in assigned_subjects]
    if form.validate_on_submit():
        db.session.add(Assignment(
            title=form.title.data, description=form.description.data,
            subject_id=form.subject_id.data, posted_by=current_user.id,
            semester=form.semester.data, due_date=form.due_date.data,
            attachment=form.attachment.data.strip() if form.attachment.data else None))
        db.session.commit()
        flash('Assignment posted!', 'success')
        return redirect(url_for('teacher.assignments'))
    my_assignments = Assignment.query.filter_by(posted_by=current_user.id).order_by(
        Assignment.created_at.desc()).all()
    return render_template('teacher/assignments.html', teacher=teacher,
                           form=form, assignments=my_assignments)


@teacher_bp.route('/assignments/<int:assignment_id>/edit', methods=['GET', 'POST'])
@login_required
@teacher_required
def edit_assignment(assignment_id):
    teacher = get_teacher()
    a = Assignment.query.get_or_404(assignment_id)
    if a.posted_by != current_user.id:
        abort(403)
    form = AssignmentForm()
    assigned_subjects = SubjectAssignment.query.filter_by(teacher_id=teacher.id).all()
    form.subject_id.choices = [(s.subject_id, f'{s.subject.code} – {s.subject.name}')
                                for s in assigned_subjects]
    if form.validate_on_submit():
        a.title       = form.title.data
        a.description = form.description.data
        a.subject_id  = form.subject_id.data
        a.semester    = form.semester.data
        a.due_date    = form.due_date.data
        db.session.commit()
        flash('Assignment updated!', 'success')
        return redirect(url_for('teacher.assignments'))
    form.title.data       = a.title
    form.description.data = a.description
    form.subject_id.data  = a.subject_id
    form.semester.data    = a.semester
    form.due_date.data    = a.due_date.date() if a.due_date else None
    return render_template('teacher/edit_assignment.html', form=form, assignment=a)


@teacher_bp.route('/assignments/<int:assignment_id>/delete', methods=['POST'])
@login_required
@teacher_required
def delete_assignment(assignment_id):
    a = Assignment.query.get_or_404(assignment_id)
    if a.posted_by != current_user.id:
        abort(403)
    db.session.delete(a)
    db.session.commit()
    flash('Assignment deleted.', 'info')
    return redirect(url_for('teacher.assignments'))


@teacher_bp.route('/assignments/<int:assignment_id>/submissions')
@login_required
@teacher_required
def view_submissions(assignment_id):
    teacher = get_teacher()
    assignment = Assignment.query.get_or_404(assignment_id)
    if assignment.posted_by != current_user.id:
        abort(403)
    submissions = AssignmentSubmission.query.filter_by(assignment_id=assignment_id).all()
    return render_template('teacher/submissions.html', teacher=teacher,
                           assignment=assignment, submissions=submissions)


@teacher_bp.route('/assignments/<int:assignment_id>/grade/<int:sub_id>', methods=['POST'])
@login_required
@teacher_required
def grade_submission(assignment_id, sub_id):
    sub = AssignmentSubmission.query.get_or_404(sub_id)
    sub.grade    = request.form.get('grade')
    sub.feedback = request.form.get('feedback')
    db.session.commit()
    flash('Grade saved!', 'success')
    return redirect(url_for('teacher.view_submissions', assignment_id=assignment_id))
