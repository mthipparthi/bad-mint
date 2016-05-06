import sys
import os

BASE_DIR =  os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,BASE_DIR)

from app.app import webapp
from app.models import db

if __name__ == '__main__':
	with webapp.app_context():
		db.metadata.create_all(bind=db.engine)