# Therapia Appointment Scheduler

[Appointment Scheduler Demo Video] - https://drive.google.com/file/d/1deg-I4TRudzp9bRL6iMgMjcJgVMFnUvh/view?usp=sharing

*A simple Flask(python)-based appointment scheduling system with SQLite*

## Features

- Therapists can set availability in 1-hour blocks  
-  Clients can view and book available slots  
-  Prevents double-booking with real-time checks  
- Responsive web interface  

## Local Setup Guide

### Prerequisites
- Python 3.8+
- Git (optional)

### Installation
1. **Clone the repository**  
   ```bash
   git clone https://github.com/nivarthana1994/therapia-scheduler.git
   cd therapia-scheduler
Set up environment


# Install dependencies
pip install -r requirements.txt


# Initialize the database


python app.py
This creates scheduler.db 

# Running the Application

python app.py
Access the app at: http://localhost:5001

# First-Time Setup

# Therapist Access


Set availability at: http://localhost:5001/therapist/set_availability

# Client Access

View availability: http://localhost:5001/client/view_availability/1

# Book appointments directly from available slots

File Structure

.
├── app.py                 
├── scheduler.db           
├── requirements.txt       
├── .env                  
└── templates/             
    ├── index.html
    ├── set_availability.html
    ├── therapist_dashboard.html
    ├── view_availability.html
    └── booking_confirmation.html

# Troubleshooting
Port already in use: Change port in app.py (app.run(port=5002))

Database issues: Delete scheduler.db and restart

Missing packages: Re-run pip install -r requirements.txt
