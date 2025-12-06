import os
from PIL import Image
import secrets
from flask import Blueprint, render_template, request, url_for, flash, redirect, session, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .extensions import db,  bcrypt, mail
from .model.models import User, Post
from .form.forms import UpdateAccountForm, UpdatePost, PasswordResetRequestForm
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message

second = Blueprint('second', __name__, static_folder='static', template_folder='templates')

# ---------------------- HOME ------------------------
@second.route('/')
@second.route('/home')
@login_required
def home():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')

    if q:
        posts = Post.query.join(User).filter(
            (Post.title.ilike(f"%{q}%")) | 
            (User.username.ilike(f"%{q}%"))
        ).order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)
    else:
        posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=10)

    return render_template('home.html', username=session.get('username'), posts=posts, search_query=q)

# ---------------------- POST ------------------------
@second.route("/post", methods=["GET", "POST"])
@login_required
def create_blog():
    if request.method == "POST":
        title = request.form['title']
        content = request.form['content']

        post = Post(title=title, content=content, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()

        flash("Blog created successfully!", "success")
        return redirect(url_for("second.create_blog"))
    
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.date_posted.desc()).all()

    return render_template("post.html", username=current_user.username, posts=posts)

# -------------------- USER DATA --------------------
@second.route("/users")
@login_required
def user_data():
    try:
        data = User.query.all() 
    except Exception as err:
        flash(f"Database Error: {err}", "danger")
        data = []
    return render_template('users.html', title='User Page', data=data, username=session.get('username'))

# -------------------- REGISTER --------------------

@second.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("second.register"))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password, image_file="default.jpg")
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect(url_for("second.register"))

    return render_template("register.html")

# -------------------- LOGIN --------------------

@second.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('second.home'))
        else:
            flash('Login Unsuccessful. Check email and password', 'danger')

    return render_template('login.html')

# -------------------- LOGOUT --------------------
@second.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('second.login'))

# -------------------- DELETE USER --------------------
@second.route('/delete/<int:id>')
@login_required
def delete(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('second.user_data'))

@second.route("/post/<int:post_id>/delete", methods=["POST", "GET"])
@login_required
def delete_blog(post_id):
    post = Post.query.get_or_404(post_id)

    # Check owner
    if post.user_id != current_user.id:
        flash("You are not authorized to delete this post.", "danger")
        return redirect(url_for("second.create_blog"))

    db.session.delete(post)
    db.session.commit()
    flash("Post deleted successfully!", "success")
    return redirect(url_for("second.create_blog"))

# -------------------- UPDATE --------------------

@second.route("/update_user", methods=["POST"])
@login_required
def update_user():
    user_id = request.form.get("user_id")
    user = User.query.get_or_404(user_id)

    user.username = request.form.get("name")
    user.email = request.form.get("email")
    user.password = request.form.get("password")

    password = request.form.get("password")
    if password.strip():
        user.password = bcrypt.generate_password_hash(password)

    db.session.commit() 
    return jsonify({"status": "success"})
                                                                                                        
@second.route("/post/<int:post_id>/edit", methods=["POST"])
@login_required
def edit_blog(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author != current_user:
        flash("You cannot edit this post!", "danger")
        return redirect(url_for("second.create_blog"))

    post.title = request.form["title"]
    post.content = request.form["content"]
    db.session.commit()
    flash("Post updated successfully!", "success")
    return redirect(url_for("second.create_blog"))

# -------------------- ACCOUNT UPDATE WITH PICTURE --------------------
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(second.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@second.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()

    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file

        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('second.account'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form, username=session.get('username'))

# ---------------------------------RESET PASSWORD---------------------------------------
def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message("Password Reset Request", recipients=[user.email])

    reset_url = url_for('second.reset_password', token=token, _external=True)

    msg.body = f'''To reset your password, click the link below:

    {reset_url}

    If you did not make this request, simply ignore this email.
    '''
    mail.send(msg)

@second.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('second.home'))

    form = PasswordResetRequestForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash("A password reset link has been sent to your email.", "success")
        return redirect(url_for('second.login'))

    return render_template("reset_request.html", form=form, legend="Reset Password")

@second.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('second.home'))

    user = User.verify_reset_token(token)
    if user is None:
        flash("Invalid or expired token.", "danger")
        return redirect(url_for('second.reset_request'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash("Passwords do not match. Please try again.", "danger")
            return redirect(url_for('second.reset_password', token=token))

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user.password = hashed_pw
        db.session.commit()

        flash("Your password has been updated!", "success")
        return redirect(url_for('second.login'))

    return render_template("reset_password.html", token=token, title='Reset Password', legend="Reset Password")

# ---------------------------SEARCH BLOG----------------------------------
# @second.route("/search")
# def search():
#     query = request.args.get("q", "")

#     if not query:
#         flash("Please enter a search term.", "warning")
#         return redirect(url_for("second.dashboard"))

#     results = Content.query.filter(
#         (Content.title.ilike(f"%{query}%")) |
#         (Content.author.ilike(f"%{query}%"))
#     ).all()

#     return render_template("search_results.html", results=results, query=query)

# ------------------------------User Account View---------------------------
# Assuming 'second' is your Blueprint instance

@second.route("/post/<int:post_id>")
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("post_detail.html", post=post, username=session.get('username'))

@second.route("/user/<string:username>")
def user_profile_view(username):
    
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    
    return render_template('view_account.html', user=user, posts=posts, username=session.get('username'))
