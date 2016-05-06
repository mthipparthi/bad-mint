from flask import Flask
from flask import render_template
from flask import redirect
from flask import url_for
from flask import request
from flask import flash
from flask_sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.login import login_required 
from flask.ext.login import login_user
from flask.ext.login import logout_user
from flask.ext.login import current_user
from flask.ext.bcrypt import Bcrypt

from models import db
from models import User
from models import Balance
from models import Transaction
from models import PlayScheduledDates
from models import Attendence

from forms import LoginForm
from forms import SignupForm
from forms import BalanceForm
from forms import PayForm
from forms import ChangePasswordForm
from forms import ForgotPasswordForm
from forms import PlayDatesForm
from forms import AttendenceForm
from forms import ChargePlayersForm

from flask_mail import Mail
from flask_mail import Message
from flask_bootstrap import Bootstrap
import logging
import sys

import os
import uuid

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# tmpl_dir = os.path.join(BASE_DIR, 'templates')

webapp = Flask(__name__)

webapp.logger.addHandler(logging.StreamHandler(sys.stdout))
webapp.logger.setLevel(logging.ERROR)

webapp.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'db/app.db')
# webapp.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:////tmp/flask_app.db')
webapp.config['SECRET_KEY'] = 'foo'
webapp.config['WTF_CSRF_KEY'] = 'foo'

webapp.config['MAIL_SERVER'] = 'smtp.gmail.com'
webapp.config['MAIL_PORT'] = 465
webapp.config['MAIL_USE_TLS'] = False
webapp.config['MAIL_USE_SSL'] = True
webapp.config['MAIL_USERNAME'] = 'mahesh.thipparthi@gmail.com'
webapp.config['MAIL_PASSWORD'] = 'XXXXXX'
webapp.config['DEFAULT_MAIL_SENDER'] = 'mahesh.thipparthi@gmail.com'

db.init_app(webapp)

login_manager = LoginManager()
login_manager.init_app(webapp)

bcrypt = Bcrypt()

mail = Mail()
mail.init_app(webapp)

bootstrap = Bootstrap()
bootstrap.init_app(webapp)

import datetime
from dateutil import parser

from rq import Queue
from rq.job import Job
from worker import conn

q = Queue(connection=conn)

import tasks
import collections

@login_manager.user_loader
def user_loader(user_id):
    """Given *user_id*, return the associated User object.
    :param unicode user_id: user_id (email) user to retrieve
    """
    return User.query.get(user_id)

@webapp.route("/charge_players", methods=["GET", "POST"])
@login_required
def charge_players():
    """For GET requests, display the login form. For POSTS, login the current user
    by processing the form."""

    form = ChargePlayersForm()
    if form.validate_on_submit():
        date_str = form.play_date.data
        total_amount = form.total_amount.data
        reason = form.reason.data

        play_date = parser.parse(date_str).date()
        played_date =  PlayScheduledDates.query.filter(PlayScheduledDates.play_date==play_date).first()

        attending_players = [ attendee for attendee in played_date.attendees if attendee.status=='Yes']

        total_players = len(attending_players) if len(attending_players) else 1
        amount_per_head =  total_amount/float(total_players)

        low_balance_users = {}

        for attendee in attending_players:
            user = User.query.get(attendee.attendee_email)
            if user:
                user.debit_balance(amount_per_head)

                txn_id = str(uuid.uuid4())[:8]
                debit_transaction = Transaction()
                debit_transaction.txn_id =  txn_id
                debit_transaction.party =  user.email
                debit_transaction.counter_party =  "Admin"
                debit_transaction.amount =  -amount_per_head
                debit_transaction.type =  'Dr'
                debit_transaction.reason = reason

                db.session.add(debit_transaction)
                db.session.add(user)

                if user.get_balance() < 10 :
                    low_balance_users[user.email] = (user.first_name, user.get_balance())

        played_date.is_charged = True;
        db.session.commit()
        send_bulk_emails(low_balance_users)   
        return redirect(url_for("user_page"))
    return render_template("charge_players.html", form=form)

