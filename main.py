from flask import Flask, request, jsonify, render_template
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)


# =========================
# MYSQL DATABASE CONNECTION
# =========================

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="24FF1A0514",
        database="CampusCare"
    )


# =========================
# CREATE USERS TABLE
# =========================

def create_users_table():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                student_id VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(150) NOT NULL UNIQUE,
                department VARCHAR(50) NOT NULL,
                year VARCHAR(20) NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()

        print("Users table is ready.")

    except Error as e:
        print("Database error:", e)


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    full_name = data.get("full_name", "").strip()
    student_id = data.get("student_id", "").strip()
    email = data.get("email", "").strip()
    department = data.get("department", "").strip()
    year = data.get("year", "").strip()
    password = data.get("password", "")

    if not all([
        full_name,
        student_id,
        email,
        department,
        year,
        password
    ]):
        return jsonify({
            "success": False,
            "message": "Please fill all fields."
        }), 400

    if len(password) < 6:
        return jsonify({
            "success": False,
            "message": "Password must be at least 6 characters."
        }), 400

    password_hash = generate_password_hash(password)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users
            (full_name, student_id, email, department, year, password)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            full_name,
            student_id,
            email,
            department,
            year,
            password_hash
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Account created successfully."
        })

    except mysql.connector.IntegrityError:
        return jsonify({
            "success": False,
            "message": "Student ID or email already exists."
        }), 409

    except Error as e:
        print("Database error:", e)

        return jsonify({
            "success": False,
            "message": "Database error."
        }), 500


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    identifier = data.get("identifier", "").strip()
    password = data.get("password", "")

    if not identifier or not password:
        return jsonify({
            "success": False,
            "message": "Please enter your login details."
        }), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM users
            WHERE email = %s OR student_id = %s
            LIMIT 1
        """, (identifier, identifier))

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user is None:
            return jsonify({
                "success": False,
                "message": "Invalid email/Student ID or password."
            }), 401

        if not check_password_hash(user["password"], password):
            return jsonify({
                "success": False,
                "message": "Invalid email/Student ID or password."
            }), 401

        return jsonify({
            "success": True,
            "message": "Login successful.",
            "user": {
                "id": user["id"],
                "name": user["full_name"],
                "student_id": user["student_id"],
                "email": user["email"],
                "department": user["department"],
                "year": user["year"]
            }
        })

    except Error as e:
        print("Database error:", e)

        return jsonify({
            "success": False,
            "message": "Database connection error."
        }), 500

@app.route("/report", methods=["POST"])
def create_report():
    data = request.get_json()

    student_id = data.get("student_id", "").strip()
    issue_title = data.get("issue_title", "").strip()
    category = data.get("category", "").strip()
    location = data.get("location", "").strip()
    description = data.get("description", "").strip()
    priority = data.get("priority", "Medium").strip()

    if not all([
        student_id,
        issue_title,
        category,
        location,
        description,
        priority
    ]):
        return jsonify({
            "success": False,
            "message": "Please fill all required fields."
        }), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create ticket ID
        cursor.execute("SELECT id FROM reports ORDER BY id DESC LIMIT 1")
        last_report = cursor.fetchone()

        if last_report:
            next_number = last_report[0] + 1
        else:
            next_number = 1

        ticket_id = f"CC-{next_number:04d}"

        cursor.execute("""
            INSERT INTO reports
            (
                ticket_id,
                student_id,
                issue_title,
                category,
                location,
                description,
                priority,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            ticket_id,
            student_id,
            issue_title,
            category,
            location,
            description,
            priority,
            "Pending"
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Report submitted successfully.",
            "ticket_id": ticket_id
        })

    except Error as e:
        print("Report database error:", e)

        return jsonify({
            "success": False,
            "message": "Unable to save report."
        }), 500
# =========================
# HOME
# =========================

@app.route("/")
def home():
    return render_template("campuslogin.html")

# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# =========================
# REPORT ISSUE PAGE
# =========================

@app.route("/report-issue")
def report_issue():
    return render_template("report-issue.html")


# =========================
# MY REPORTS PAGE
# =========================

@app.route("/Myreports.html")
def my_reports_page():
    return render_template("Myreports.html")
# =========================
# TRACK STATUS PAGE
# =========================

@app.route("/track.html")
def track_status_page():
    return render_template("track.html")


@app.route("/analytics.html")
def analytics_page():
    return render_template("analytics.html")

@app.route("/profile")
def profile_page():
    return render_template("profile.html")

@app.route("/notifications")
def notifications_page():
    return render_template("notifications.html")

@app.route("/settings")
def settings_page():
    return render_template("settings.html")

