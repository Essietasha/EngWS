import json
from datetime import datetime
from app import app, db
from app.models import User, Post

with app.app_context():
    with open("reviews_postdata.json", "r") as f:
        reviews = json.load(f)

    for review in reviews:
        user = User.query.filter_by(username=review["creator_name"]).first()

        if user:
            # Convert the string date_posted to a datetime object
            date_posted = datetime.fromisoformat(review["date_posted"])

            post = Post(
                content=review["content"],
                date_posted=date_posted, 
                creator_id=user.id,
                creator_name=user.username
            )
            
            db.session.add(post)

    db.session.commit()
    print("Old reviews inserted into the new database.")
