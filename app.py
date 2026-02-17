from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital_queue.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    average_service_time = db.Column(db.Integer, nullable=False)  # in minutes
    description = db.Column(db.String(200))
    
    def __repr__(self):
        return f'<Department {self.name}>'

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    queue_number = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='waiting')  # 'waiting' or 'served'
    
    def __repr__(self):
        return f'<Patient {self.name} - {self.department}>'

# Initialize database and default departments
def init_db():
    with app.app_context():
        db.create_all()
        
        # Check if departments already exist
        if Department.query.count() == 0:
            departments = [
                Department(name='Doctor Consultation', average_service_time=15, 
                          description='General physician consultation'),
                Department(name='Pharmacy / Medicine Pickup', average_service_time=5,
                          description='Collect prescribed medicines'),
                Department(name='Blood Test / Laboratory', average_service_time=10,
                          description='Blood tests and lab work'),
                Department(name='Radiology / Scanning (X-ray, MRI, CT)', average_service_time=20,
                          description='Medical imaging services'),
                Department(name='Medical Report Collection', average_service_time=3,
                          description='Collect test reports and documents')
            ]
            
            for dept in departments:
                db.session.add(dept)
            
            db.session.commit()
            print("Database initialized with default departments")

# Queue Management Functions
def get_next_queue_number(department_name):
    """Get the next queue number for a specific department"""
    last_patient = Patient.query.filter_by(
        department=department_name,
        status='waiting'
    ).order_by(Patient.queue_number.desc()).first()
    
    if last_patient:
        return last_patient.queue_number + 1
    return 1

def get_queue_position(patient_id):
    """Get current position in queue for a patient"""
    patient = Patient.query.get(patient_id)
    if not patient or patient.status != 'waiting':
        return None
    
    # Count patients ahead in the same department
    position = Patient.query.filter(
        Patient.department == patient.department,
        Patient.status == 'waiting',
        Patient.queue_number < patient.queue_number
    ).count() + 1
    
    return position

def calculate_waiting_time(department_name, position):
    """Calculate estimated waiting time based on position and average service time"""
    dept = Department.query.filter_by(name=department_name).first()
    if not dept:
        return 0
    
    # Estimated Waiting Time = Position × Average Service Time
    return (position - 1) * dept.average_service_time

def get_crowd_level(count):
    """Classify crowd level based on count"""
    if count <= 10:
        return {'level': 'Low', 'color': 'success'}
    elif count <= 25:
        return {'level': 'Moderate', 'color': 'warning'}
    else:
        return {'level': 'High', 'color': 'danger'}

def get_hospital_crowd_level(total_count):
    """Classify overall hospital crowd level"""
    if total_count <= 40:
        return {'level': 'Low', 'color': 'success'}
    elif total_count <= 80:
        return {'level': 'Moderate', 'color': 'warning'}
    else:
        return {'level': 'High', 'color': 'danger'}

