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
        # Update user information if the form is submitted valid, changes are made and no conflicts are found
        updated = False
        error = False
        if form.username.data != current_user.username:
            if User.query.filter_by(username=form.username.data).first():
                form.username.errors.append("Username is already taken.")
                error = True
            else:
                current_user.username = form.username.data
                updated = True

        if form.email.data != current_user.email:
            if User.query.filter_by(email=form.email.data).first():
                form.email.errors.append("Email is already registered.")
                error = True
            else:
                current_user.email = form.email.data
                updated = True

        if form.password.data and form.password.data != current_user.password:
            current_user.password = form.password.data
            updated = True

        if error:
            return render_template('account.html', form=form, user=current_user)

        if updated:
            db.session.commit()
            flash('Changes saved.', 'success')
        else:
            flash('No changes made.', 'info')

        return redirect(url_for('account.account_page'))

    return render_template('account.html', form=form, user=current_user)
