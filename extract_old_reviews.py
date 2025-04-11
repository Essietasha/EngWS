
from app import app, db
from app.models import Post
import json

with app.app_context():
    posts = Post.query.all()
    postdata = []

    for post in posts:
        postdata.append({
            "content": post.content,
            "date_posted": post.date_posted.isoformat(),
            "creator_id": post.creator_id,
            "creator_name": getattr(post, "creator_name", None)  # Safe check if it exists
        })

    with open("reviews_postdata.json", "w") as f:
        json.dump(postdata, f, indent=2)
