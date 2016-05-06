"""Forms for the bull application."""
from flask_wtf import Form
from wtforms import TextField, PasswordField, SelectField, FloatField, IntegerField
from wtforms.validators import DataRequired

class LoginForm(Form):
    """Form class for user login."""
    email = TextField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class SignupForm(Form):
    """Form class for user sign up."""
    email = TextField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    retype_password = PasswordField('Reenter Password', validators=[DataRequired()])
    first_name = TextField('First Name', validators=[DataRequired()])
    last_name = TextField('Last Name')
    contact_no = IntegerField('Contact no')

class ForgotPasswordForm(Form):
    """Form class for changing password."""
    email = TextField('Email', validators=[DataRequired()])

class ChangePasswordForm(Form):
    """Form class for changing password."""
    password = PasswordField('Password', validators=[DataRequired()])
    retype_password = PasswordField('Reenter Password', validators=[DataRequired()])

class BalanceForm(Form):
	email = TextField('User Email', validators=[DataRequired()])
	amount = FloatField('Amount', validators=[DataRequired()])

class PayForm(Form):
	receiver_email = TextField('Receiver Email', validators=[DataRequired()])
	amount = FloatField('Amount', validators=[DataRequired()])

class PlayDatesForm(Form):
    """Form class for changing password."""
    dates = TextField('Dates')

class AttendenceForm(Form):
    play_date = TextField('Play Date', validators=[DataRequired()])
    indicator = TextField('Are you for Game?', validators=[DataRequired()])

class ChargePlayersForm(Form):
    play_date = TextField('Play Date', validators=[DataRequired()])
    total_amount = FloatField('Total Amount', validators=[DataRequired()])
    reason = TextField('Reason', validators=[DataRequired()])
	