from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import sqlite3, os, json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'portfolio_secret_key_2024'
app.config['DATABASE'] = 'portfolio.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db: db.close()

def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv

def execute(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid

def init_db():
    with app.app_context():
        db = get_db()
        db.executescript('''
            CREATE TABLE IF NOT EXISTS admin (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS student (id INTEGER PRIMARY KEY, name TEXT NOT NULL, tagline TEXT, email TEXT, phone TEXT, location TEXT, about TEXT, profile_image TEXT, github TEXT, linkedin TEXT, twitter TEXT, website TEXT, resume TEXT, skills TEXT);
            CREATE TABLE IF NOT EXISTS education (id INTEGER PRIMARY KEY, student_id INTEGER NOT NULL, degree TEXT NOT NULL, institution TEXT NOT NULL, field TEXT, start_year TEXT, end_year TEXT, grade TEXT, description TEXT, logo TEXT);
            CREATE TABLE IF NOT EXISTS project (id INTEGER PRIMARY KEY, student_id INTEGER NOT NULL, title TEXT NOT NULL, description TEXT, tech_stack TEXT, image TEXT, github_link TEXT, live_link TEXT, category TEXT, featured INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS certificate (id INTEGER PRIMARY KEY, student_id INTEGER NOT NULL, title TEXT NOT NULL, issuer TEXT, date TEXT, credential_id TEXT, credential_url TEXT, image TEXT, category TEXT);
            CREATE TABLE IF NOT EXISTS experience (id INTEGER PRIMARY KEY, student_id INTEGER NOT NULL, role TEXT NOT NULL, company TEXT NOT NULL, start_date TEXT, end_date TEXT, current INTEGER DEFAULT 0, description TEXT, logo TEXT);
        ''')
        existing = db.execute('SELECT id FROM admin WHERE username=?', ('admin',)).fetchone()
        if not existing:
            db.execute('INSERT INTO admin (username,password) VALUES (?,?)', ('admin', generate_password_hash('admin123')))
            db.commit()

def allowed_file(f):
    return '.' in f and f.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file, subfolder):
    if file and file.filename and allowed_file(file.filename):
        fn = secure_filename(file.filename)
        ts = datetime.now().strftime('%Y%m%d%H%M%S')
        fn = f"{ts}_{fn}"
        path = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
        os.makedirs(path, exist_ok=True)
        file.save(os.path.join(path, fn))
        return f"uploads/{subfolder}/{fn}"
    return None

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please login first.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def rd(row): return dict(row) if row else None
def rl(rows): return [dict(r) for r in rows]

