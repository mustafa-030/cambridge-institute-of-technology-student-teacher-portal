from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user


def role_required(*roles):
    """Decorator: restrict view to users with one of the given roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('auth.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def student_required(f):
    return role_required('student')(f)


def teacher_required(f):
    """Allows both teacher and hod."""
    return role_required('teacher', 'hod')(f)


def hod_required(f):
    return role_required('hod')(f)


def admin_required(f):
    return role_required('admin')(f)
