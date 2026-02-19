# 🚀 Student Portfolio Website

A **professional, full-featured portfolio website** built with Python Flask + SQLite.  
Supports **Light & Dark mode**, full admin panel, image uploads, and more.

---

## 📁 Project Structure

```
portfolio_app/
├── app.py                    ← Main Flask application
├── requirements.txt          ← Python dependencies
├── templates/
│   ├── base.html             ← Public base layout
│   ├── index.html            ← Main portfolio page
│   ├── setup.html            ← First-time setup page
│   └── admin/
│       ├── base.html         ← Admin sidebar layout
│       ├── login.html        ← Admin login
│       ├── dashboard.html    ← Stats overview
│       ├── personal.html     ← Edit personal info
│       ├── education.html    ← Manage education
│       ├── experience.html   ← Manage experience
│       ├── projects.html     ← Manage projects
│       ├── project_edit.html ← Edit a project
│       └── certificates.html ← Manage certificates
└── static/
    └── uploads/              ← Auto-created on first upload
        ├── profile/
        ├── projects/
        ├── certificates/
        ├── education/
        └── experience/
```

---

## ⚙️ Setup & Run

### 1. Install Python 3.10+

### 2. Create virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate      # Linux / Mac
venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
python app.py
```

### 5. Open in browser
```
http://localhost:5000          ← Portfolio (public)
http://localhost:5000/admin    ← Admin Panel
```

---

## 🔑 Default Admin Login

| Field    | Value      |
|----------|------------|
| Username | `admin`    |
| Password | `admin123` |

> ⚠️ **Change the password** in `app.py` after first login for security.

---

## ✨ Features

### Public Portfolio
- 🌓 Light & Dark mode toggle (persists across sessions)
- 🦸 Hero section with profile photo, name, tagline, social links
- 📖 About section with skills tags and stats
- 🎓 Education timeline with logos and grades
- 💼 Work experience with company logos
- 💻 Projects with image, tech stack, GitHub/Live links, category filter
- 🏆 Certificates with image lightbox, verification links, category filter
- 📬 Contact section with social links
- 📱 Fully responsive mobile layout

### Admin Panel
- 🔐 Secure login with hashed passwords
- 📊 Dashboard with quick stats
- 👤 Personal info — name, tagline, bio, photo, social links, skills
- 🎓 Education — add/delete with logos, grades, dates
- 💼 Experience — add/delete with logos, current job badge
- 💻 Projects — add/edit/delete with images, featured flag, category
- 🏆 Certificates — add/delete with images, credential ID, verification URL

---

## 🗄️ Database

SQLite database (`portfolio.db`) is auto-created on first run.  
Tables: `admin`, `student`, `education`, `experience`, `project`, `certificate`

---

## 🎨 Customization

Edit CSS variables in `templates/base.html` under `:root` and `[data-theme="dark"]`:

```css
--accent: #c8621a;      /* Primary color — change to your brand color */
--font-display: 'Playfair Display', serif;
--font-body: 'DM Sans', sans-serif;
```

---

## 🚀 Deploy to Production

For production deployment:

```bash
pip install gunicorn
gunicorn -w 4 app:app
```

Or deploy to **Railway**, **Render**, **Heroku**, or **PythonAnywhere**.
