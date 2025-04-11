from app import app, db
from app.models import User

with app.app_context():
    users = User.query.all()
    for user in users:
        print(f'ID: {user.id}, Username: {user.username}, "passwordhash": "{user.passwordhash}')

# In terminal Run: python extract_old_users.py > users_data.json