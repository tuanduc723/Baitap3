from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key để quản lý session

# Cấu hình kết nối database
DB_CONFIG = {
    'dbname': 'students',
    'host': 'localhost',
    'port': '5432',
    'user': 'postgres',
    'password': '12345'
}

# Hàm kết nối cơ sở dữ liệu
def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_CONFIG['dbname'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port']
        )
        return conn
    except Exception as e:
        print("Connection failed:", e)
        return None

# Route trang chủ
@app.route('/')
def home():
    return render_template('home.html')

# Route đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Xác thực người dùng từ bảng users
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            session['username'] = username
            return redirect(url_for('student_management'))
        else:
            flash("Đăng nhập thất bại. Vui lòng thử lại!", "danger")
    
    return render_template('login.html')

# Route đăng ký
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        cur.close()
        conn.close()
        
        flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Route quên mật khẩu
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user:
            flash("Liên hệ admin để khôi phục mật khẩu.", "info")
        else:
            flash("Tên người dùng không tồn tại.", "danger")
    
    return render_template('forgot_password.html')

# Route quản lý sinh viên
@app.route('/student_management', methods=['GET', 'POST'])
def student_management():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        flash("Không thể kết nối tới cơ sở dữ liệu", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        major = request.form.get('major')
        action = request.form.get('action')

        cur = conn.cursor()
        try:
            if action == 'add':
                cur.execute(
                    "INSERT INTO students (name, age, gender, major) VALUES (%s, %s, %s, %s)",
                    (name, age, gender, major)
                )
                flash("Sinh viên đã được thêm!", "success")
            elif action == 'update':
                cur.execute(
                    "UPDATE students SET name=%s, age=%s, gender=%s, major=%s WHERE id=%s",
                    (name, age, gender, major, student_id)
                )
                flash("Thông tin sinh viên đã được cập nhật!", "success")
            elif action == 'delete':
                cur.execute("DELETE FROM students WHERE id=%s", (student_id,))
                flash("Sinh viên đã được xóa!", "success")

            conn.commit()
        except Exception as e:
            conn.rollback()
            flash(f"Đã xảy ra lỗi: {str(e)}", "danger")
        finally:
            cur.close()

    cur = conn.cursor()
    cur.execute("SELECT * FROM students")
    students = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('student_management.html', students=students)

# Route quản lý chuyên ngành
@app.route('/major_management', methods=['GET', 'POST'])
def major_management():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        flash("Không thể kết nối tới cơ sở dữ liệu", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        major_id = request.form.get('major_id')
        name = request.form.get('name')
        action = request.form.get('action')

        cur = conn.cursor()
        try:
            if action == 'add':
                cur.execute("INSERT INTO majors (name) VALUES (%s)", (name,))
                flash("Chuyên ngành đã được thêm!", "success")
            elif action == 'update':
                cur.execute("UPDATE majors SET name=%s WHERE id=%s", (name, major_id))
                flash("Chuyên ngành đã được cập nhật!", "success")
            elif action == 'delete':
                cur.execute("DELETE FROM majors WHERE id=%s", (major_id,))
                flash("Chuyên ngành đã được xóa!", "success")

            conn.commit()
        except Exception as e:
            conn.rollback()
            flash(f"Đã xảy ra lỗi: {str(e)}", "danger")
        finally:
            cur.close()

    cur = conn.cursor()
    cur.execute("SELECT * FROM majors")
    majors = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('major_management.html', majors=majors)

# Route đăng xuất
@app.route('/logout')
def logout():
    session.clear()
    flash("Đã đăng xuất!", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
