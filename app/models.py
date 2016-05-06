from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.orm import backref
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class Base(db.Model):

    __abstract__  = True

    id         = db.Column(db.Integer, primary_key=True)
    create_at  = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                                           onupdate=db.func.current_timestamp())

class User(db.Model):
    """An admin user capable of viewing reports.
    :param str email: email address of user
    :param str password: encrypted password for the user
    """
    __tablename__ = 'user'

    email = db.Column(db.String(60), primary_key=True)
    password = db.Column(db.String)
    authenticated = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    first_name = db.Column(db.String(40))
    last_name = db.Column(db.String(40))
    contact_no = db.Column(db.String(10))

    create_at  = db.Column(db.DateTime,  default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime,  default=db.func.current_timestamp(),
                                           onupdate=db.func.current_timestamp())

    balance = db.relationship("Balance", uselist=False, backref="user")
    attendence = db.relationship("Attendence", uselist=True, backref="user")

    def is_active(self):
        """True, as all users are active."""
        return True

    def get_id(self):
        """Return the email address to satify Flask-Login's requirements."""
        return self.email

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

    def debit_balance(self, debit_amount):
        self.balance.amount -= debit_amount

    def credit_balance(self, credit_amount):
        self.balance.amount += credit_amount

    def get_balance(self):
        return self.balance.amount

class Balance(Base):
    amount = db.Column(db.Float)
    email = db.Column(db.String, db.ForeignKey('user.email'))

    __tablename__ = 'balance'

    def __repr__(self):
        return '<Available Balance : %r>' % self.amount

class Transaction(Base):
    txn_id = db.Column(db.String(10)) #str(uuid.uuid4())[:8]
    party = db.Column(db.String(40))
    counter_party = db.Column(db.String(40))
    amount = db.Column(db.Float)
    type = db.Column(db.String(2))
    reason = db.Column(db.String(20))

    __tablename__ = 'transaction'

    def __repr__(self):
        return '<Transaction %r>' % self.txn_id

class PlayScheduledDates(Base):
    play_date = db.Column(db.Date, unique=True)
    is_active = db.Column(db.Boolean, default=True)
    is_charged = db.Column(db.Boolean, default=True)

    __tablename__ = 'play_scheduled_dates'

    attendees = db.relationship("Attendence", uselist=True, backref="dates")

    def __repr__(self):
        return '<Play Date %r>' % self.play_date

class Attendence(Base):
    play_date = db.Column(db.Date, db.ForeignKey('play_scheduled_dates.play_date'))
    attendee_email = db.Column(db.String(60), db.ForeignKey('user.email'))
    status = db.Column(db.String(3))

    __tablename__ = 'attendence'

    def __repr__(self):
        return '<User : %r Attending %r>' % (self.attendee_email, self.play_date)
