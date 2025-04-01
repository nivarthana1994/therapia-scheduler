from datetime import datetime, timedelta
import sqlite3

class GoogleCalendarMock:
    def __init__(self, db_file):
        self.db_file = db_file
    
    def _get_conn(self):
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn
    
    def add_availability(self, therapist_id, start_time, end_time):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT 1 FROM appointments 
                WHERE therapist_id = ? 
                AND ((start_time < ? AND end_time > ?)
                OR (start_time < ? AND end_time > ?)
                OR (start_time >= ? AND end_time <= ?))
                LIMIT 1
            ''', (therapist_id, end_time, start_time,
                 end_time, start_time,
                 start_time, end_time))
            
            if not c.fetchone():
                c.execute('''
                    INSERT INTO appointments 
                    (therapist_id, client_name, client_email, 
                     start_time, end_time, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (therapist_id, '', '', 
                     start_time, end_time, 'available'))
                conn.commit()
                return True
            return False

    def get_availability(self, therapist_id, date=None):
        with self._get_conn() as conn:
            c = conn.cursor()
            if date:
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                next_day = date_obj + timedelta(days=1)
                c.execute('''
                    SELECT * FROM appointments 
                    WHERE therapist_id = ? 
                    AND status = 'available'
                    AND start_time >= ? 
                    AND end_time <= ?
                    ORDER BY start_time
                ''', (therapist_id, date_obj, next_day))
            else:
                c.execute('''
                    SELECT * FROM appointments 
                    WHERE therapist_id = ? 
                    AND status = 'available'
                    AND start_time >= datetime('now')
                    ORDER BY start_time
                ''', (therapist_id,))
            return c.fetchall()

    def is_slot_available(self, therapist_id, start_time, end_time):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT 1 FROM appointments 
                WHERE therapist_id = ? 
                AND start_time = ? 
                AND end_time = ?
                AND status = 'available'
                LIMIT 1
            ''', (therapist_id, start_time, end_time))
            return c.fetchone() is not None

    def book_appointment(self, therapist_id, client_name, client_email, start_time, end_time):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('''
                UPDATE appointments 
                SET client_name = ?,
                    client_email = ?,
                    status = 'booked'
                WHERE therapist_id = ?
                AND start_time = ?
                AND end_time = ?
                AND status = 'available'
            ''', (client_name, client_email, 
                 therapist_id, start_time, end_time))
            conn.commit()
            return c.rowcount > 0

    def get_appointments(self, therapist_id):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT * FROM appointments 
                WHERE therapist_id = ? 
                AND status = 'booked'
                AND start_time >= datetime('now')
                ORDER BY start_time
            ''', (therapist_id,))
            return c.fetchall()