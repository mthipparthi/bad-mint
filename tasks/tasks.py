from app import app
from app import mail

def queue_mail(msg):
    with app.app_context():
        mail.send(msg)