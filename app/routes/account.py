from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from app.forms import AccountForm
from app.models import User

account = Blueprint('account', __name__)

@account.route('/account', methods=['GET', 'POST'])
@login_required
def account_page():
    form = AccountForm(obj=current_user)  # pre-fill from user
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data

        # Check if username or email already exists for another user
        existing_user = User.query.filter(
            (User.id != current_user.id) &
            (
                    (User.username == username) |
                    (User.email == email)
            )
        ).first()
        if existing_user:
            flash('Username or email already exists.', 'warning')
            return redirect(url_for('account.account_page'))

        # Update user information
        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.password.data:
            current_user.password = form.password.data

        db.session.commit()

        flash("Changes saved.", "success")
        return redirect(url_for('account.account_page'))

    return render_template('account.html', form=form, user=current_user)
