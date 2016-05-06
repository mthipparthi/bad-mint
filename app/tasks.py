import app

def queue_mail(msg):
    with app.webapp.app_context():
        app.mail.send(msg)