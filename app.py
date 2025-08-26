from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
import os, sqlite3
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
DB_PATH = os.path.join(BASE_DIR, 'products.db')

ALLOWED_EXT = {'png','jpg','jpeg','gif'}

app = Flask(__name__)
app.secret_key = 'change_this_to_a_random_secret_in_production'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 8MB

# --- Database helpers ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price TEXT NOT NULL,
        description TEXT,
        image TEXT
    )''')
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

# Initialize DB
init_db()

# --- Routes ---
@app.route('/')
def index():
    conn = get_db()
    products = conn.execute('SELECT * FROM products ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', products=products)

@app.route('/admin', methods=['GET','POST'])
def admin():
    # Simple session-based admin -- username Ben / password Ben1234
    if request.method == 'POST':
        username = request.form.get('username','')
        password = request.form.get('password','')
        if username == 'Ben' and password == 'Ben1234':
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash('Taarifa za admin si sahihi', 'error')
            return redirect(url_for('admin'))
    return render_template('admin.html')

@app.route('/admin/panel', methods=['GET','POST'])
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    conn = get_db()
    products = conn.execute('SELECT * FROM products ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin_panel.html', products=products)

@app.route('/upload-product', methods=['POST'])
def upload_product():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    name = request.form.get('name','').strip()
    price = request.form.get('price','').strip()
    description = request.form.get('description','').strip()
    file = request.files.get('image')
    filename = None
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        dest = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(dest)
        # store relative path for template compatibility
        filename = 'static/uploads/' + filename
    conn = get_db()
    conn.execute('INSERT INTO products (name, price, description, image) VALUES (?,?,?,?)', (name, price, description, filename))
    conn.commit()
    conn.close()
    flash('Bidhaa imeongezwa', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Run in debug mode for local testing
    app.run(host='0.0.0.0', port=5000, debug=True)