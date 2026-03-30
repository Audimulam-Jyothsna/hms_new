import os
from datetime import datetime
from flask import Flask, render_template, request, redirect ,session, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Use absolute path to ensure Flask reliably finds the custom 'templets' folder
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templets'))
app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'secrect123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Database Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'doctor', 'patient'

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    details = db.Column(db.Text, nullable=False)
    date_time = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='Scheduled')
    payment_status = db.Column(db.String(20), default='Unpaid')
    prescription = db.Column(db.Text, nullable=True)

    patient = db.relationship('User', foreign_keys=[patient_id], backref='appointments_as_patient')
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='appointments_as_doctor')

# --- New Models for Extended Features ---
class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    treatment = db.Column(db.Text, nullable=False)
    
    patient = db.relationship('User', foreign_keys=[patient_id])
    doctor = db.relationship('User', foreign_keys=[doctor_id])

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.String(50), nullable=False)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text, nullable=True)
    
    patient = db.relationship('User', foreign_keys=[patient_id])
    doctor = db.relationship('User', foreign_keys=[doctor_id])


# --- Mock Data for Doctor Portfolios ---
doctors_info = {
    'Dr.Nangi Rahul': {'spec': 'Cardiologist', 'bio': 'Dr. Rahul is a senior Cardiologist with over 15 years of experience in treating complex heart conditions. He specializes in interventional cardiology.', 'img': '/static/image/Rahul.jpeg'},
    'Dr. Nayan Pitlam': {'spec': 'Pediatrician', 'bio': 'Dr. Nayan is dedicated to providing comprehensive care for infants, children, and adolescents. Known for a friendly approach with kids.', 'img': '/static/image/Nayan Pitlam.jpg'},
    'Dr. Sushanth': {'spec': 'Neurologist', 'bio': 'Dr. Sushanth specializes in disorders of the nervous system, including epilepsy, migraines, and stroke management.', 'img': '/static/image/Sushanth.avif'},
    'Dr. Anitha Desai': {'spec': 'Gynecologist', 'bio': 'Dr. Desai provides compassionate care in women’s health, specializing in obstetrics and gynecological surgeries.', 'img': '/static/image/anitha desi.webp'},
    'Dr. Lohith Pattabhi': {'spec': 'Dermatologist', 'bio': 'Dr. Lohith is an expert in clinical and cosmetic dermatology, helping patients achieve healthy and radiant skin.', 'img': '/static/image/Lohith Pattabhi.jpeg'}
}

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/doctor/<name>')
def doctor_profile(name):
    doctor = doctors_info.get(name)
    if not doctor:
        # Default fallback if name not found
        doctor = {'spec': 'Specialist', 'bio': 'Experienced medical professional.', 'img': 'https://via.placeholder.com/500'}
    doctor_user = User.query.filter_by(username=name, role='doctor').first()
    return render_template('portfolio.html', name=name, doctor=doctor, doctor_user=doctor_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        hashed_pw = generate_password_hash(password)

        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect('/register')

        new_user = User(username=username, password_hash=hashed_pw, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful')
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['username'] = user.username
            return redirect('/dashboard')
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    user_role = session['role']
    appointments = []
    doctors = []
    users = []
    notifications = Notification.query.filter_by(user_id=session['user_id']).order_by(Notification.id.desc()).all()
    medical_records = []
    feedbacks = []

    match user_role:
        case 'patient':
            appointments = Appointment.query.filter_by(patient_id=session['user_id']).all()
            doctors = User.query.filter_by(role='doctor').all()
            medical_records = MedicalRecord.query.filter_by(patient_id=session['user_id']).all()
        case 'doctor':
            appointments = Appointment.query.filter_by(doctor_id=session['user_id']).all()
            feedbacks = Feedback.query.filter_by(doctor_id=session['user_id']).all()
        case 'admin':
            appointments = Appointment.query.all()
            users = User.query.all()
            feedbacks = Feedback.query.all()

    return render_template('dashboard.html', role=user_role, appointments=appointments, doctors=doctors, users=users, notifications=notifications, medical_records=medical_records, feedbacks=feedbacks)

@app.route('/book', methods=['POST'])
def book_appointment():
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect('/login')

    doctor_id = request.form['doctor_id']
    date_time = request.form['date_time']
    details = request.form['details']

    new_appt = Appointment(patient_id=session['user_id'], doctor_id=doctor_id, date_time=date_time, details=details)
    db.session.add(new_appt)
    db.session.commit()
    
    # Notify patient
    notif = Notification(user_id=session['user_id'], message=f"Appointment booked successfully for {date_time}", timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"))
    db.session.add(notif)
    db.session.commit()
    flash('Appointment booked successfully')
    return redirect('/dashboard')

@app.route('/admin/user/add', methods=['POST'])
def admin_add_user():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect('/login')
    
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    hashed_pw = generate_password_hash(password)
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists')
    else:
        new_user = User(username=username, password_hash=hashed_pw, role=role)
        db.session.add(new_user)
        db.session.commit()
        flash('User added successfully')
    return redirect('/dashboard')

@app.route('/admin/user/delete/<int:user_id>')
def admin_delete_user(user_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect('/login')
    User.query.filter_by(id=user_id).delete()
    Appointment.query.filter((Appointment.patient_id == user_id) | (Appointment.doctor_id == user_id)).delete()
    db.session.commit()
    flash('User deleted successfully')
    return redirect('/dashboard')

@app.route('/admin/appointment/update/<int:id>', methods=['POST'])
def admin_update_appointment(id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect('/login')
    appt = Appointment.query.get(id)
    if appt:
        appt.date_time = request.form['date_time']
        appt.status = request.form['status']
        
        # Notify patient of status update
        notif = Notification(user_id=appt.patient_id, message=f"Admin updated your appointment status to {appt.status}", timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"))
        db.session.add(notif)
        
        db.session.commit()
        flash('Appointment updated successfully')
    return redirect('/dashboard')

@app.route('/doctor/appointment/update/<int:id>', methods=['POST'])
def doctor_update_appointment(id):
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect('/login')
    appt = Appointment.query.get(id)
    if appt and appt.doctor_id == session['user_id']:
        appt.status = request.form['status']
        appt.prescription = request.form.get('prescription', '')
        
        # Notify patient of status update
        notif = Notification(user_id=appt.patient_id, message=f"Doctor updated your appointment status to {appt.status}", timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"))
        db.session.add(notif)
        
        db.session.commit()
        flash('Appointment status and prescription updated')
    return redirect('/dashboard')

@app.route('/notification/read/<int:id>')
def read_notification(id):
    if 'user_id' not in session: return redirect('/login')
    notif = Notification.query.get(id)
    if notif and notif.user_id == session['user_id']:
        notif.is_read = True
        db.session.commit()
    return redirect('/dashboard')

@app.route('/medical_record/add', methods=['POST'])
def add_medical_record():
    if 'user_id' not in session or session['role'] != 'doctor': return redirect('/login')
    patient_id = request.form['patient_id']
    
    new_record = MedicalRecord(patient_id=patient_id, doctor_id=session['user_id'], date=datetime.now().strftime("%Y-%m-%d"), diagnosis=request.form['diagnosis'], treatment=request.form['treatment'])
    db.session.add(new_record)
    
    notif = Notification(user_id=patient_id, message="A new medical record has been added to your profile.", timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"))
    db.session.add(notif)
    
    db.session.commit()
    flash('Medical record added successfully')
    return redirect('/dashboard')

@app.route('/feedback/add', methods=['POST'])
def add_feedback():
    if 'user_id' not in session or session['role'] != 'patient': return redirect('/login')
    new_feedback = Feedback(patient_id=session['user_id'], doctor_id=request.form['doctor_id'], rating=request.form['rating'], comments=request.form['comments'])
    db.session.add(new_feedback)
    db.session.commit()
    flash('Feedback submitted successfully')
    return redirect('/dashboard')

@app.route('/bill/<int:id>')
def view_bill(id):
    if 'user_id' not in session:
        return redirect('/login')
        
    appt = Appointment.query.get(id)
    if not appt:
        flash('Appointment not found')
        return redirect('/dashboard')
        
    # Prevent patients from viewing other patients' bills
    if session['role'] == 'patient' and appt.patient_id != session['user_id']:
        flash('Unauthorized access')
        return redirect('/dashboard')
        
    if appt.status != 'Completed':
        flash('Bill is only available after treatment is completed.')
        return redirect('/dashboard')

    # Mock bill generation values
    base_fee = 500
    tax = 50
    total = base_fee + tax

    return render_template('bill.html', appt=appt, base_fee=base_fee, tax=tax, total=total, for_pdf=False)

@app.route('/pay/<int:id>', methods=['POST'])
def pay_bill(id):
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect('/login')
        
    appt = Appointment.query.get(id)
    if appt and appt.patient_id == session['user_id']:
        appt.payment_status = 'Paid'
        db.session.commit()
        flash('Payment successful! Thank you.')
    else:
        flash('Error processing payment.')
        
    return redirect('/dashboard')

@app.route('/bill/pdf/<int:id>')
def download_bill_pdf(id):
    if 'user_id' not in session:
        return redirect('/login')
        
    appt = Appointment.query.get(id)
    if not appt:
        flash('Appointment not found')
        return redirect('/dashboard')
        
    # Security check
    if session['role'] == 'patient' and appt.patient_id != session['user_id']:
        flash('Unauthorized access')
        return redirect('/dashboard')

    base_fee, tax, total = 500, 50, 550

    # Delegate PDF generation to the browser's native engine
    return render_template('bill.html', appt=appt, base_fee=base_fee, tax=tax, total=total, for_pdf=True)

@app.route('/prescription/pdf/<int:id>')
def download_prescription_pdf(id):
    if 'user_id' not in session:
        return redirect('/login')
        
    appt = Appointment.query.get(id)
    if not appt:
        flash('Appointment not found')
        return redirect('/dashboard')
        
    if session['role'] == 'patient' and appt.patient_id != session['user_id']:
        flash('Unauthorized access')
        return redirect('/dashboard')
        
    if not appt.prescription:
        flash('No prescription available yet.')
        return redirect('/dashboard')

    # Delegate PDF generation to the browser's native engine
    return render_template('prescription.html', appt=appt)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Seed doctors from doctors_info into the database
        for name in doctors_info.keys():
            if not User.query.filter_by(username=name).first():
                hashed_pw = generate_password_hash('doctor123') # Default password for doctors
                new_doctor = User(username=name, password_hash=hashed_pw, role='doctor')
                db.session.add(new_doctor)
                
        # Seed a default admin if one does not exist
        if not User.query.filter_by(role='admin').first():
            admin_pw = generate_password_hash('admin123')
            new_admin = User(username='admin', password_hash=admin_pw, role='admin')
            db.session.add(new_admin)
            
        db.session.commit()
    app.run(debug=True)
