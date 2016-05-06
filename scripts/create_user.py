import sys
import os

BASE_DIR =  os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,BASE_DIR)

from app.app import webapp
from app.app import bcrypt
from app.models import db
from app.models import User
from app.models import Balance
from getpass import getpass

def main():
    """Main entry point for script."""
    with webapp.app_context():
        db.metadata.create_all(db.engine)
        if User.query.all():
            print 'A user already exists! Create another? (y/n):',
            create = raw_input()
            if create == 'n':
                return
        
        print 'Enter email address: ',
        email = raw_input()
        password = getpass()
        assert password == getpass('Password (again):')

        print 'Enter First Name: ',
        first_name = raw_input()

        print 'Enter Last Name: ',
        last_name = raw_input()

        print 'Enter Contact No: ',
        contact_no = raw_input()

        print 'Is admin? (y/n):'
        is_admin = raw_input()

        user = User()
        user.email = email
        user.password = bcrypt.generate_password_hash(password)
        user.first_name = first_name
        user.last_name = last_name
        user.contact_no = contact_no

        # Adding Zero Balance to user
        user.balance = Balance()
        user.balance.amount = 0.0

        if is_admin=="y":
            user.is_admin = True

        db.session.add(user)
        db.session.commit()
        print 'User added.'

if __name__ == '__main__':
    sys.exit(main())