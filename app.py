from flask import Flask, render_template, request, redirect, url_for, g, flash
from datetime import datetime, timedelta
import sqlite3
import os

app = Flask(__name__, template_folder='templates')
app.config['DATABASE'] = 'scheduler.db'
app.secret_key = os.urandom(24) 

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        # Enable foreign key constraints
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        c = db.cursor()
        
        # Drop tables if they exist (for development only)
        c.execute("DROP TABLE IF EXISTS appointments")
        c.execute("DROP TABLE IF EXISTS therapists")
        
        c.execute('''
            CREATE TABLE therapists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            )
        ''')
        
        c.execute('''
            CREATE TABLE appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                therapist_id INTEGER NOT NULL,
                client_name TEXT NOT NULL,
                client_email TEXT NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY(therapist_id) REFERENCES therapists(id) ON DELETE CASCADE,
                UNIQUE(therapist_id, start_time, end_time)
            )
        ''')
        
        try:
            c.execute('''
                INSERT INTO therapists (name, email)
                VALUES (?, ?)
            ''', ('Dr. Smith', 'dr.smith@example.com'))
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/therapist/set_availability', methods=['GET', 'POST'])
def set_availability():
    if request.method == 'POST':
        therapist_id = request.form.get('therapist_id', '1')
        date = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        
        try:
            start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
            
            db = get_db()
            current_slot = start_datetime
            added_slots = 0
            
            while current_slot < end_datetime:
                slot_end = current_slot + timedelta(hours=1)
                try:
                    db.execute('''
                        INSERT INTO appointments (
                            therapist_id, client_name, client_email, 
                            start_time, end_time, status
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    ''', (therapist_id, '', '', current_slot, slot_end, 'available'))
                    added_slots += 1
                except sqlite3.IntegrityError:
                    db.rollback()
                    flash(f"Slot {current_slot} to {slot_end} already exists", 'warning')
                current_slot = slot_end
            
            db.commit()
            flash(f"Successfully added {added_slots} availability slots", 'success')
            return redirect(url_for('therapist_dashboard', therapist_id=therapist_id))
            
        except ValueError as e:
            flash(f"Invalid date/time format: {str(e)}", 'error')
    
    return render_template('set_availability.html')

@app.route('/therapist/<therapist_id>')
def therapist_dashboard(therapist_id):
    db = get_db()
    try:
        # Get availability
        availability = db.execute('''
            SELECT * FROM appointments 
            WHERE therapist_id = ? 
            AND status = 'available'
            AND start_time >= datetime('now')
            ORDER BY start_time
        ''', (therapist_id,)).fetchall()
        
        # Get appointments
        appointments = db.execute('''
            SELECT * FROM appointments 
            WHERE therapist_id = ? 
            AND status = 'booked'
            AND start_time >= datetime('now')
            ORDER BY start_time
        ''', (therapist_id,)).fetchall()
        
        return render_template('therapist_dashboard.html',
                            availability=availability,
                            appointments=appointments,
                            therapist_id=therapist_id)
    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", 'error')
        return redirect(url_for('home'))

@app.route('/client/view_availability/<therapist_id>')
def view_availability(therapist_id):
    date = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
    db = get_db()
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        next_day = date_obj + timedelta(days=1)
        availability = db.execute('''
            SELECT * FROM appointments 
            WHERE therapist_id = ? 
            AND status = 'available'
            AND start_time >= ? 
            AND end_time <= ?
            ORDER BY start_time
        ''', (therapist_id, date_obj, next_day)).fetchall()
        
        return render_template('view_availability.html',
                            availability=availability,
                            therapist_id=therapist_id,
                            selected_date=date)
    except ValueError:
        flash("Invalid date format", 'error')
        return redirect(url_for('home'))

@app.route('/client/book_appointment', methods=['POST'])
def book_appointment():
    therapist_id = request.form['therapist_id']
    client_name = request.form['client_name']
    client_email = request.form['client_email']
    start_time = request.form['start_time']
    
    try:
        start_datetime = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        end_datetime = start_datetime + timedelta(hours=1)
        
        db = get_db()
        # Check if slot exists and is available
        slot = db.execute('''
            SELECT id FROM appointments 
            WHERE therapist_id = ? 
            AND start_time = ? 
            AND end_time = ?
            AND status = 'available'
        ''', (therapist_id, start_datetime, end_datetime)).fetchone()
        
        if slot:
            db.execute('''
                UPDATE appointments 
                SET client_name = ?,
                    client_email = ?,
                    status = 'booked'
                WHERE id = ?
            ''', (client_name, client_email, slot['id']))
            db.commit()
            return render_template('booking_confirmation.html',
                                start_time=start_datetime,
                                therapist_id=therapist_id)
        
        flash("Time slot no longer available", 'error')
        return redirect(url_for('view_availability', therapist_id=therapist_id))
    except ValueError as e:
        flash(f"Invalid date/time format: {str(e)}", 'error')
        return redirect(url_for('home'))

@app.route('/cancel_slot', methods=['POST'])
def cancel_slot():
    slot_id = request.form['slot_id']
    therapist_id = request.form.get('therapist_id', '1')
    db = get_db()
    try:
        db.execute('DELETE FROM appointments WHERE id = ?', (slot_id,))
        db.commit()
        flash("Time slot removed successfully", 'success')
    except Exception as e:
        db.rollback()
        flash(f"Error removing slot: {str(e)}", 'error')
    return redirect(url_for('therapist_dashboard', therapist_id=therapist_id))

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=False, port=5002)