@webapp.route("/mark_attendence", methods=["GET", "POST"])
@login_required
def mark_attendence():
    """For GET requests, display the login form. For POSTS, login the current user
    by processing the form."""

    date_str = request.form.get('date', None)
    indicator = "No"
    if "Yes" in request.form.getlist('indicator'):
        indicator="Yes"

    if request.method == 'POST' and date_str is not None and  indicator is not None:
        play_date = parser.parse(date_str).date()

        attendence = Attendence.query.filter_by(attendee_email=current_user.email, play_date=play_date).first()
        if attendence is None:
            attendence = Attendence()

        attendence.play_date = play_date
        attendence.attendee_email = current_user.email
        attendence.status = indicator

        db.session.add(attendence)
        db.session.commit()

    return redirect(url_for("user_page"))


@webapp.route("/signup", methods=["GET", "POST"])
def signup():
    """For GET requests, display the login form. For POSTS, login the current user
    by processing the form."""

    form = SignupForm()
    if form.validate_on_submit():
        if form.password.data != form.retype_password.data:
            flash('Invalid Password')
            return render_template("signup.html", form=form)

        user = User.query.get(form.email.data)
        if user :
            flash('User already exists')
            return render_template("signup.html", form=form)          

        user = User()
        user.email = form.email.data
        user.password = bcrypt.generate_password_hash(form.password.data)
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.contact_no = form.contact_no.data

        # Adding Zero Balance to user
        user.balance = Balance()
        user.balance.amount = 0.0

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("signup.html", form=form)

@webapp.route("/login", methods=["GET", "POST"])
def login():
    """For GET requests, display the login form. For POSTS, login the current user
    by processing the form."""

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.get(form.email.data)
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                user.authenticated = True
                db.session.add(user)
                db.session.commit()
                login_user(user, remember=True)
                return redirect(url_for("user_page"))
            else:
                flash('Invalid Password')
        else:
            flash('Invalid Email Id')
    return render_template("login.html", form=form)


@webapp.route("/logout", methods=["GET"])
@login_required
def logout():
    """Logout the current user."""
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return redirect(url_for("index"))

