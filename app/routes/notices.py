from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Notice, Department
from app.forms import NoticeForm

notices_bp = Blueprint('notices', __name__)


def _build_form_choices(form):
    depts = Department.query.order_by(Department.name).all()
    form.department_ids.choices = [(d.id, f'{d.code} – {d.name}') for d in depts]
    return depts


@notices_bp.route('/')
@login_required
def index():
    all_notices = Notice.query.order_by(Notice.is_pinned.desc(), Notice.created_at.desc()).all()
    notices = [n for n in all_notices if n.is_visible_to(current_user)]
    return render_template('shared/notices.html', notices=notices)


@notices_bp.route('/post', methods=['GET', 'POST'])
@login_required
def post_notice():
    if current_user.role == 'student':
        flash('Students cannot post notices.', 'danger')
        return redirect(url_for('notices.index'))

    form = NoticeForm()
    depts = _build_form_choices(form)

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

        # attach specific departments if requested
        if form.dept_scope.data == 'specific' and form.department_ids.data:
            for dept_id in form.department_ids.data:
                dept = Department.query.get(dept_id)
                if dept:
                    notice.target_departments.append(dept)

        db.session.commit()
        flash('Notice posted!', 'success')
        return redirect(url_for('notices.index'))

    return render_template('shared/post_notice.html', form=form, depts=depts)


@notices_bp.route('/<int:notice_id>')
@login_required
def view_notice(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    if not notice.is_visible_to(current_user):
        abort(403)
    return render_template('shared/notice_detail.html', notice=notice)


@notices_bp.route('/<int:notice_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_notice(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    if notice.author_id != current_user.id and current_user.role != 'admin':
        abort(403)
    form = NoticeForm()
    depts = _build_form_choices(form)

    if form.validate_on_submit():
        notice.title       = form.title.data
        notice.content     = form.content.data
        notice.target_role = form.target_role.data
        notice.is_pinned   = form.is_pinned.data
        # reset dept targets
        for d in list(notice.target_departments):
            notice.target_departments.remove(d)
        if form.dept_scope.data == 'specific' and form.department_ids.data:
            for dept_id in form.department_ids.data:
                dept = Department.query.get(dept_id)
                if dept:
                    notice.target_departments.append(dept)
        db.session.commit()
        flash('Notice updated!', 'success')
        return redirect(url_for('notices.view_notice', notice_id=notice.id))

    # pre-fill
    form.title.data       = notice.title
    form.content.data     = notice.content
    form.target_role.data = notice.target_role
    form.is_pinned.data   = notice.is_pinned
    current_dept_ids = [d.id for d in notice.target_departments]
    form.department_ids.data = current_dept_ids
    form.dept_scope.data = 'specific' if current_dept_ids else 'all'

    return render_template('shared/edit_notice.html', form=form, notice=notice, depts=depts)


@notices_bp.route('/<int:notice_id>/delete', methods=['POST'])
@login_required
def delete_notice(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    if notice.author_id != current_user.id and current_user.role != 'admin':
        abort(403)
    db.session.delete(notice)
    db.session.commit()
    flash('Notice deleted.', 'info')
    return redirect(url_for('notices.index'))
