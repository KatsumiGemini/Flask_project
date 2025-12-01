import os
from PIL import Image
import secrets
import mysql.connector
from flask import Blueprint, render_template, request, url_for, flash, redirect, session, jsonify,abort
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from mysql.connector import Error as MySQLError

second = Blueprint('second', __name__, static_folder='static', template_folder='templates')
def get_db_connection():
    con = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="flask_db"
    )
    return con

# ---------------------- HOME ------------------------
@second.route('/')
@second.route('/home')
def home():
    username = session.get('username')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
    SELECT posts.id, posts.title, posts.content, posts.created_at, users.username AS username
    FROM posts
    JOIN users ON posts.user_id = users.id
    ORDER BY posts.created_at DESC
    """)
    posts = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template('home.html', username=username, posts=posts)

# ---------------------- POST ------------------------
@second.route('/post')
def post():
    return render_template('post.html')

@second.route("/create-blog", methods=["GET", "POST"])
def create_blog():
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("second.login"))

    if request.method == "POST":
        title = request.form['title']
        content = request.form['content']
        user_id = session['user_id']
        created_at = datetime.now()
        updated_at = datetime.now()

        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO posts (user_id, title, content, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, title, content, created_at, updated_at)
                )
                conn.commit()
            flash("Blog created successfully!", "success")
        except Exception as e:
            flash(f"Error: {e}", "danger")
        finally:
            conn.close()

        return redirect(url_for("second.create_blog"))  

    return render_template("post.html", username=session.get("username"))

# -------------------- USER DATA --------------------
@second.route("/users")
def user_data():
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users")
        data = cursor.fetchall()
        cursor.close()
    except MySQLError as err:
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

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s )"
            values = (username, email, hashed_password)
            cur.execute(query, values)
            conn.commit()
            cur.close()
            conn.close()

            flash("Account created successfully!", "success")
            return redirect(url_for("second.register"))

        except mysql.connector.Error as err:
            flash(f"Database Error: {err}", "danger")
            return redirect(url_for("second.register"))

    return render_template("register.html")

# -------------------- LOGIN --------------------

@second.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT id, username, email, password FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('second.home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
            return render_template('login.html')
        
    return render_template('login.html')

# @second.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         email = request.form["email"]
#         password = request.form["password"]

#         conn = get_db_connection()
#         cur = conn.cursor(dictionary=True)
#         cur.execute("SELECT * FROM users WHERE email = %s", (email,))
#         user = cur.fetchone()
#         cur.close()
#         conn.close()

#         if user and check_password_hash(user["password"], password):
#             # Save user info in session
#             session["user_id"] = user["id"]
#             session["username"] = user["name"]
#             session["role_id"] = user["role_id"]

#             flash("Login successful!", "success")

#             # Redirect based on role
#             if user["role_id"] == 1:
#                 return redirect(url_for("second.admin_dashboard"))
#             elif user["role_id"] == 2:
#                 return redirect(url_for("second.user_dashboard"))
#             elif user["role_id"] == 3:
#                 return redirect(url_for("second.staff_dashboard"))
#             else:
#                 flash("Role not recognized!", "danger")
#                 return redirect(url_for("second.login"))
#         else:
#             flash("Invalid email or password", "danger")
    
#     return render_template("login.html")
# -------------------- LOGOUT --------------------
@second.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('second.login'))

# -------------------- DELETE USER --------------------

@second.route('/delete/<int:id>')
def delete(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        flash('User deleted successfully!', 'success')
    except MySQLError as err:
        flash(f"Database Error: {err}", "danger")
    return redirect(url_for('second.user_data'))

# -------------------- UPDATE USER --------------------

@second.route("/update_user", methods=["POST"])
def update_user():
    user_id = request.form.get("user_id")
    name = request.form.get("name")
    email = request.form.get("email")
    role = int(request.form["role"]) 
    password = request.form.get("password")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if password.strip() == "":
            query = "UPDATE users SET name=%s, email=%s, role_id=%s WHERE id=%s"
            cursor.execute(query, (name, email, role, user_id))
        else:
            query = "UPDATE users SET name=%s, email=%s, role_id=%s, password=%s WHERE id=%s"
            cursor.execute(query, (name, email, role, password, user_id))

        conn.commit()
        cursor.close()
        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    
# -------------------- ACCOUNT UPDATE WITH PICTURE --------------------
# @second.route("/account")
# def account():
#     if 'user_id' not in session:
#         flash("Please log in first.", "warning")
#         return redirect(url_for("second.login"))

#     user_id = session['user_id']
#     conn = get_db_connection()
#     with conn.cursor(dictionary=True) as cur:
#         cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
#         user = cur.fetchone()
#     conn.close()

#     return render_template('account.html', user=user, username=session.get('username'))

def save_picture(form_picture):
    upload_folder = os.path.join('static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)

    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(upload_folder, picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@second.route("/account", methods=["GET", "POST"])
def account():
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("second.login"))

    user_id = session['user_id']
    conn = get_db_connection()
    with conn.cursor(dictionary=True) as cur:
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()

        if request.method == "POST":
            username = request.form['username']
            email = request.form['email']

            # Handle image upload
            if 'image' in request.files:
                file = request.files['image']
                if file.filename != '':
                    picture_file = save_picture(file)

                    
                    if user['image']:
                        old_path = os.path.join('static/uploads', user['image'])
                        if os.path.exists(old_path):
                            os.remove(old_path)

                    cur.execute(
                        "UPDATE users SET name=%s, email=%s, image=%s WHERE id=%s",
                        (username, email, picture_file, user_id)
                    )
                else:
                    cur.execute(
                        "UPDATE users SET name=%s, email=%s WHERE id=%s",
                        (username, email, user_id)
                    )
            else:
                cur.execute(
                    "UPDATE users SET name=%s, email=%s WHERE id=%s",
                    (username, email, user_id)
                )

            conn.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for('second.account'))

    conn.close()
    return render_template('account.html', user=user, username=session.get('username'))