@webapp.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Changing password """
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if form.password.data != form.retype_password.data:
            flash('Passwords are not same')
        else:
            user = current_user
            user.password = bcrypt.generate_password_hash(form.password.data)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for("logout"))
    return render_template("change_password.html", form=form)

def send_forgot_password_email(user, temp_password):
    msg = Message("PlaynPay -Your new Password ",sender="mahesh.thipparthi@gmail.com")
    msg.recipients = [user.email]
    msg.body = "Your password : " + temp_password
    msg.html = "<b>Dear "+ user.first_name + "<br/>" *2 + "Your password is : " + temp_password + "<br/>"*3 + "With Regards" + "<br/>" + "Team PlaynPlay"

    mail.send(msg)
    # job = q.enqueue(tasks.queue_mail, msg) 
    flash('Please check your email')

def send_bulk_emails(low_balance_users):
    for email, details in low_balance_users.items():
        send_low_balance_email(email, details[0], details[1])


def send_low_balance_email(email, name, balance):
    msg = Message("PlaynPay -Your have low balance ",sender="mahesh.thipparthi@gmail.com")
    msg.recipients = [email]
    msg.body = "Your balace : " + str(balance)
    msg.html = "<b>Dear "+ name + "<br/>" *2 + "Kindly recharge - Your current balance is : " + str(balance) + "<br/>"*3 + "With Regards" + "<br/>" + "Team PlaynPlay"
    mail.send(msg)
    # job = q.enqueue(tasks.queue_mail, msg) 

@webapp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    """Forgot password"""

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.get(form.email.data)
        if user is None:
            flash('Email does not exist')
        else:

            temp_password = str(uuid.uuid4())[:8]
            user.password = bcrypt.generate_password_hash(temp_password)
            db.session.add(user)
            db.session.commit()

            send_forgot_password_email(user, temp_password)

            return redirect(url_for("index"))

    return render_template("forgot_password.html", form=form)
    
@webapp.route('/')
def index():
    return render_template('index.html')

@webapp.route('/user_page')
@login_required
def user_page():

    transactions = Transaction.query.filter_by(party=current_user.email).order_by(Transaction.create_at.desc())

    today = datetime.date.today()
    playdates =  PlayScheduledDates.query.filter(PlayScheduledDates.play_date >= today).order_by(PlayScheduledDates.play_date)[:4]
    plat_date_list = [str(i.play_date) for i in playdates ]

    user_attendence_list = collections.OrderedDict()
    for play_date in plat_date_list:
        user_attendence_list[play_date] = "No"

    for attendence in current_user.attendence:
        if  str(attendence.play_date) in plat_date_list:
            user_attendence_list[str(attendence.play_date)] = attendence.status

    if current_user.is_admin:
        return render_template('admin_page.html', transactions=transactions, balance = current_user.balance.amount, playdates=playdates, user_attendence_list=user_attendence_list)
    else:
        return render_template('user_page.html', transactions=transactions, balance = current_user.balance.amount, playdates=playdates, user_attendence_list=user_attendence_list)


@webapp.route("/add_balance", methods=["GET", "POST"])
@login_required
def add_balance():
    """For GET requests, display the login form. For POSTS, login the current user
    by processing the form."""

    form = BalanceForm()
    if form.validate_on_submit():
        user = User.query.get(form.email.data)
        if user:
            if user.balance is None:
                user.balance = UserBalance()
                user.balance.amount = 0.0
            user.balance.amount += form.amount.data

            txn_id = str(uuid.uuid4())[:8]
            reason = "ABU - Admin Balance update"

            credit_transaction = Transaction()
            credit_transaction.txn_id =  txn_id
            credit_transaction.party =  form.email.data
            credit_transaction.counter_party =  "Admin"
            credit_transaction.amount =  form.amount.data
            credit_transaction.type =  'Cr'
            credit_transaction.reason =  reason

            db.session.add(user.balance)
            db.session.add(credit_transaction)
            db.session.commit()
            return redirect(url_for("user_page"))
        else:
            flash('Invalid User Id')
    return render_template("add_balance.html", form=form)


@webapp.route('/send_money', methods=["GET", "POST"])
@login_required
def send_money():
    """For GET requests, display the login form. For POSTS, login the current user
    by processing the form."""

    form = PayForm()
    if form.validate_on_submit():

        transaction_amount = form.amount.data
        sender = current_user

        receiver = User.query.get(form.receiver_email.data)
        if receiver is None:
            flash('Receiver Does Not exist in system')
            return render_template("pay.html", form=form)

        if sender.balance is None or sender.balance.amount < transaction_amount:
            flash('You have insufficient balance')
            return render_template("pay.html", form=form)

        if transaction_amount <= 0:
            flash('Wrong amount entered')
            return render_template("pay.html", form=form)

        if sender.email == receiver.email:
            flash('Sender and Receiver Cant be same')
            return render_template("pay.html", form=form)            

        sender.debit_balance(transaction_amount)
        receiver.credit_balance(transaction_amount)

        txn_id = str(uuid.uuid4())[:8]
        reason = "SNM - Send Money"

        debit_transaction = Transaction()
        debit_transaction.txn_id =  txn_id
        debit_transaction.party =  sender.email
        debit_transaction.counter_party =  receiver.email
        debit_transaction.amount =  -transaction_amount
        debit_transaction.type =  'Dr'
        debit_transaction.reason = reason

        credit_transaction = Transaction()
        credit_transaction.txn_id =  txn_id
        credit_transaction.party =  receiver.email
        credit_transaction.counter_party =  sender.email
        credit_transaction.amount =  transaction_amount
        credit_transaction.type =  'Cr'
        credit_transaction.reason =  reason


        db.session.add(sender.balance)
        db.session.add(receiver.balance)
        db.session.add(debit_transaction)
        db.session.add(credit_transaction)
        db.session.commit()

        if current_user.get_balance() < 10 :
            send_low_balance_email(current_user.email, current_user.first_name, current_user.get_balance())

        return redirect(url_for("user_page"))

    return render_template("send_money.html", form=form)


if __name__ == "__main__":
    port = int(os.environ.get('PORT',5000))
    webapp.run(host="0.0.0.0", port=port)
    