# TRACK STATUS API
@app.route('/track-status', methods=['GET'])
def track_status():
    student_id = request.args.get('student_id')

    if not student_id:
        return jsonify({
            "success": False,
            "message": "Student ID is required"
        }), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                ticket_id,
                issue_title,
                category,
                location,
                priority,
                status,
                created_at
            FROM reports
            WHERE student_id = %s
            ORDER BY created_at DESC
        """, (student_id,))

        reports = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "reports": reports
        })

    except Error as e:
        print("Track Status database error:", e)

        return jsonify({
            "success": False,
            "message": "Unable to load track status."
        }), 500


# =========================
# MY REPORTS API
# =========================

@app.route('/my-reports', methods=['GET'])
def my_reports():
    student_id = request.args.get('student_id')

    if not student_id:
        return jsonify({
            "success": False,
            "message": "Student ID is required"
        }), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                ticket_id,
                issue_title,
                category,
                location,
                priority,
                status,
                created_at
            FROM reports
            WHERE student_id = %s
            ORDER BY created_at DESC
        """, (student_id,))

        reports = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "reports": reports
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

# =========================
# ANALYTICS API
# =========================

@app.route("/analytics-data", methods=["GET"])
def analytics_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Total reports
        cursor.execute("SELECT COUNT(*) AS total FROM reports")
        total = cursor.fetchone()["total"]

        # Status counts
        cursor.execute("""
            SELECT status, COUNT(*) AS count
            FROM reports
            GROUP BY status
        """)
        status_rows = cursor.fetchall()

        pending = 0
        in_progress = 0
        resolved = 0

        for row in status_rows:
            status = str(row["status"]).lower().strip()

            if status == "pending":
                pending = row["count"]
            elif status in ["in progress", "in_progress"]:
                in_progress = row["count"]
            elif status == "resolved":
                resolved = row["count"]

        # Resolution rate
        resolution_rate = round(
            (resolved / total) * 100
        ) if total > 0 else 0

        # Category counts
        cursor.execute("""
            SELECT category, COUNT(*) AS count
            FROM reports
            GROUP BY category
            ORDER BY count DESC
        """)
        category_rows = cursor.fetchall()

        categories = [
            {
                "name": row["category"],
                "count": row["count"]
            }
            for row in category_rows
        ]

        # Top locations
        cursor.execute("""
            SELECT location, COUNT(*) AS count
            FROM reports
            GROUP BY location
            ORDER BY count DESC
            LIMIT 5
        """)
        location_rows = cursor.fetchall()

        locations = [
            {
                "name": row["location"],
                "count": row["count"]
            }
            for row in location_rows
        ]

        # Last 7 days trend
        cursor.execute("""
            SELECT
                DATE(created_at) AS report_date,
                COUNT(*) AS total,
                SUM(CASE WHEN LOWER(status) = 'pending' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN LOWER(status) = 'resolved' THEN 1 ELSE 0 END) AS resolved
            FROM reports
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
            GROUP BY DATE(created_at)
            ORDER BY report_date
        """)

        trend_rows = cursor.fetchall()

        trend = []

        for row in trend_rows:
            trend.append({
                "date": str(row["report_date"]),
                "total": row["total"],
                "pending": row["pending"] or 0,
                "resolved": row["resolved"] or 0
            })

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "resolved": resolved,
            "resolution_rate": resolution_rate,
            "categories": categories,
            "locations": locations,
            "trend": trend
        })

    except Error as e:
        print("Analytics database error:", e)

        return jsonify({
            "success": False,
            "message": "Unable to load analytics data."
        }), 500

# =========================
# NOTIFICATIONS API
# =========================

@app.route("/notifications-data", methods=["GET"])
def notifications_data():

    student_id = request.args.get("student_id")

    if not student_id:
        return jsonify({
            "success": False,
            "message": "Student ID is required."
        }), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                title,
                message,
                notification_type,
                is_read,
                created_at
            FROM notifications
            WHERE student_id = %s
            ORDER BY created_at DESC
        """, (student_id,))

        notifications = cursor.fetchall()

        cursor.close()
        conn.close()

        for notification in notifications:
            if notification["created_at"]:
                notification["created_at"] = (
                    notification["created_at"]
                    .strftime("%Y-%m-%d %H:%M:%S")
                )

        return jsonify({
            "success": True,
            "notifications": notifications
        })

    except Error as e:

        print("Notifications database error:", e)

        return jsonify({
            "success": False,
            "message": "Unable to load notifications."
        }), 500


# =========================
# MARK ONE NOTIFICATION READ
# =========================

@app.route(
    "/notifications/<int:notification_id>/read",
    methods=["POST"]
)
def mark_notification_read(notification_id):

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE notifications
            SET is_read = 1
            WHERE id = %s
        """, (notification_id,))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Notification marked as read."
        })

    except Error as e:

        print("Mark notification read error:", e)

        return jsonify({
            "success": False,
            "message": "Unable to update notification."
        }), 500


