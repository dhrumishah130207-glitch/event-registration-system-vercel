import mysql.connector
import qrcode
import io
import base64
import os
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from fpdf import FPDF

app = Flask(__name__)
CORS(app)  # Allows the frontend to communicate with this backend

# --- DATABASE CONFIGURATION ---
db_config = {
    'host': 'localhost',
    'user': 'root',         # Change to your MySQL username
    'password': '1302'  # Change to your MySQL password
}

def init_db():
    """Initializes the database and table as per project requirements."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS college_events")
    cursor.execute("USE college_events")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(100),
            email VARCHAR(100),
            phone VARCHAR(20),
            event_name VARCHAR(100),
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def get_db_connection():
    return mysql.connector.connect(**db_config, database='college_events')

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('full_name')
    email = data.get('email')
    phone = data.get('phone')
    event = data.get('event_name')

    # Save to MySQL Database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO participants (full_name,email, phone, event_name) VALUES (%s, %s, %s, %s)", (name, email, phone, event))
    conn.commit()
    cursor.close()
    conn.close()

    # Generate QR Code containing user details
    qr_content = f"Name: {name} |Email: {email} |Phone: {phone} | Event: {event}"
    qr = qrcode.make(qr_content)
    buffered = io.BytesIO()
    qr.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()

    return jsonify({
        "status": "success",
        "qr_code": qr_base64,
        "name": name,
        "email": email,
        "phone": phone,
        "event": event
    })

@app.route('/download_receipt', methods=['POST'])
def download_receipt():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    event = data.get('event')
    qr_b64 = data.get('qr_code')

    # Create Thermal Style Receipt (Width: 80mm, Height: 150mm)
    # This mimics the narrow paper look in your uploaded image
    pdf = FPDF(format=(80, 150)) 
    pdf.add_page()
    
    # Header: Shop Name style
    pdf.set_font("Courier", 'B', 12)
    pdf.cell(60, 10, event , ln=True, align='C')
    
    pdf.set_font("Courier", size=7)
    pdf.cell(60, 4, "Karnavati University Campus, Main Hall", ln=True, align='C')
    pdf.cell(60, 4, "Date: 2026-04-03", ln=True, align='C') # Current Date
    
    # Decorative line
    '''pdf.cell(60, 5, "*" * 35, ln=True, align='C')
    pdf.set_font("Courier", 'B', 10)
    pdf.cell(60, 8, "CASH RECEIPT", ln=True, align='C')
    pdf.cell(60, 5, "*" * 35, ln=True, align='C')'''

    # Table Header
    pdf.ln(1)
    pdf.set_font("Courier", 'B', 9)
    pdf.cell(35, 8, "Description", align='L')
    pdf.cell(25, 8, "Details", align='R', ln=True)
    
    # Participant Name Row
    pdf.set_font("Courier", size=9)
    pdf.cell(35, 6, "PARTICIPANT:", align='L')
    pdf.cell(25, 6, f"{name[:12]}", align='R', ln=True)

    # Event Name Row
    pdf.cell(35, 6, "EVENT:", align='L')
    pdf.cell(25, 6, f"{event[:12]}", align='R', ln=True)
    
    # Phone Row
    pdf.cell(35, 6, "PHONE:", align='L')
    pdf.cell(25, 6, f"{phone[:12]}", align='R', ln=True)
    
    # Decorative line before QR
    pdf.ln(1)
    pdf.cell(60, 5, "-" * 35, ln=True, align='C')
    pdf.set_font("Courier", 'B', 9)
    pdf.cell(60, 8, "SCAN FOR ENTRY", ln=True, align='C')

    # Embed QR Code (Centered)
    qr_img_data = base64.b64decode(qr_b64)
    qr_path = "temp_qr.png"
    with open(qr_path, "wb") as f:
        f.write(qr_img_data)
    
    # Positioning the QR code in the middle of the 80mm width
    pdf.image(qr_path, x=15, y=pdf.get_y(), w=50)
    
    # Footer
    pdf.ln(50) # Move below the QR image
    pdf.set_font("Courier", 'B', 10)
    pdf.cell(60, 5, "THANK YOU!", ln=True, align='C')
    pdf.set_font("Courier", size=7)
    pdf.cell(60, 5, "Keep this for event entry", ln=True, align='C')

    pdf_out = io.BytesIO()
    pdf_content = pdf.output(dest='S')
    if isinstance(pdf_content, str):
        pdf_content = pdf_content.encode('latin-1')
    pdf_out = io.BytesIO()
    pdf_out.write(pdf_content)
    pdf_out.seek(0)
    
    # Cleanup temp file
    if os.path.exists(qr_path):
        os.remove(qr_path)
    
    return send_file(pdf_out, as_attachment=True, download_name=f"Receipt_{name}.pdf", mimetype='application/pdf')

@app.route('/get_registrations', methods=['GET'])
def get_registrations():
    """Fetches all participants from the MySQL database for the Admin Panel."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True) # returns rows as dictionaries
        cursor.execute("SELECT full_name, email, phone, event_name FROM participants ORDER BY id DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(port=5000, debug=True)