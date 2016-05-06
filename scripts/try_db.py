import os
import sys
import datetime

BASE_DIR =  os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,BASE_DIR)


from getpass import getpass

from app.app import webapp
from app.app import bcrypt

from app.models import db
from app.models import Transaction
from app.models import PlayScheduledDates
from app.models import Attendence
from app.models import User
from app.models import PlayScheduledDates


def main():
    """Main entry point for script."""
    with webapp.app_context():
        db.metadata.create_all(db.engine)

        today = datetime.date.today()
        playdates =  PlayScheduledDates.query.filter(PlayScheduledDates.play_date >= today).order_by(PlayScheduledDates.play_date)[:4]
        plat_date_list = [str(i.play_date) for i in playdates ]
        print plat_date_list

        use_attendence_list = []
        user = User.query.get('mahesh.thipparthi@gmail.com')
        a= [ (attendence.play_date, attendence.status) for attendence in user.attendence]
        for attendence in user.attendence:
            if  str(attendence.play_date) in plat_date_list:
                use_attendence_list.append((str(attendence.play_date), attendence.status))
        print use_attendence_list[0][1]


if __name__ == '__main__':
    sys.exit(main())