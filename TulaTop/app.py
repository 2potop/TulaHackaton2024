from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "your_secure_random_secret_key"
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    with sqlite3.connect('health_monitoring.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                snils TEXT UNIQUE NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                blood_pressure TEXT,
                heart_rate INTEGER,
                medication_schedule TEXT,
                recommendations TEXT,
                FOREIGN KEY (patient_id) REFERENCES users (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                age INTEGER,
                gender TEXT,
                general_feeling TEXT,
                symptom_start_date TEXT,
                symptoms TEXT,
                fever TEXT,
                cough TEXT,
                sore_throat TEXT,
                breathing_difficulty TEXT,
                muscle_joint_pain TEXT,
                weakness TEXT,
                digestive_disorders TEXT,
                headache TEXT,
                skin_rash TEXT,
                contact_with_sick TEXT,
                medication TEXT,
                allergies TEXT,
                chronic_diseases TEXT,
                additional_info TEXT,
                urgency_level INTEGER,
                files TEXT,
                recommendations TEXT,
                FOREIGN KEY (patient_id) REFERENCES users (id)
            )
        ''')
        conn.commit()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_urgency_level(request_data):
    level = 0
    if "плохо" in request_data['general_feeling'].lower():
        level += 2
    if request_data['fever'] == 'да':
        level += 2
    if request_data['breathing_difficulty'] == 'да':
        level += 3
    return min(level, 10)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role')
        snils = request.form.get('snils')

        if 'register' in request.form:
            if username and password and role and snils:
                try:
                    with sqlite3.connect('health_monitoring.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO users (username, password, role, snils) VALUES (?, ?, ?, ?)", (username, password, role, snils))
                        conn.commit()
                    session['username'] = username
                    session['role'] = role
                    flash('Вы успешно зарегистрированы!', 'success')
                    return redirect(url_for('dashboard'))
                except sqlite3.IntegrityError:
                    flash('Имя пользователя или СНИЛС уже занято.', 'error')
        elif 'login' in request.form:
            with sqlite3.connect('health_monitoring.db') as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, role FROM users WHERE username = ? AND password = ?", (username, password))
                user = cursor.fetchone()
                if user:
                    session['username'] = username
                    session['role'] = user[1]
                    return redirect(url_for('dashboard'))
                else:
                    flash('Неверное имя пользователя или пароль.', 'error')
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))

    role = session.get('role')
    if role == 'doctor':
        with sqlite3.connect('health_monitoring.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM health_requests")
            requests = cursor.fetchall()
        return render_template('doctor_dashboard.html', requests=requests)
    elif role == 'patient':
        with sqlite3.connect('health_monitoring.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, recommendations FROM health_requests WHERE patient_id = (SELECT id FROM users WHERE username = ?)", (session['username'],))
            responses = cursor.fetchall()
        return render_template('patient_dashboard.html', responses=responses)

@app.route('/patient_overview')
def patient_overview():
    if 'username' not in session or session.get('role') != 'doctor':
        return redirect(url_for('index'))

    with sqlite3.connect('health_monitoring.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.username, h.blood_pressure, h.heart_rate, h.medication_schedule, h.recommendations
            FROM users u
            LEFT JOIN health_data h ON u.id = h.patient_id
            WHERE u.role = 'patient'
        ''')
        patient_health_data = cursor.fetchall()

    return render_template('patient_overview.html', patient_health_data=patient_health_data)

@app.route('/record_health_data', methods=['POST'])
def record_health_data():
    if 'username' not in session or session.get('role') != 'patient':
        return redirect(url_for('index'))

    blood_pressure = request.form.get('blood_pressure')
    heart_rate = request.form.get('heart_rate')

    with sqlite3.connect('health_monitoring.db') as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO health_data (patient_id, blood_pressure, heart_rate) VALUES ((SELECT id FROM users WHERE username = ?), ?, ?)",
                       (session['username'], blood_pressure, heart_rate))
        conn.commit()

    flash('Данные о здоровье успешно записаны!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/submit_health_request', methods=['GET', 'POST'])
