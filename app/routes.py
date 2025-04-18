from flask import render_template, redirect, url_for, request, session, flash, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from app import app, db
from app.models import User, Post, Like, Comment, Trialbooking
from app.helpers import login_required, error
from app.email import send_confirmation_email
from flask import make_response
import re
import bleach
from datetime import datetime, timezone


@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response

# Validation Function
def validate_input(input_str):
    pattern = r"^[A-Za-z0-9.,!+\-?'@#&’\";:\s]+$"
    if not re.match(pattern, input_str):
        raise ValueError("Invalid input. Only alphabets, numbers, and .,!?@#&'\";: are allowed.")
    return input_str

def validate_password(password):
    # Password policy with regex
    pattern = r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$"
    if not re.match(pattern, password):
        raise ValueError(
            "Password must be at least 8 characters long, include an uppercase letter, "
            "a lowercase letter, a digit, and a special character."
        )
    return password


def sanitize_input(input_str):
    # Clean input to remove all HTML tags and allow only plain text
    return bleach.clean(input_str, tags=[], attributes={}, strip=True)


@app.context_processor
def inject_user_status():
    # Check if the user is logged in based on session data
    return {"is_authenticated": "user_id" in session}



# Routes Definition
@app.route("/")
# @login_required
def index():
    return render_template("homepage.html")


@app.route("/learning")
@login_required
def learning():
    return render_template("learning.html")


@app.route("/programs")
@login_required
def programs():
    return render_template("programs.html")


@app.route("/grammar")
@login_required
def grammar():
    return render_template("grammar.html")

@app.route("/skills")
@login_required
def skills():
    return render_template("skills.html")

@app.route("/allbookings")
@login_required
def allbookings():
    users = User.query.all()
    trialbooking = Trialbooking.query.order_by(Trialbooking.created_at.desc()).all()
    cu_id = session.get("user_id")
    current_user = User.query.filter_by(id=cu_id).first() if cu_id else None
    is_admin = current_user.is_admin if current_user else False
    return render_template("allbookings.html", users=users, is_admin=is_admin, trialbooking=trialbooking, current_user=current_user)


@app.route("/allposts")
@login_required
def allposts():
    # is_authenticated = "user_id" in session
    user_id = session.get("user_id")
    search_query = request.args.get("q")

    page = request.args.get("page", 1, type=int)
    per_page = 5
    if search_query:
        # posts = Post.query.filter(Post.title.ilike(f"%{search_query}%")).order_by(Post.date_posted.desc()).all()
        posts = Post.query.filter(Post.title.ilike(f"%{search_query}%")).order_by(Post.date_posted.desc()).paginate(page=page, per_page=per_page)
    else:
        # posts = Post.query.order_by(Post.date_posted.desc()).all()
        posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=per_page)

    for post in posts.items:
        # Set user_liked if user is logged in and has liked this post
        if user_id:
            post.user_liked = Like.query.filter_by(user_id=user_id, post_id=post.id).first() is not None
        else:
            post.user_liked = False
    
        post.comment_count = post.comments.count()

    if not posts.items:
        flash("No posts found!", "info")
        return render_template("noposts.html")
    return render_template("index.html", posts=posts, user_id=user_id)



@app.route('/like/<int:post_id>', methods=['POST'])
def like_post(post_id):

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error": "You need to log in to like a post."}), 401

    post = Post.query.get_or_404(post_id)
    existing_like = Like.query.filter_by(user_id=user_id, post_id=post_id).first()
    
    if existing_like:
        db.session.delete(existing_like)
        liked = False
    else:
        like = Like(user_id=user_id, post_id=post_id)
        db.session.add(like)
        liked = True

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An error occurred while processing your request."}), 500

    return jsonify({"liked": liked, "likes_count": post.likes.count()})


@app.route('/comment/<int:post_id>', methods=['POST'])
def comment_post(post_id):

    user_id = session.get("user_id")

    if not user_id:
        flash("You need to log in to comment on a post.", "error")
        return redirect("/login")
    
    post = Post.query.get_or_404(post_id)
    commentContent = request.form.get('commentposted')

    # White space check
    if not commentContent.strip():
        flash("Comment cannot be empty", "error")
        return redirect(request.referrer or "/allposts")
    
    if not commentContent:
        flash("Comment cannot be empty", "error")
        return redirect(request.referrer or "/allposts")
    
    try:
        validateComment = validate_input(commentContent)
        sanitizedComment = sanitize_input(validateComment)
    except Exception as e:
        flash(str(e), "danger")
        return redirect("/allposts")
    
    new_comment = Comment(comment_content=sanitizedComment, user_id=user_id, post_id=post_id)
    db.session.add(new_comment)
    db.session.commit()
    return redirect(request.referrer or "/allposts")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        session.clear()

    if request.method == "POST":
        username = request.form.get("name")
        password = request.form.get("password")

        if not username or not password:
            flash("Enter Username and Password!", "danger")
            return redirect("/login")
        
        try:
            username = sanitize_input(validate_input(username)).lower()
        except Exception as e:
            flash(str(e), "danger")
            return redirect("/login")
        
        # username = username.lower()        
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.passwordhash, password):
            flash("Username or Password Incorrect!", "danger")
            return redirect("/login")
        
        session["user_id"] = user.id
        flash("Successfully Logged in!", "success")
        return redirect("/")
    return render_template("login.html")
    
    