# =========================
# DELETE NOTIFICATION
# =========================

@app.route(
    "/notifications/<int:notification_id>",
    methods=["DELETE"]
)
def delete_notification(notification_id):

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM notifications
            WHERE id = %s
        """, (notification_id,))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Notification deleted."
        })

    except Error as e:

        print("Delete notification error:", e)

        return jsonify({
            "success": False,
            "message": "Unable to delete notification."
        }), 500


# =========================
# MARK ALL NOTIFICATIONS READ
# =========================

@app.route(
    "/notifications/mark-all-read",
    methods=["POST"]
)
def mark_all_notifications_read():

    data = request.get_json() or {}

    student_id = data.get("student_id", "").strip()

    if not student_id:
        return jsonify({
            "success": False,
            "message": "Student ID is required."
        }), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE notifications
            SET is_read = 1
            WHERE student_id = %s
        """, (student_id,))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "All notifications marked as read."
        })

    except Error as e:

        print("Mark all notifications error:", e)

        return jsonify({
            "success": False,
            "message": "Unable to update notifications."
        }), 500
# =========================
# SETTINGS - GET USER
# =========================

@app.route("/settings/user", methods=["GET"])
def get_settings_user():

    student_id = request.args.get("student_id", "").strip()

    if not student_id:
        return jsonify({
            "success": False,
            "message": "Student ID is required."
        }), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                full_name,
                student_id,
                email,
                department,
                year
            FROM users
            WHERE student_id = %s
            LIMIT 1
        """, (student_id,))

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if not user:
            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404

        return jsonify({
            "success": True,
            "user": user
        })

    except Error as e:
        print("Settings user error:", e)

        return jsonify({
            "success": False,
            "message": "Unable to load user details."
        }), 500


# =========================
# SETTINGS - UPDATE PROFILE
# =========================

@app.route("/settings/update-profile", methods=["POST"])
def update_profile():

    data = request.get_json() or {}

    student_id = data.get("student_id", "").strip()
    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip()
    department = data.get("department", "").strip()
    year = data.get("year", "").strip()

    if not student_id:
        return jsonify({
            "success": False,
            "message": "Student ID is required."
        }), 400

    if not full_name or not email or not department or not year:
        return jsonify({
            "success": False,
            "message": "Please fill all profile fields."
        }), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET
                full_name = %s,
                email = %s,
                department = %s,
                year = %s
            WHERE student_id = %s
        """, (
            full_name,
            email,
            department,
            year,
            student_id
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Profile updated successfully."
        })

    except mysql.connector.IntegrityError:
        return jsonify({
            "success": False,
            "message": "This email is already being used."
        }), 409

    except Error as e:
        print("Update profile error:", e)

        return jsonify({
            "success": False,
            "message": "Unable to update profile."
        }), 500


# =========================
# SETTINGS - CHANGE PASSWORD
# =========================

@app.route("/settings/change-password", methods=["POST"])
def change_password():

    data = request.get_json() or {}

    student_id = data.get("student_id", "").strip()
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")
    confirm_password = data.get("confirm_password", "")

    if not student_id:
        return jsonify({
            "success": False,
            "message": "Student ID is required."
        }), 400

    if not current_password or not new_password or not confirm_password:
        return jsonify({
            "success": False,
            "message": "Please fill all password fields."
        }), 400

    if new_password != confirm_password:
        return jsonify({
            "success": False,
            "message": "New passwords do not match."
        }), 400

    if len(new_password) < 6:
        return jsonify({
            "success": False,
            "message": "New password must be at least 6 characters."
        }), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT password
            FROM users
            WHERE student_id = %s
            LIMIT 1
        """, (student_id,))

        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()

            return jsonify({
                "success": False,
                "message": "User not found."
            }), 404

        if not check_password_hash(
            user["password"],
            current_password
        ):
            cursor.close()
            conn.close()

            return jsonify({
                "success": False,
                "message": "Current password is incorrect."
            }), 401

        new_password_hash = generate_password_hash(new_password)

        cursor.execute("""
            UPDATE users
            SET password = %s
            WHERE student_id = %s
        """, (
            new_password_hash,
            student_id
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Password changed successfully."
        })

    except Error as e:
        print("Change password error:", e)

        return jsonify({
            "success": False,
            "message": "Unable to change password."
        }), 500
# =========================
# START SERVER
# =========================

if __name__ == "__main__":
    create_users_table()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )