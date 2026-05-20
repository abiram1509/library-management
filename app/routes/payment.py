from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from app import db
from app.models import Subscription, Payment, Fine
from datetime import date, timedelta, datetime

payment = Blueprint('payment', __name__)

PLANS = {
    'silver':   {'price': 499,  'borrow_limit': 10, 'loan_duration': 15},
    'gold':     {'price': 999,  'borrow_limit': 14, 'loan_duration': 21},
    'platinum': {'price': 1800, 'borrow_limit': 20, 'loan_duration': 30},
}

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@payment.route('/subscription')
@login_required
def subscription():
    user_id = session['user_id']
    sub     = Subscription.query.filter_by(user_id=user_id, status='active').first()
    return render_template('user/subscription.html',
        plans   = PLANS,
        current = sub
    )


@payment.route('/subscribe/<string:plan>', methods=['POST'])
@login_required
def subscribe(plan):
    if plan not in PLANS:
        flash('Invalid plan.', 'error')
        return redirect(url_for('payment.subscription'))

    user_id = session['user_id']

    # cancel old subscription
    old_sub = Subscription.query.filter_by(user_id=user_id, status='active').first()
    if old_sub:
        old_sub.status = 'cancelled'

    # create new subscription
    new_sub = Subscription(
        user_id       = user_id,
        plan          = plan,
        price         = PLANS[plan]['price'],
        borrow_limit  = PLANS[plan]['borrow_limit'],
        loan_duration = PLANS[plan]['loan_duration'],
        start_date    = date.today(),
        end_date      = date.today() + timedelta(days=30),
        status        = 'active'
    )
    db.session.add(new_sub)

    # log payment
    p = Payment(
        user_id      = user_id,
        amount       = PLANS[plan]['price'],
        payment_type = 'subscription',
        status       = 'success'
    )
    db.session.add(p)
    db.session.commit()

    flash(f'🎉 {plan.capitalize()} plan activated successfully!', 'success')
    return redirect(url_for('payment.subscription'))


@payment.route('/pay-fine/<int:fine_id>', methods=['POST'])
@login_required
def pay_fine(fine_id):
    fine = Fine.query.filter_by(id=fine_id, user_id=session['user_id']).first_or_404()

    fine.status  = 'paid'
    fine.paid_at = datetime.utcnow()

    p = Payment(
        user_id      = session['user_id'],
        amount       = fine.amount,
        payment_type = 'fine',
        status       = 'success'
    )
    db.session.add(p)
    db.session.commit()

    flash(f'Fine of ₹{fine.amount} paid successfully!', 'success')
    return redirect(url_for('user.fines'))

@payment.route('/cancel-subscription', methods=['POST'])
@login_required
def cancel_subscription():
    user_id = session['user_id']
    sub     = Subscription.query.filter_by(user_id=user_id, status='active').first()
    if sub:
        sub.status = 'cancelled'
        db.session.commit()
        flash('Subscription cancelled.', 'success')
    return redirect(url_for('payment.subscription'))