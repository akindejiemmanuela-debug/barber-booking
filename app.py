from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.secret_key = "ayuugggnnndmmbvfffdddg"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/book", methods=["POST"])
def book():
    name = request.form.get("name")
    phone = request.form.get("phone")
    service = request.form.get("service")
    date = request.form.get("date")
    time = request.form.get("time")

    if not name or not phone or not service:
        return "All fields are required ❌"

    conn = sqlite3.connect("barber.db")
    cursor = conn.cursor()

# Check if the date and time are already booked
    cursor.execute(
        "SELECT * FROM appointments                     WHERE date = ? AND time = ?",
        (date, time)
    )

    existing_booking = cursor.fetchone()

    if existing_booking:
        conn.close()
        return """
    <h2>❌ This time slot is already booked.</h2>
    <a href="/">Go Back</a>
    """

    cursor.execute("""
    INSERT INTO appointments
    (name, phone, service, date, time)
    VALUES (?, ?, ?, ?, ?)
""", (name, phone, service, date, time))

    conn.commit()
    conn.close()

    return """
<h2>✅ Booking Successful</h2>
<a href="/">Go Home</a>
"""

@app.route("/admin")
def admin():

    if not session.get("logged_in"):
        return redirect("/login")

    conn = sqlite3.connect("barber.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM appointments")
    data = cursor.fetchall()
    conn.close()


    return render_template("admin.html", bookings=data);
    




@app.route("/delete/<int:id>")
def delete(id) :
    conn = sqlite3.connect("barber.db")
    cursor = conn.cursor()
    
    cursor.execute(
        "DELETE FROM appointments WHERE id = ?" ,
            (id,)
)

    conn.commit()
    conn.close()
    
    return """
<h2>Delete Successful ✅</h2>
<a href="/admin">Back to Admin</a>
"""
@app.route("/edit/<int:id>")
def edit(id):
    conn = sqlite3.connect("barber.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM appointments WHERE id = ?",
        (id,)
    )

    booking = cursor.fetchone()

    conn.close()

    return render_template(
        "edit.html",
        booking=booking
    )
    return redirect("/admin")


@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    name = request.form.get("name")
    phone = request.form.get("phone")
    service = request.form.get("service")

    conn = sqlite3.connect("barber.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE appointments
        SET name = ?, phone = ?, service = ?
        WHERE id = ?
    """, (name, phone, service, id))

    conn.commit()
    conn.close()

    return redirect("/admin")


@app.route("/login")
def login():
    return render_template("login.html")
    


@app.route("/login", methods=["POST"])
def login_post():

    username = request.form.get("username")
    password = request.form.get("password")

    if username == "admin" and password == "8888":
        session["logged_in"] = True
        return redirect("/admin")

    return """
<h2>Invalid Username or Password ❌</h2>
<a href='/'>Go Home</a>
"""

@app.route("/logout")
def logout():

    session.pop("logged_in", None)

    return redirect("/login")

@app.route("/approve/<int:id>")
def approve(id):

    conn = sqlite3.connect("barber.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE appointments SET status='approved' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    

    return redirect("/admin")


@app.route("/reject/<int:id>")
def reject(id):

    conn = sqlite3.connect("barber.db")
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE appointments SET status='rejected' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


@app.route("/status")
def status_page():
    return render_template("status.html")



@app.route("/check-status", methods=["POST"])
def check_status():

    phone = request.form.get("phone")

    conn = sqlite3.connect("barber.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM appointments WHERE phone = ?",
        (phone,)
    )

    booking = cursor.fetchone()

    conn.close()

    if booking:
        return render_template(
            "result.html",
            booking=booking
        )

    return "No booking found ❌"

@app.route("/gallery")
def gallery():

    conn = sqlite3.connect("barber.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM styles")

    styles = cursor.fetchall()

    conn.close()

    return render_template(
        "gallery.html",
        styles=styles
    )

@app.route("/stats")
def stats():

    conn = sqlite3.connect("barber.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM appointments")
    total = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM appointments WHERE status='approved'"
    )
    approved = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM appointments WHERE status='pending'"
    )
    pending = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM appointments WHERE status='rejected'"
    )
    rejected = cursor.fetchone()[0]



    cursor.execute("""
        SELECT service, COUNT(*)
        FROM appointments
        GROUP BY service
        ORDER BY COUNT(*) DESC
        LIMIT 1
    """)

    popular_style = cursor.fetchone()
    conn.close()

    return render_template(
    "stats.html",
    total=total,
    approved=approved,
    pending=pending,
    rejected=rejected,
    popular_style=popular_style
    )

@app.route("/upload")
def upload():

    if not session.get("logged_in"):
        return redirect("/login")

    return render_template("upload.html")
    
@app.route("/upload", methods=["POST"])
def upload_post():

    file = request.files["image"]
    
    title = request.form.get("title")
    price = request.form.get("price")
    description = request.form.get("description")

    filename = secure_filename(file.filename)

    file.save(
        os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )
    )

    conn = sqlite3.connect("barber.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO styles
    (image, title, price, description)
    VALUES (?, ?, ?, ?)
    """, (
        filename,
        title,
        price,
        description
    ))

    conn.commit()
    conn.close()

    return redirect("/gallery")


@app.route("/delete-image/<filename>")
def delete_image(filename):

    os.remove(
        os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )
    )

    return redirect("/gallery")


conn = sqlite3.connect("barber.db")
cursor = conn.cursor()

cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
)

print(cursor.fetchall())

conn.close()




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    
    
