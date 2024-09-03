from api.models import User
from api import Session

def get_user(uid:int):
    session = Session()
    user = session.query(User).first()
    return user