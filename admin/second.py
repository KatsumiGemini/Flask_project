import mysql.connector
from flask import Blueprint, render_template, request, url_for, flash, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
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
    return render_template('home.html', username=username)

# -------------------- VIEW USERS --------------------
@second.route("/userdata")
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
    return render_template('user_data.html', title='User Page', data=data)

# -------------------- REGISTER --------------------
@second.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        role = int(request.form["role"]) 
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("second.register"))

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cur = conn.cursor()
            query = "INSERT INTO users (name, email, role_id, password, created_at) VALUES (%s, %s, %s, %s, %s)"
            values = (username, email, role, hashed_password, datetime.now())
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
            cur.execute("SELECT name, email, password FROM users WHERE email = %s", (email,))
            user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['username'] = user['name']
            flash('Login successful!', 'success')
            return redirect(url_for('second.home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
            return render_template('login.html')
        
    return render_template('login.html')

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
