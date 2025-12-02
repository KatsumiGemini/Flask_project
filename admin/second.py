import os
from PIL import Image
import secrets
from flask import Blueprint, render_template, request, url_for, flash, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .extensions import db
from .models import User, Post
from flask_login import login_user, logout_user, current_user, login_required

second = Blueprint('second', __name__, static_folder='static', template_folder='templates')

# ---------------------- HOME ------------------------
@second.route('/')
@second.route('/home')
@login_required
def home():
    posts = Post.query.join(User).add_columns(User.username, Post.id, Post.title, Post.content, Post.date_posted)\
                      .order_by(Post.date_posted.desc()).all()
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

    return render_template("post.html", username=current_user.username)

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

        hashed_password = generate_password_hash(password)
        user = User(username=username, email=email, password=hashed_password)
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
        if user and check_password_hash(user.password, password):
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


# -------------------- UPDATE USER --------------------

@second.route("/update_user", methods=["POST"])
@login_required
def update_user():
    user_id = request.form.get("user_id")
    user = User.query.get_or_404(user_id)

    user.username = request.form.get("name")
    user.email = request.form.get("email")
    user.role_id = int(request.form["role"])

    password = request.form.get("password")
    if password.strip():
        user.password = generate_password_hash(password)

    db.session.commit()
    return jsonify({"status": "success"})

# -------------------- ACCOUNT UPDATE WITH PICTURE --------------------
def save_picture(form_picture):
    upload_folder = os.path.join('static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)

    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(upload_folder, picture_fn)

    i = Image.open(form_picture)
    i.thumbnail((125, 125))
    i.save(picture_path)

    return picture_fn

@second.route("/account", methods=["GET", "POST"])
@login_required
def account():
    user = current_user

    if request.method == "POST":
        user.username = request.form['username']
        user.email = request.form['email']

        if 'image' in request.files:
            file = request.files['image']
            if file.filename != '':
                picture_file = save_picture(file)

                if user.image:
                    old_path = os.path.join('static/uploads', user.image)
                    if os.path.exists(old_path):
                        os.remove(old_path)

                user.image = picture_file

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('second.account'))

    return render_template('account.html', user=user, username=user.username)