# Routes
@app.route('/')
def landing():
    """Landing page - entry point after QR scan"""
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Queue registration page"""
    if request.method == 'GET':
        departments = Department.query.all()
        return render_template('register.html', departments=departments)
    
    # POST - Handle registration
    name = request.form.get('name', '').strip()
    department = request.form.get('department', '').strip()
    
    # Input validation
    if not name or not department:
        return jsonify({'error': 'Name and department are required'}), 400
    
    # Verify department exists
    dept = Department.query.filter_by(name=department).first()
    if not dept:
        return jsonify({'error': 'Invalid department'}), 400
    
    # Create new patient
    queue_number = get_next_queue_number(department)
    patient = Patient(
        name=name,
        department=department,
        queue_number=queue_number
    )
    
    db.session.add(patient)
    db.session.commit()
    
    # Calculate position and waiting time
    position = get_queue_position(patient.id)
    waiting_time = calculate_waiting_time(department, position)
    
    # Get department crowd level
    dept_queue_count = Patient.query.filter_by(
        department=department,
        status='waiting'
    ).count()
    crowd_level = get_crowd_level(dept_queue_count)
    
    # Store patient ID in session
    session['patient_id'] = patient.id
    
    return jsonify({
        'success': True,
        'patient_id': patient.id,
        'queue_number': queue_number,
        'position': position,
        'waiting_time': waiting_time,
        'crowd_level': crowd_level
    })

@app.route('/status/<int:user_id>')
def status(user_id):
    """User status page - live queue position tracker"""
    patient = Patient.query.get_or_404(user_id)
    
    if patient.status == 'served':
        position = 0
        waiting_time = 0
    else:
        position = get_queue_position(user_id)
        waiting_time = calculate_waiting_time(patient.department, position) if position else 0
    
    # Get department crowd level
    dept_queue_count = Patient.query.filter_by(
        department=patient.department,
        status='waiting'
    ).count()
    crowd_level = get_crowd_level(dept_queue_count)
    
    return render_template('status.html', 
                         patient=patient,
                         position=position,
                         waiting_time=waiting_time,
                         crowd_level=crowd_level)

@app.route('/dashboard')
def dashboard():
    """Public live dashboard - hospital-wide monitoring"""
    return render_template('dashboard.html')

@app.route('/api/department_status')
def department_status():
    """API endpoint for department-wise queue data"""
    departments = Department.query.all()
    dept_data = []
    
    for dept in departments:
        # Get waiting patients count
        queue_count = Patient.query.filter_by(
            department=dept.name,
            status='waiting'
        ).count()
        
        # Calculate average waiting time
        avg_waiting_time = dept.average_service_time * (queue_count / 2 if queue_count > 0 else 0)
        
        # Get crowd level
        crowd_level = get_crowd_level(queue_count)
        
        dept_data.append({
            'name': dept.name,
            'queue_count': queue_count,
            'average_service_time': dept.average_service_time,
            'avg_waiting_time': round(avg_waiting_time, 1),
            'crowd_level': crowd_level['level'],
            'crowd_color': crowd_level['color']
        })
    
    return jsonify(dept_data)

@app.route('/api/hospital_overview')
def hospital_overview():
    """API endpoint for hospital-wide metrics"""
    total_waiting = Patient.query.filter_by(status='waiting').count()
    total_served = Patient.query.filter_by(status='served').count()
    
    # Get overall hospital crowd level
    hospital_crowd = get_hospital_crowd_level(total_waiting)
    
    return jsonify({
        'total_waiting': total_waiting,
        'total_served': total_served,
        'total_patients': total_waiting + total_served,
        'crowd_level': hospital_crowd['level'],
        'crowd_color': hospital_crowd['color']
    })

@app.route('/api/patient_status/<int:patient_id>')
def patient_status_api(patient_id):
    """API endpoint for individual patient status updates"""
    patient = Patient.query.get_or_404(patient_id)
    
    if patient.status == 'served':
        position = 0
        waiting_time = 0
    else:
        position = get_queue_position(patient_id)
        waiting_time = calculate_waiting_time(patient.department, position) if position else 0
    
    # Get department crowd level
    dept_queue_count = Patient.query.filter_by(
        department=patient.department,
        status='waiting'
    ).count()
    crowd_level = get_crowd_level(dept_queue_count)
    
    return jsonify({
        'name': patient.name,
        'department': patient.department,
        'queue_number': patient.queue_number,
        'position': position,
        'waiting_time': waiting_time,
        'status': patient.status,
        'crowd_level': crowd_level['level'],
        'crowd_color': crowd_level['color']
    })

@app.route('/api/leave_queue', methods=['POST'])
def leave_queue():
    """API endpoint for patients to leave/cancel their queue registration"""
    patient_id = request.json.get('patient_id')
    
    if not patient_id:
        return jsonify({'error': 'Patient ID required'}), 400
    
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    if patient.status != 'waiting':
        return jsonify({'error': 'Patient is not in queue'}), 400
    
    # Mark patient as cancelled (left the queue)
    patient.status = 'cancelled'
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f'{patient.name} has left the queue for {patient.department}'
    })

@app.route('/api/mark_served', methods=['POST'])
def mark_served():
    """API endpoint to mark a patient as served (for testing/admin)"""
    patient_id = request.json.get('patient_id')
    
    if not patient_id:
        return jsonify({'error': 'Patient ID required'}), 400
    
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    patient.status = 'served'
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'Patient {patient.name} marked as served'})

if __name__ == '__main__':
    init_db()
    print("Server started on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
    
