import os
from PIL import Image
import secrets
from flask import Blueprint, render_template, request, url_for, flash, redirect, session, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .extensions import db,  bcrypt
from .models import User, Post
from .forms import UpdateAccountForm, UpdatePost
from flask_login import login_user, logout_user, current_user, login_required

second = Blueprint('second', __name__, static_folder='static', template_folder='templates')

# ---------------------- HOME ------------------------
@second.route('/')
@second.route('/home')
@login_required
def home():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('home.html', username=session.get('username'), posts=posts)

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
    return render_template('users.html', title='User Page', data=data)

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
    return render_template('account.html', title='Account', image_file=image_file, form=form)

