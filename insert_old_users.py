import json
from app import app, db
from app.models import User

with app.app_context():
    with open("users_data.json", "r") as file:
        users = json.load(file)

    for user in users:
        if not User.query.filter_by(username=user["username"]).first():
            user = User(username=user["username"], passwordhash=user["passwordhash"])
            db.session.add(user)

    db.session.commit()
    print("Old users inserted successfully.")

print("Done")
