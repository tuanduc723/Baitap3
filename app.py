from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Cấu hình kết nối cơ sở dữ liệu
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
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print("Kết nối thất bại:", e)
        return None

# Route đăng ký tài khoản
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        if conn is None:
            flash("Không thể kết nối tới cơ sở dữ liệu", "danger")
            return redirect(url_for('register'))

        cur = conn.cursor()
        # Kiểm tra xem tên người dùng đã tồn tại chưa
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            flash("Tên người dùng đã tồn tại, vui lòng chọn tên khác", "danger")
        else:
            # Thêm người dùng mới
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            session['username'] = username
            flash("Đăng ký thành công! Bạn đã đăng nhập.", "success")
            return redirect(url_for('student_management'))
        cur.close()
        conn.close()

    return render_template('register.html')

# Route quên mật khẩu
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']

        conn = get_db_connection()
        if conn is None:
            flash("Không thể kết nối tới cơ sở dữ liệu", "danger")
            return redirect(url_for('forgot_password'))

        cur = conn.cursor()
        # Lấy mật khẩu của người dùng
        cur.execute("SELECT password FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        if user:
            flash(f"Mật khẩu của bạn là: {user[0]}", "info")
        else:
            flash("Không tìm thấy tên người dùng", "danger")
        cur.close()
        conn.close()

    return render_template('forgot_password.html')

# Route đăng nhập
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        if conn is None:
            flash("Không thể kết nối tới cơ sở dữ liệu", "danger")
            return redirect(url_for('login'))

        cur = conn.cursor()
        # Xác thực người dùng
        cur.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cur.fetchone()
        if user:
            session['username'] = username
            return redirect(url_for('student_management'))
        else:
            flash("Đăng nhập thất bại. Vui lòng thử lại!", "danger")
        cur.close()
        conn.close()

    return render_template('login.html')

# Route quản lý sinh viên
@app.route('/student_management', methods=['GET', 'POST'])
def student_management():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        flash("Không thể kết nối tới cơ sở dữ liệu", "danger")
        return redirect(url_for('login'))

    cur = conn.cursor()

    if request.method == 'POST':
        student_id = request.form.get('student_id')
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        major = request.form.get('major')
        action = request.form.get('action')

        try:
            if action == 'add' and name:
                cur.execute(
                    "INSERT INTO students (name, age, gender, major) VALUES (%s, %s, %s, %s)",
                    (name, age, gender, major)
                )
                flash("Sinh viên đã được thêm!", "success")
            elif action == 'update' and student_id and name:
                cur.execute(
                    "UPDATE students SET name=%s, age=%s, gender=%s, major=%s WHERE id=%s",
                    (name, age, gender, major, student_id)
                )
                flash("Thông tin sinh viên đã được cập nhật!", "success")
            elif action == 'delete' and student_id:
                cur.execute("DELETE FROM students WHERE id=%s", (student_id,))
                flash("Sinh viên đã được xóa!", "success")
            conn.commit()
        except Exception as e:
            conn.rollback()
            flash(f"Đã xảy ra lỗi: {str(e)}", "danger")

    # Xử lý tìm kiếm
    search_query = request.args.get('search', '').strip()
    if search_query:
        cur.execute("""
            SELECT * FROM students 
            WHERE name ILIKE %s OR major ILIKE %s
        """, (f"%{search_query}%", f"%{search_query}%"))
    else:
        cur.execute("SELECT * FROM students")
    
    students = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('student_management.html', students=students)

# Route đăng xuất
@app.route('/logout')
def logout():
    session.clear()
    flash("Đã đăng xuất!", "info")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
