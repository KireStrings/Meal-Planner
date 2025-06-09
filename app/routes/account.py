from flask import Blueprint, render_template
from flask_login import current_user

account = Blueprint('account', __name__)

@account.route('/account')
@login_required
def account_page():
    return render_template('account.html', user=current_user)