@app.route('/')
def index():
    student = rd(query('SELECT * FROM student LIMIT 1', one=True))
    if not student: return render_template('setup.html')
    sid = student['id']
    projects = rl(query('SELECT * FROM project WHERE student_id=?', (sid,)))
    certificates = rl(query('SELECT * FROM certificate WHERE student_id=?', (sid,)))
    education = rl(query('SELECT * FROM education WHERE student_id=?', (sid,)))
    experience = rl(query('SELECT * FROM experience WHERE student_id=?', (sid,)))
    skills = json.loads(student['skills']) if student.get('skills') else []
    categories = list(set(p['category'] for p in projects if p.get('category')))
    cert_categories = list(set(c['category'] for c in certificates if c.get('category')))
    return render_template('index.html', student=student, projects=projects, certificates=certificates, education=education, experience=experience, skills=skills, categories=categories, cert_categories=cert_categories)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        admin = rd(query('SELECT * FROM admin WHERE username=?', (request.form['username'],), one=True))
        if admin and check_password_hash(admin['password'], request.form['password']):
            session['admin_id'] = admin['id']
            flash('Welcome back!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials.', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    student = rd(query('SELECT * FROM student LIMIT 1', one=True))
    stats = {
        'projects': query('SELECT COUNT(*) as n FROM project', one=True)['n'],
        'certificates': query('SELECT COUNT(*) as n FROM certificate', one=True)['n'],
        'education': query('SELECT COUNT(*) as n FROM education', one=True)['n'],
        'experience': query('SELECT COUNT(*) as n FROM experience', one=True)['n'],
    }
    return render_template('admin/dashboard.html', student=student, stats=stats)

@app.route('/admin/personal', methods=['GET', 'POST'])
@login_required
def admin_personal():
    student = rd(query('SELECT * FROM student LIMIT 1', one=True))
    if request.method == 'POST':
        skills_list = [s.strip() for s in request.form.get('skills', '').split(',') if s.strip()]
        profile_img = save_file(request.files.get('profile_image'), 'profile')
        f = request.form
        if not student:
            execute('INSERT INTO student (name,tagline,email,phone,location,about,github,linkedin,twitter,website,skills) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                    (f['name'],f.get('tagline'),f.get('email'),f.get('phone'),f.get('location'),f.get('about'),f.get('github'),f.get('linkedin'),f.get('twitter'),f.get('website'),json.dumps(skills_list)))
        else:
            if profile_img:
                execute('UPDATE student SET name=?,tagline=?,email=?,phone=?,location=?,about=?,github=?,linkedin=?,twitter=?,website=?,skills=?,profile_image=? WHERE id=?',
                        (f['name'],f.get('tagline'),f.get('email'),f.get('phone'),f.get('location'),f.get('about'),f.get('github'),f.get('linkedin'),f.get('twitter'),f.get('website'),json.dumps(skills_list),profile_img,student['id']))
            else:
                execute('UPDATE student SET name=?,tagline=?,email=?,phone=?,location=?,about=?,github=?,linkedin=?,twitter=?,website=?,skills=? WHERE id=?',
                        (f['name'],f.get('tagline'),f.get('email'),f.get('phone'),f.get('location'),f.get('about'),f.get('github'),f.get('linkedin'),f.get('twitter'),f.get('website'),json.dumps(skills_list),student['id']))
        flash('Personal details updated!', 'success')
        return redirect(url_for('admin_personal'))
    return render_template('admin/personal.html', student=student)

@app.route('/admin/education')
@login_required
def admin_education():
    student = rd(query('SELECT * FROM student LIMIT 1', one=True))
    items = rl(query('SELECT * FROM education WHERE student_id=?', (student['id'],))) if student else []
    return render_template('admin/education.html', items=items, student=student)

@app.route('/admin/education/add', methods=['POST'])
@login_required
def admin_education_add():
    student = rd(query('SELECT * FROM student LIMIT 1', one=True))
    logo = save_file(request.files.get('logo'), 'education')
    f = request.form
    execute('INSERT INTO education (student_id,degree,institution,field,start_year,end_year,grade,description,logo) VALUES (?,?,?,?,?,?,?,?,?)',
            (student['id'],f['degree'],f['institution'],f.get('field'),f.get('start_year'),f.get('end_year'),f.get('grade'),f.get('description'),logo))
    flash('Education added!', 'success')
    return redirect(url_for('admin_education'))

@app.route('/admin/education/delete/<int:id>')
@login_required
def admin_education_delete(id):
    execute('DELETE FROM education WHERE id=?', (id,))
    flash('Education deleted.', 'success')
    return redirect(url_for('admin_education'))

@app.route('/admin/projects')
@login_required
def admin_projects():
    student = rd(query('SELECT * FROM student LIMIT 1', one=True))
    projects = rl(query('SELECT * FROM project WHERE student_id=?', (student['id'],))) if student else []
    return render_template('admin/projects.html', projects=projects, student=student)

@app.route('/admin/projects/add', methods=['POST'])
@login_required
def admin_projects_add():
    student = rd(query('SELECT * FROM student LIMIT 1', one=True))
    img = save_file(request.files.get('image'), 'projects')
    f = request.form
    execute('INSERT INTO project (student_id,title,description,tech_stack,image,github_link,live_link,category,featured) VALUES (?,?,?,?,?,?,?,?,?)',
            (student['id'],f['title'],f.get('description'),f.get('tech_stack'),img,f.get('github_link'),f.get('live_link'),f.get('category'),1 if 'featured' in f else 0))
    flash('Project added!', 'success')
    return redirect(url_for('admin_projects'))

@app.route('/admin/projects/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_projects_edit(id):
    proj = rd(query('SELECT * FROM project WHERE id=?', (id,), one=True))
    if request.method == 'POST':
        img = save_file(request.files.get('image'), 'projects')
        f = request.form
        featured = 1 if 'featured' in f else 0
        if img:
            execute('UPDATE project SET title=?,description=?,tech_stack=?,github_link=?,live_link=?,category=?,featured=?,image=? WHERE id=?',
                    (f['title'],f.get('description'),f.get('tech_stack'),f.get('github_link'),f.get('live_link'),f.get('category'),featured,img,id))
        else:
            execute('UPDATE project SET title=?,description=?,tech_stack=?,github_link=?,live_link=?,category=?,featured=? WHERE id=?',
                    (f['title'],f.get('description'),f.get('tech_stack'),f.get('github_link'),f.get('live_link'),f.get('category'),featured,id))
        flash('Project updated!', 'success')
        return redirect(url_for('admin_projects'))
    return render_template('admin/project_edit.html', proj=proj)

@app.route('/admin/projects/delete/<int:id>')
@login_required
def admin_projects_delete(id):
    execute('DELETE FROM project WHERE id=?', (id,))
    flash('Project deleted.', 'success')
    return redirect(url_for('admin_projects'))

@app.route('/admin/certificates')
@login_required
def admin_certificates():
    student = rd(query('SELECT * FROM student LIMIT 1', one=True))
    certs = rl(query('SELECT * FROM certificate WHERE student_id=?', (student['id'],))) if student else []
    return render_template('admin/certificates.html', certs=certs, student=student)

@app.route('/admin/certificates/add', methods=['POST'])
@login_required
def admin_certificates_add():
    student = rd(query('SELECT * FROM student LIMIT 1', one=True))
    img = save_file(request.files.get('image'), 'certificates')
    f = request.form
    execute('INSERT INTO certificate (student_id,title,issuer,date,credential_id,credential_url,image,category) VALUES (?,?,?,?,?,?,?,?)',
            (student['id'],f['title'],f.get('issuer'),f.get('date'),f.get('credential_id'),f.get('credential_url'),img,f.get('category')))
    flash('Certificate added!', 'success')
    return redirect(url_for('admin_certificates'))

@app.route('/admin/certificates/delete/<int:id>')
@login_required
def admin_certificates_delete(id):
    execute('DELETE FROM certificate WHERE id=?', (id,))
    flash('Certificate deleted.', 'success')
    return redirect(url_for('admin_certificates'))

@app.route('/admin/experience')
@login_required
def admin_experience():
    student = rd(query('SELECT * FROM student LIMIT 1', one=True))
    items = rl(query('SELECT * FROM experience WHERE student_id=?', (student['id'],))) if student else []
    return render_template('admin/experience.html', items=items, student=student)

@app.route('/admin/experience/add', methods=['POST'])
@login_required
def admin_experience_add():
    student = rd(query('SELECT * FROM student LIMIT 1', one=True))
    logo = save_file(request.files.get('logo'), 'experience')
    f = request.form
    execute('INSERT INTO experience (student_id,role,company,start_date,end_date,current,description,logo) VALUES (?,?,?,?,?,?,?,?)',
            (student['id'],f['role'],f['company'],f.get('start_date'),f.get('end_date'),1 if 'current' in f else 0,f.get('description'),logo))
    flash('Experience added!', 'success')
    return redirect(url_for('admin_experience'))

@app.route('/admin/experience/delete/<int:id>')
@login_required
def admin_experience_delete(id):
    execute('DELETE FROM experience WHERE id=?', (id,))
    flash('Experience deleted.', 'success')
    return redirect(url_for('admin_experience'))

if __name__ == '__main__':
    for d in ['profile','projects','certificates','education','experience']:
        os.makedirs(f'static/uploads/{d}', exist_ok=True)
    init_db()
    app.run(debug=True, port=5000)
