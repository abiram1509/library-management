from app import db
from app.models import Loan, Notification
from datetime import date, timedelta

def generate_due_alerts():
    """Run this daily — checks loans due in 3 days and creates alerts"""
    soon = date.today() + timedelta(days=3)
    
    loans = Loan.query.filter(
        Loan.status == 'active',
        Loan.due_date <= soon,
        Loan.due_date >= date.today()
    ).all()

    for loan in loans:
        existing = Notification.query.filter_by(
            user_id = loan.user_id,
            type    = 'due_alert'
        ).filter(
            Notification.created_at >= date.today()
        ).first()

        if not existing:
            days_left = (loan.due_date - date.today()).days
            msg = f'"{loan.book.title}" is due in {days_left} day(s) on {loan.due_date.strftime("%b %d, %Y")}.'
            n = Notification(
                user_id = loan.user_id,
                message = msg,
                type    = 'due_alert'
            )
            db.session.add(n)

    db.session.commit()


def notify_reservation_available(reservation):
    msg = f'"{reservation.book.title}" is now available for pickup! Please collect it soon.'
    n = Notification(
        user_id = reservation.user_id,
        message = msg,
        type    = 'reservation'
    )
    db.session.add(n)
    # no commit here — admin.py commits


def notify_fine_added(fine):
    msg = f'A {fine.fine_type} fine of ₹{fine.amount} has been added to your account.'
    n = Notification(
        user_id = fine.user_id,
        message = msg,
        type    = 'fine_warning'
    )
    db.session.add(n)
    # no commit here — admin.py commits