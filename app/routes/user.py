from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from app.models import Loan, Reservation, Fine, Subscription
from datetime import date

user = Blueprint('user', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@user.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    
    from app.notifications import generate_due_alerts
    generate_due_alerts()

    active_loans       = Loan.query.filter_by(user_id=user_id, status='active').count()
    total_reservations = Reservation.query.filter_by(user_id=user_id, status='pending').count()
    recent_loans       = Loan.query.filter_by(user_id=user_id).order_by(Loan.checkout_date.desc()).limit(5).all()

    fines         = Fine.query.filter_by(user_id=user_id, status='pending').all()
    pending_fines = sum(f.amount for f in fines)

    overdue_loans  = Loan.query.filter_by(user_id=user_id, status='active').all()
    predicted_fine = 0
    overdue_count  = 0
    for loan in overdue_loans:
        if loan.due_date < date.today():
            days_late       = (date.today() - loan.due_date).days
            book_price      = loan.book.price
            daily_rate      = max(5, book_price * 0.01)
            predicted_fine += days_late * daily_rate
            overdue_count  += 1

    sub       = Subscription.query.filter_by(user_id=user_id, status='active').first()
    plan      = sub.plan.capitalize() if sub else 'Free'
    days_left = max(0, (sub.end_date - date.today()).days) if sub else 0

    return render_template('user/dashboard.html',
        active_loans       = active_loans,
        total_reservations = total_reservations,
        pending_fines      = round(pending_fines, 2),
        recent_loans       = recent_loans,
        predicted_fine     = round(predicted_fine, 2),
        overdue_loans      = overdue_count,
        plan               = plan,
        days_left          = days_left
    )


@user.route('/browse')
@login_required
def browse():
    from app.models import Book, Genre

    search   = request.args.get('search', '')
    genre_id = request.args.get('genre', '')
    genres   = Genre.query.all()

    query = Book.query
    if search:
        query = query.filter(Book.title.ilike(f'%{search}%') | Book.author.ilike(f'%{search}%'))
    if genre_id:
        query = query.filter_by(genre_id=genre_id)

    books = query.all()
    return render_template('user/browse.html', books=books, genres=genres, search=search)


@user.route('/borrow/<int:book_id>', methods=['POST'])
@login_required
def borrow_book(book_id):
    from app.models import Book, Loan, Subscription
    from app import db
    from datetime import timedelta

    user_id = session['user_id']
    book    = Book.query.get_or_404(book_id)
    sub     = Subscription.query.filter_by(user_id=user_id, status='active').first()

    if sub:
        borrow_limit  = sub.borrow_limit
        loan_duration = sub.loan_duration
    else:
        borrow_limit  = 2
        loan_duration = 7

    active_count = Loan.query.filter_by(user_id=user_id, status='active').count()
    if active_count >= borrow_limit:
        flash(f'Borrow limit reached ({borrow_limit} books). Upgrade your subscription for more.', 'error')
        return redirect(url_for('user.browse'))

    if book.available_copies < 1:
        flash('No copies available. You can reserve this book.', 'error')
        return redirect(url_for('user.browse'))

    from datetime import timedelta
    due_date = date.today() + timedelta(days=loan_duration)
    loan = Loan(
        user_id       = user_id,
        book_id       = book_id,
        checkout_date = date.today(),
        due_date      = due_date
    )
    book.available_copies -= 1
    db.session.add(loan)
    db.session.commit()

    flash(f'Successfully borrowed "{book.title}". Due: {due_date.strftime("%b %d, %Y")}', 'success')
    return redirect(url_for('user.loans'))


@user.route('/loans')
@login_required
def loans():
    from app import db

    user_id = session['user_id']
    status  = request.args.get('status', 'all')

    query = Loan.query.filter_by(user_id=user_id)
    if status != 'all':
        query = query.filter_by(status=status)

    loans = query.order_by(Loan.checkout_date.desc()).all()

    for loan in loans:
        if loan.status == 'active' and loan.due_date < date.today():
            loan.status = 'overdue'
    db.session.commit()

    return render_template('user/loans.html', loans=loans, status=status, today=date.today())


@user.route('/renew/<int:loan_id>', methods=['POST'])
@login_required
def renew_loan(loan_id):
    from app.models import Loan, Subscription
    from app import db
    from datetime import timedelta

    user_id = session['user_id']
    loan    = Loan.query.filter_by(id=loan_id, user_id=user_id).first_or_404()
    sub     = Subscription.query.filter_by(user_id=user_id, status='active').first()

    if loan.renewals_used >= loan.max_renewals:
        flash('Maximum renewals reached.', 'error')
    else:
        duration           = sub.loan_duration if sub else 7
        loan.due_date      = loan.due_date + timedelta(days=duration)
        loan.renewals_used += 1
        loan.status = 'active'
        db.session.commit()
        flash('Loan renewed successfully.', 'success')

    return redirect(url_for('user.loans'))


@user.route('/reservations')
@login_required
def reservations():
    user_id = session['user_id']
    status  = request.args.get('status', 'all')

    query = Reservation.query.filter_by(user_id=user_id)
    if status != 'all':
        query = query.filter_by(status=status)

    reservations = query.order_by(Reservation.reserved_at.desc()).all()
    total        = Reservation.query.filter_by(user_id=user_id).count()
    active       = Reservation.query.filter_by(user_id=user_id, status='pending').count()
    ready        = Reservation.query.filter_by(user_id=user_id, status='available').count()

    return render_template('user/reservations.html',
        reservations = reservations,
        status       = status,
        total        = total,
        active       = active,
        ready        = ready
    )


@user.route('/reserve/<int:book_id>', methods=['POST'])
@login_required
def reserve_book(book_id):
    from app.models import Reservation, Book
    from app import db

    user_id = session['user_id']
    book    = Book.query.get_or_404(book_id)

    existing = Reservation.query.filter_by(
        user_id=user_id, book_id=book_id, status='pending'
    ).first()

    if existing:
        flash('You already have a reservation for this book.', 'error')
        return redirect(url_for('user.browse'))

    reservation = Reservation(user_id=user_id, book_id=book_id)
    db.session.add(reservation)
    db.session.commit()

    flash(f'Reserved "{book.title}". We will notify you when available.', 'success')
    return redirect(url_for('user.reservations'))


@user.route('/cancel-reservation/<int:res_id>', methods=['POST'])
@login_required
def cancel_reservation(res_id):
    from app.models import Reservation
    from app import db

    user_id     = session['user_id']
    reservation = Reservation.query.filter_by(id=res_id, user_id=user_id).first_or_404()
    reservation.status = 'cancelled'
    db.session.commit()

    flash('Reservation cancelled.', 'success')
    return redirect(url_for('user.reservations'))


@user.route('/fines')
@login_required
def fines():
    user_id = session['user_id']
    status  = request.args.get('status', 'all')

    query = Fine.query.filter_by(user_id=user_id)
    if status != 'all':
        query = query.filter_by(status=status)

    fines         = query.order_by(Fine.created_at.desc()).all()
    total_pending = sum(f.amount for f in Fine.query.filter_by(user_id=user_id, status='pending').all())
    total_paid    = sum(f.amount for f in Fine.query.filter_by(user_id=user_id, status='paid').all())

    return render_template('user/fines.html',
        fines         = fines,
        status        = status,
        total_pending = round(total_pending, 2),
        total_paid    = round(total_paid, 2)
    )


@user.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from app.models import User
    from app import db
    import bcrypt

    user_id = session['user_id']
    user    = User.query.get(user_id)

    if request.method == 'POST':
        user.name = request.form['name']
        new_pass  = request.form.get('new_password')
        if new_pass:
            user.password_hash = bcrypt.hashpw(
                new_pass.encode('utf-8'), bcrypt.gensalt()
            ).decode('utf-8')
        db.session.commit()
        session['name'] = user.name
        flash('Profile updated successfully.', 'success')

    return render_template('user/profile.html', user=user)


@user.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    from app.models import UserSettings
    from app import db

    user_id  = session['user_id']
    settings = UserSettings.query.filter_by(user_id=user_id).first()

    if request.method == 'POST':
        settings.email_notifications = 'email_notifications' in request.form
        settings.push_notifications  = 'push_notifications'  in request.form
        settings.book_reminders      = 'book_reminders'       in request.form
        settings.due_date_alerts     = 'due_date_alerts'      in request.form
        settings.new_arrivals        = 'new_arrivals'         in request.form
        settings.recommendations     = 'recommendations'      in request.form
        settings.marketing_emails    = 'marketing_emails'     in request.form
        db.session.commit()
        flash('Settings saved.', 'success')

    return render_template('user/settings.html', settings=settings)


@user.route('/notifications')
@login_required
def notifications():
    from app.models import Notification
    from app import db

    user_id = session['user_id']
    notifs  = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()

    for n in notifs:
        n.is_read = True
    db.session.commit()

    return render_template('user/notifications.html', notifs=notifs)