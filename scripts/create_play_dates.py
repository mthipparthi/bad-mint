# from models import PlayScheduledDates
import datetime
import os
import sys

BASE_DIR =  os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,BASE_DIR)

from app.app import webapp
from app.models import PlayScheduledDates
from app.models import db
# db = models.db

def get_weekend_list():
	start = datetime.date.today()
	end = datetime.date(2016, 12, 31)
	delta = datetime.timedelta(days=1)
	d = start
	weekend_list = []
	weekend = set([5, 6])
	while d <= end:
	    if d.weekday() in weekend:
	        weekend_list.append(d)
	    d += delta
	
	return weekend_list


def main():
    """Main entry point for script."""
    with webapp.app_context():
        db.metadata.create_all(db.engine)

        for weekend in get_weekend_list():
        	pd = PlayScheduledDates()
        	pd.play_date = weekend
        	db.session.add(pd)
        	db.session.commit()

if __name__ == '__main__':
    sys.exit(main())