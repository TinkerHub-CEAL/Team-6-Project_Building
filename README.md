# Smart Queue and Crowd Monitoring System

A mobile-first hospital queue management system with QR-based registration, department-based queue segmentation, waiting time prediction, and a publicly accessible live dashboard.

## Features

- **QR-Based Registration**: Patients scan a QR code at hospital entrance and register via mobile web interface
- **Department-Based Queues**: 5 separate queues for different hospital services
- **Real-Time Updates**: Live dashboard updates every 5 seconds, patient status updates every 10 seconds
- **Waiting Time Prediction**: Intelligent estimation based on queue position and average service time
- **Crowd Level Monitoring**: Color-coded indicators (Green/Yellow/Red) for department and hospital-wide crowd levels
- **Mobile-First Design**: Optimized for smartphones with touch-friendly buttons and responsive layout
- **Medical Theme**: Clean, professional design with blue, white, and green color scheme

## Technology Stack

- **Backend**: Python Flask with SQLAlchemy ORM
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Real-Time Updates**: AJAX polling

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone or navigate to the project directory**:
   ```bash
   cd Team-6-Project_Building
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access the application**:
   - Open your browser and navigate to: `http://localhost:5000`
   - For mobile testing on the same network: `http://[your-computer-ip]:5000`

## QR Code Setup

To create a QR code for hospital entrance:

1. **Generate QR Code** pointing to your application URL:
   - For local testing: `http://[your-computer-ip]:5000/`
   - For production: `https://yourdomain.com/`

2. **QR Code Generation Options**:
   - Use online QR generators (e.g., qr-code-generator.com)
   - Or use Python's qrcode library:
     ```python
     import qrcode
     qr = qrcode.make('http://your-url:5000/')
     qr.save('hospital_entrance_qr.png')
     ```

3. **Print and Display** the QR code at hospital entrance

## Application Structure

```
Team-6-Project_Building/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── hospital_queue.db          # SQLite database (auto-created)
├── static/
│   └── css/
│       └── style.css          # Responsive CSS with medical theme
└── templates/
    ├── base.html              # Base template
    ├── landing.html           # Landing page (QR entry point)
    ├── register.html          # Queue registration form
    ├── status.html            # Patient status tracker
    └── dashboard.html         # Live public dashboard
```

## Available Departments

1. **👨‍⚕️ Doctor Consultation** (15 min avg service time)
2. **💊 Pharmacy / Medicine Pickup** (5 min avg service time)
3. **🩸 Blood Test / Laboratory** (10 min avg service time)
4. **🔬 Radiology / Scanning (X-ray, MRI, CT)** (20 min avg service time)
5. **📄 Medical Report Collection** (3 min avg service time)

## API Endpoints

### Public Endpoints

- `GET /` - Landing page
- `GET /register` - Registration form
- `POST /register` - Submit registration
- `GET /status/<user_id>` - User status page
- `GET /dashboard` - Live public dashboard

### API Endpoints

- `GET /api/department_status` - Department-wise queue data (JSON)
- `GET /api/hospital_overview` - Hospital-wide metrics (JSON)
- `GET /api/patient_status/<patient_id>` - Individual patient status (JSON)
- `GET /api/waiting_patients` - List of all waiting patients (JSON)
- `POST /api/leave_queue` - Patient leaves/cancels queue registration (JSON)
- `POST /api/mark_served` - Mark patient as served (JSON)

## Usage Flow

### For Patients

1. **Scan QR Code** at hospital entrance
2. **Enter Details**: Name/Patient ID and select department
3. **Receive Queue Number** with estimated waiting time
4. **Monitor Status**: Auto-refreshing status page shows live position
5. **Get Notified**: When position approaches, head to department

### For Hospital Staff

1. **View Dashboard**: Monitor all department queues in real-time
2. **Track Crowd Levels**: Color-coded indicators show busy departments
3. **Manage Flow**: Use insights to allocate resources

## Crowd Level Classification

### Per Department
- **Low (Green)**: 0-10 patients
- **Moderate (Yellow)**: 11-25 patients
- **High (Red)**: 26+ patients

### Hospital-Wide
- **Low (Green)**: 0-40 patients
- **Moderate (Yellow)**: 41-80 patients
- **High (Red)**: 81+ patients

## Waiting Time Calculation

```
Estimated Waiting Time = (Position in Queue - 1) × Average Service Time
```

Example: If you're 5th in line for Doctor Consultation (15 min avg):
```
Waiting Time = (5 - 1) × 15 = 60 minutes
```

## Testing the Application

### Manual Testing

1. **Register multiple patients** in different departments
2. **Open dashboard** in another tab to see live updates
3. **Monitor status page** to see position changes
4. **Test on mobile device** for responsive design

### Mark Patient as Served (Testing)

Use the API endpoint to simulate patient service:

```bash
curl -X POST http://localhost:5000/api/mark_served \
  -H "Content-Type: application/json" \
  -d '{"patient_id": 1}'
```

### Leave Queue (Patient Self-Service)

Patients can leave the queue using the "Leave Queue" button on their status page, or via API:

```bash
curl -X POST http://localhost:5000/api/leave_queue \
  -H "Content-Type: application/json" \
  -d '{"patient_id": 1}'
```

### Auto-Timeout (No-Show Management)

Patients are automatically removed from the queue if they don't show up within their estimated waiting time plus a grace period.

**Configuration**:
- Grace Period: 5 minutes (configurable in `app.py` as `TIMEOUT_GRACE_PERIOD`)
- Calculation: `Registration Time + Estimated Wait Time + Grace Period`
- Status: Timed-out patients are marked as `'timeout'`

**Example**:
- Patient registers at 14:00
- Estimated wait time: 15 minutes
- Grace period: 5 minutes
- Auto-removal time: 14:20 (14:00 + 15 + 5)

The timeout check runs automatically on every dashboard and API refresh.

## Mobile Optimization

- ✅ Responsive design (mobile-first approach)
- ✅ Touch-friendly buttons (minimum 48px height)
- ✅ Large, readable fonts
- ✅ High contrast for accessibility
- ✅ Fast loading with minimal dependencies
- ✅ Works offline after initial load (static assets cached)

## Browser Compatibility

- Chrome/Edge (recommended)
- Firefox
- Safari (iOS/macOS)
- Mobile browsers (Android/iOS)

## Future Enhancements

- [ ] SMS/Email notifications when turn approaches
- [ ] Flask-SocketIO for WebSocket-based real-time updates
- [ ] Admin panel for managing departments and service times
- [ ] Patient history and analytics
- [ ] Multi-language support
- [ ] PWA (Progressive Web App) for offline functionality
- [ ] Integration with hospital management systems

## Troubleshooting

### Database Issues
If you encounter database errors, delete `hospital_queue.db` and restart the application. The database will be recreated automatically.

### Port Already in Use
If port 5000 is already in use, modify the last line in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change port number
```

### Mobile Access Issues
Ensure your mobile device is on the same network and firewall allows connections to port 5000.

## License

This project is created for educational purposes.

## Support

For issues or questions, please refer to the implementation documentation.

---

**Built with ❤️ for better hospital queue management**