def submit_health_request():
    if 'username' not in session or session.get('role') != 'patient':
        return redirect(url_for('index'))

    if request.method == 'POST':
        age = request.form.get('age')
        gender = request.form.get('gender')
        general_feeling = request.form.get('general_feeling')
        symptom_start_date = request.form.get('symptom_start_date')
        symptoms = request.form.get('symptoms')
        fever = request.form.get('fever')
        cough = request.form.get('cough')
        sore_throat = request.form.get('sore_throat')
        breathing_difficulty = request.form.get('breathing_difficulty')
        muscle_joint_pain = request.form.get('muscle_joint_pain')
        weakness = request.form.get('weakness')
        digestive_disorders = request.form.get('digestive_disorders')
        headache = request.form.get('headache')
        skin_rash = request.form.get('skin_rash')
        contact_with_sick = request.form.get('contact_with_sick')
        medication = request.form.get('medication')
        allergies = request.form.get('allergies')
        chronic_diseases = request.form.get('chronic_diseases')
        additional_info = request.form.get('additional_info')
        
        urgency_level = calculate_urgency_level(request.form)
        
        file_path = None
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

        with sqlite3.connect('health_monitoring.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO health_requests (
                    patient_id, age, gender, general_feeling, symptom_start_date, symptoms, fever, cough, sore_throat, 
                    breathing_difficulty, muscle_joint_pain, weakness, digestive_disorders, headache, skin_rash, 
                    contact_with_sick, medication, allergies, chronic_diseases, additional_info, urgency_level, files
                ) VALUES (
                    (SELECT id FROM users WHERE username = ?), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )''', 
                (session['username'], age, gender, general_feeling, symptom_start_date, symptoms, fever, cough, 
                 sore_throat, breathing_difficulty, muscle_joint_pain, weakness, digestive_disorders, headache, 
                 skin_rash, contact_with_sick, medication, allergies, chronic_diseases, additional_info, 
                 urgency_level, file_path))
            conn.commit()

        flash('Ваша заявка успешно отправлена!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('health_request_form.html')

@app.route('/view_health_data')
def view_health_data():
    if 'username' not in session or session.get('role') != 'doctor':
        return redirect(url_for('index'))

    with sqlite3.connect('health_monitoring.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT u.username, h.blood_pressure, h.heart_rate FROM health_data h JOIN users u ON h.patient_id = u.id")
        health_data = cursor.fetchall()

    return render_template('view_health_data.html', health_data=health_data)

@app.route('/create_medication_schedule', methods=['POST'])
def create_medication_schedule():
    if 'username' not in session or session.get('role') != 'doctor':
        return redirect(url_for('index'))

    patient_username = request.form.get('patient_username')
    medication_schedule = request.form.get('medication_schedule')

    with sqlite3.connect('health_monitoring.db') as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE health_data SET medication_schedule = ? WHERE patient_id = (SELECT id FROM users WHERE username = ?)",
                       (medication_schedule, patient_username))
        conn.commit()

    flash('График приема лекарств успешно обновлен!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/get_medication_schedule')
def get_medication_schedule():
    if 'username' not in session or session.get('role') != 'patient':
        return redirect(url_for('index'))

    with sqlite3.connect('health_monitoring.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT medication_schedule FROM health_data WHERE patient_id = (SELECT id FROM users WHERE username = ?)', (session['username'],))
        schedule_data = cursor.fetchone()

    events = []
    if schedule_data and schedule_data[0]:
        import json
        try:
            schedule = json.loads(schedule_data[0])
            for entry in schedule:
                events.append({
                    'title': entry['medication'],
                    'start': entry['date'],
                    'end': entry['date']
                })
        except json.JSONDecodeError:
            pass

    return jsonify(events)

@app.route('/respond_to_request/<int:request_id>', methods=['POST'])
def respond_to_request(request_id):
    if 'username' not in session or session.get('role') != 'doctor':
        return redirect(url_for('index'))

    treatment_plan = request.form.get('treatment_plan')

    with sqlite3.connect('health_monitoring.db') as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE health_requests SET recommendations = ? WHERE id = ?", (treatment_plan, request_id))
        conn.commit()

    flash('Ответ на заявку успешно отправлен!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
