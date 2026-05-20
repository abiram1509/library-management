from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app import db
from app.models import *
from datetime import date

admin = Blueprint('admin', __name__)

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@admin.route('/dashboard')
@admin_required
def dashboard():
    total_books        = Book.query.count()
    active_loans       = Loan.query.filter_by(status='active').count()
    overdue_loans      = Loan.query.filter_by(status='overdue').count()
    total_users        = User.query.filter_by(role='user').count()
    active_subs        = Subscription.query.filter_by(status='active').count()
    pending_reservations = Reservation.query.filter_by(status='pending').count()
    pending_fines      = sum(f.amount for f in Fine.query.filter_by(status='pending').all())
    revenue            = sum(p.amount for p in Payment.query.filter_by(status='success').all())
    recent_activity    = Loan.query.order_by(Loan.checkout_date.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
        total_books          = total_books,
        active_loans         = active_loans,
        overdue_loans        = overdue_loans,
        total_users          = total_users,
        active_subs          = active_subs,
        pending_reservations = pending_reservations,
        pending_fines        = round(pending_fines, 2),
        revenue              = round(revenue, 2),
        recent_activity      = recent_activity
    )


@admin.route('/books', methods=['GET', 'POST'])
@admin_required
def books():
    if request.method == 'POST':
        book = Book(
            title            = request.form['title'],
            author           = request.form['author'],
            isbn             = request.form['isbn'],
            genre_id         = request.form['genre_id'],
            price            = float(request.form['price']),
            total_copies     = int(request.form['total_copies']),
            available_copies = int(request.form['total_copies'])
        )
        db.session.add(book)
        db.session.commit()
        flash('Book added successfully.', 'success')
        return redirect(url_for('admin.books'))

    books  = Book.query.all()
    genres = Genre.query.all()
    return render_template('admin/books.html', books=books, genres=genres)

@admin.route('/books/delete/<int:book_id>', methods=['POST'])
@admin_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    if book.loans:
        flash('Cannot delete book with existing loans.', 'error')
        return redirect(url_for('admin.books'))
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted.', 'success')
    return redirect(url_for('admin.books'))

@admin.route('/loans')
@admin_required
def loans():
    status = request.args.get('status', 'all')
    query  = Loan.query
    if status != 'all':
        query = query.filter_by(status=status)
    loans = query.order_by(Loan.checkout_date.desc()).all()
    return render_template('admin/loans.html', loans=loans, status=status, today=date.today())


@admin.route('/loans/mark/<int:loan_id>/<string:new_status>', methods=['POST'])
@admin_required
def mark_loan(loan_id, new_status):
    loan = Loan.query.get_or_404(loan_id)
    loan.status = new_status

    if new_status == 'returned':
        loan.return_date             = date.today()
        loan.book.available_copies  += 1
        # check reservations for this book
        reservation = Reservation.query.filter_by(
            book_id=loan.book_id, status='pending'
        ).order_by(Reservation.reserved_at).first()
        if reservation:
            reservation.status       = 'available'
            reservation.available_at = db.func.now()
            from app.notifications import notify_reservation_available
            notify_reservation_available(reservation)

    elif new_status in ['lost', 'damaged']:
        fine_type  = new_status
        book_price = loan.book.price
        amount     = book_price if new_status == 'lost' else book_price * 0.4
        if new_status == 'lost':
            amount += 100
        fine = Fine(
            loan_id   = loan.id,
            user_id   = loan.user_id,
            fine_type = fine_type,
            amount    = round(amount, 2)
        )
        db.session.add(fine)
        from app.notifications import notify_fine_added
        notify_fine_added(fine)

    db.session.commit()
    flash(f'Loan marked as {new_status}.', 'success')
    return redirect(url_for('admin.loans'))


@admin.route('/fines')
@admin_required
def fines():
    status = request.args.get('status', 'all')
    query  = Fine.query
    if status != 'all':
        query = query.filter_by(status=status)
    fines = query.order_by(Fine.created_at.desc()).all()
    total_pending = sum(f.amount for f in Fine.query.filter_by(status='pending').all())
    return render_template('admin/fines.html', fines=fines, status=status, total_pending=round(total_pending,2))


@admin.route('/reservations')
@admin_required
def reservations():
    status = request.args.get('status', 'all')
    query  = Reservation.query
    if status != 'all':
        query = query.filter_by(status=status)
    reservations = query.order_by(Reservation.reserved_at.desc()).all()
    return render_template('admin/reservations.html', reservations=reservations, status=status)


@admin.route('/users')
@admin_required
def users():
    users = User.query.filter_by(role='user').all()
    return render_template('admin/users.html', users=users)


@admin.route('/fines/mark-paid/<int:fine_id>', methods=['POST'])
@admin_required
def mark_fine_paid(fine_id):
    from datetime import datetime
    fine        = Fine.query.get_or_404(fine_id)
    fine.status = 'paid'
    fine.paid_at = datetime.utcnow()
    db.session.commit()
    flash('Fine marked as paid.', 'success')
    return redirect(url_for('admin.fines'))