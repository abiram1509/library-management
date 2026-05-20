from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Genre(db.Model):
    __tablename__ = 'genres'
    id      = db.Column(db.Integer, primary_key=True)
    name    = db.Column(db.String(100), unique=True, nullable=False)
    books   = db.relationship('Book', backref='genre', lazy=True)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(100), nullable=False)
    email           = db.Column(db.String(100), unique=True, nullable=False)
    password_hash   = db.Column(db.String(255), nullable=False)
    role            = db.Column(db.Enum('user','admin'), default='user')
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    loans           = db.relationship('Loan', backref='user', lazy=True)
    reservations    = db.relationship('Reservation', backref='user', lazy=True)
    fines           = db.relationship('Fine', backref='user', lazy=True)
    subscription    = db.relationship('Subscription', backref='user', uselist=False)
    settings        = db.relationship('UserSettings', backref='user', uselist=False)
    notifications   = db.relationship('Notification', backref='user', lazy=True)
    payments        = db.relationship('Payment', backref='user', lazy=True)

class Book(db.Model):
    __tablename__ = 'books'
    id               = db.Column(db.Integer, primary_key=True)
    title            = db.Column(db.String(200), nullable=False)
    author           = db.Column(db.String(100), nullable=False)
    isbn             = db.Column(db.String(20), unique=True, nullable=False)
    genre_id         = db.Column(db.Integer, db.ForeignKey('genres.id'))
    price            = db.Column(db.Float, nullable=False)
    total_copies     = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    added_at         = db.Column(db.DateTime, default=datetime.utcnow)
    loans            = db.relationship('Loan', backref='book', lazy=True)
    reservations     = db.relationship('Reservation', backref='book', lazy=True)

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'))
    plan            = db.Column(db.Enum('silver','gold','platinum'))
    price           = db.Column(db.Float)
    borrow_limit    = db.Column(db.Integer)
    loan_duration   = db.Column(db.Integer)
    start_date      = db.Column(db.Date)
    end_date        = db.Column(db.Date)
    status          = db.Column(db.Enum('active','expired','cancelled'), default='active')

class Loan(db.Model):
    __tablename__ = 'loans'
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'))
    book_id         = db.Column(db.Integer, db.ForeignKey('books.id'))
    checkout_date   = db.Column(db.Date, default=datetime.utcnow)
    due_date        = db.Column(db.Date, nullable=False)
    return_date     = db.Column(db.Date, nullable=True)
    renewals_used   = db.Column(db.Integer, default=0)
    max_renewals    = db.Column(db.Integer, default=2)
    status          = db.Column(db.Enum('active','returned','overdue','lost','damaged'), default='active')
    assigned_by     = db.Column(db.Enum('user','admin'), default='user')
    fines           = db.relationship('Fine', backref='loan', lazy=True)

class Fine(db.Model):
    __tablename__ = 'fines'
    id          = db.Column(db.Integer, primary_key=True)
    loan_id     = db.Column(db.Integer, db.ForeignKey('loans.id'))
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'))
    fine_type   = db.Column(db.Enum('late','damaged','lost'))
    amount      = db.Column(db.Float)
    status      = db.Column(db.Enum('pending','paid'), default='pending')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at     = db.Column(db.DateTime, nullable=True)

class Reservation(db.Model):
    __tablename__ = 'reservations'
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'))
    book_id         = db.Column(db.Integer, db.ForeignKey('books.id'))
    reserved_at     = db.Column(db.DateTime, default=datetime.utcnow)
    available_at    = db.Column(db.DateTime, nullable=True)
    fulfilled_at    = db.Column(db.DateTime, nullable=True)
    status          = db.Column(db.Enum('pending','available','fulfilled','cancelled'), default='pending')

class Payment(db.Model):
    __tablename__ = 'payments'
    id                  = db.Column(db.Integer, primary_key=True)
    user_id             = db.Column(db.Integer, db.ForeignKey('users.id'))
    amount              = db.Column(db.Float)
    payment_type        = db.Column(db.Enum('subscription','fine'))
    razorpay_order_id   = db.Column(db.String(100))
    razorpay_payment_id = db.Column(db.String(100))
    status              = db.Column(db.Enum('pending','success','failed'), default='pending')
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'))
    message     = db.Column(db.Text)
    type        = db.Column(db.Enum('due_alert','fine_warning','reservation','new_arrival'))
    is_read     = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

class UserSettings(db.Model):
    __tablename__ = 'user_settings'
    id                  = db.Column(db.Integer, primary_key=True)
    user_id             = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True)
    email_notifications = db.Column(db.Boolean, default=True)
    push_notifications  = db.Column(db.Boolean, default=True)
    book_reminders      = db.Column(db.Boolean, default=True)
    due_date_alerts     = db.Column(db.Boolean, default=True)
    new_arrivals        = db.Column(db.Boolean, default=False)
    recommendations     = db.Column(db.Boolean, default=False)
    marketing_emails    = db.Column(db.Boolean, default=False)