@app.route("/logout", methods=["GET", "POST"])
def logout():

    # session.clear()
    flash("Logged Out!", "success")
    session.pop("user_id", None)
    return redirect("/")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    # session.clear()
    if "user_id" in session:
        session.clear()

    if request.method == "POST":
        username = request.form.get("name")
        password = request.form.get("password")
        confirmPassword = request.form.get("confirmpasswordlb")

        if not username or not password or not confirmPassword:
            flash("Oops! You did not input a name or password.", "danger")
            return redirect("/signup")
            
        
        if password != confirmPassword:
            flash("Oops! Your passwords don't match!", "danger")
            return redirect("/signup")

        if len(password) < 8:
            flash("Password must be at least 6 characters long.", "danger")
            return redirect("/signup")
        
        # Validate and sanitize inputs
        try:
            username = sanitize_input(validate_input(username)).lower()
            validate_password(password)
            validate_password(confirmPassword)
        except Exception as e:
            flash(str(e), "danger")
            return redirect("/signup")
        
        # username = username.lower()  # Ensure username is case-insensitively unique
        
        # Check if username exists in database
        existingUsername = User.query.filter_by(username=username).first()
        if existingUsername:
            flash(f"Oops! {username} has been taken! Retry another!", "danger")
            return redirect("/signup")

        generatedPassword = generate_password_hash(password)
        new_user = User(username=username, passwordhash=generatedPassword)
        db.session.add(new_user)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"An unexpected  error occurred: {str(e)}", 'danger')
            return redirect("/signup")

        session["user_id"] = new_user.id
        flash("Registration successful!", "success")
        return redirect("/")

    return render_template("signup.html")


@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    user_id = session.get("user_id")  

    if request.method == "POST":
        post_content = request.form.get("postcontent")

        if not post_content:
            flash("Please fill in content field!", "danger")
            return redirect("/create")
        
        if len(post_content) < 5:
            flash("Content must be at least 5 characters.", "danger")
            return redirect("/create")
        
        try:
            validateComment = validate_input(post_content)
            sanitizedComment = sanitize_input(validateComment)
        except Exception as e:
            flash(str(e), "danger")
            return redirect("/create")

        creator = User.query.get(user_id)
        if not creator:
            flash("Oops! An error occurred while fetching your details!", "danger")
            return redirect("/create")
  
        new_post = Post(
            content=sanitizedComment,
            creator_id=user_id,
            creator_name=creator.username,
        )
        db.session.add(new_post)
        db.session.commit()

        flash("Review created successfully!", "success")
        return redirect("/allposts")
    return render_template("create.html")


@app.route("/myposts")
@login_required
def myposts():
    user_id = session["user_id"]

    page = request.args.get("page", 1, type=int)
    per_page = 5

    my_posts = Post.query.filter_by(creator_id=user_id).order_by(Post.date_posted.desc()).paginate(page=page, per_page=per_page)
    # my_posts = Post.query.filter_by(creator_id=user_id).order_by(Post.date_posted.desc()).all()
    # if not my_posts.items:
    #     flash("Sorry! You have no posts available!", "danger")
    return render_template("myposts.html", posts=my_posts)


@app.route("/creators")
def creators():
    # cu_id : current user id
    users = User.query.all()
    cu_id = session.get("user_id")
    current_user = User.query.filter_by(id=cu_id).first() if cu_id else None
    is_admin = current_user.is_admin if current_user else False
    return render_template("creators.html", users=users, current_user=current_user, is_admin=is_admin)


@app.route("/edit/<int:post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.creator_id != session["user_id"]:
        flash("You are not authorized to edit this post!", "danger")
        return redirect("/allposts")

    if request.method == "POST":
        post_content = request.form.get("postcontent")

        if not post_content:
            flash("Please fill in the content field!", "danger")
            return redirect(f"/edit/{post_id}")
        
        try:
            validateComment = validate_input(post_content)
            sanitizedComment = sanitize_input(validateComment)
        except Exception as e:
            flash(str(e), "danger")
            return redirect("/allposts")
        
        # Update the post
        post.content = sanitizedComment
        db.session.commit()

        flash("Post updated successfully!", "success")
        return redirect("/myposts")
    return render_template("edit.html", post=post)


@app.route("/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get(post_id)
    user_id = session.get("user_id")

    if not post or post.creator_id != user_id:
        flash("Unauthorized access!", "danger")
        return redirect("/myposts")

    db.session.delete(post)
    db.session.commit()
    flash("Post deleted successfully!", "success")
    return redirect("/myposts")


@app.route("/progress")
def progress():
    return render_template("progress.html")


@app.route('/delete_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def delete_user(user_id):
    if request.method == "POST":
        current_user = User.query.get(session.get("user_id"))

        if not current_user.is_admin:
            flash("Unauthorized action!", "danger")
            return redirect("/creators")

        user_to_delete = User.query.get_or_404(user_id)

        # Prevent admin from deleting themselves
        if user_to_delete.id == current_user.id:
            flash("You cannot delete your own account.", "danger")
            return redirect("/creators")

        try:
            user = User.query.get(user_id)
            Post.query.filter_by(creator_id=user.id).delete()
            Comment.query.filter_by(user_id=user.id).delete()
            Like.query.filter_by(user_id=user.id).delete()
            db.session.delete(user)
            db.session.commit()

            # Delete the user
            db.session.delete(user_to_delete)
            db.session.commit()

            # Reaffirm my admin status
            admin_user = User.query.get(current_user.id)
            if admin_user:
                admin_user.is_admin = True 
                db.session.commit()

            flash(f"User {user_to_delete.username} has been deleted.", "success")
            return redirect("/creators")
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while deleting the user.", "danger")
            return redirect("/creators")


@app.route('/bookings', methods=['GET', 'POST'])
@login_required
def trial_lesson():
    users = User.query.all()
    cu_id = session.get("user_id")
    current_user = User.query.filter_by(id=cu_id).first() if cu_id else None
    is_admin = current_user.is_admin if current_user else False

    if request.method == 'POST':
        name = request.form['name']
        lastname = request.form['lastname']
        email = request.form['email']
        date = request.form['date']
        time = request.form['time']
        phone = request.form['phone']

        if not name or not lastname:
            flash("Name and Last name are required.", "danger")
            return redirect("/bookings")
        
        if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email address.", "danger")
            return redirect("/bookings")
        
        if (phone.startswith('+') and not phone[1:].isdigit()) or (not phone.startswith('+') and not phone.isdigit()) or len(phone) < 7:
            flash("Phone number must be numeric and at least 7 digits long.", "danger")
            return redirect("/bookings")

        try:
            name = sanitize_input(validate_input(name))
            lastname = sanitize_input(validate_input(lastname))
            email = sanitize_input(validate_input(email))
            phone = sanitize_input(validate_input(phone))
        except Exception as e:
            flash(str(e), "danger")
            return redirect("/bookings")

        # Past date Logic
        # Combine date and time strings into one datetime object
        try:
            selected_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
            selected_datetime = selected_datetime.replace(tzinfo=timezone.utc)
        except ValueError:
            flash("No valid date or time provided.", "error")
            return redirect(request.referrer)
        now = datetime.now(timezone.utc)
        if selected_datetime < now:
            flash("You cannot book a time in the past.", "error")
            return redirect(request.referrer)
        
        booking = Trialbooking(name=name, lastname=lastname, email=email, date=date, time=time, phone=phone, created_at=datetime.now(timezone.utc))
        db.session.add(booking)
        db.session.commit()

        send_confirmation_email(email, name, lastname, date, time, phone, booking.created_at)
        flash('Your trial lesson is booked! Please check your email for details.', 'success')
        return redirect("/bookings")

    return render_template('bookings.html', users=users, is_admin=is_admin)


@app.route('/delete_booking/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def delete_booking(booking_id):
    if request.method == "POST":
        current_user = User.query.get(session.get("user_id"))

        if not current_user.is_admin:
            flash("Unauthorized action!", "danger")
            return redirect("/allbookings")

        booking_to_delete = Trialbooking.query.get_or_404(booking_id)

        try:
            db.session.delete(booking_to_delete)
            db.session.commit()

            flash(f"Bookinf for {booking_to_delete.name} has been deleted.", "success")
            return redirect("/allbookings")
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while deleting the user.", "danger")
            return redirect("/allbookings")