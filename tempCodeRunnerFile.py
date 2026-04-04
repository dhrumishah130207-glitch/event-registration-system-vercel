@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('full_name')
    event = data.get('event_name')

    # Save to MySQL Database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO participants (full_name, event_name) VALUES (%s, %s)", (name, event))
    conn.commit()
    cursor.close()
    conn.close()

    # Generate QR Code containing user details
    qr_content = f"Name: {name} | Event: {event}"
    qr = qrcode.make(qr_content)
    buffered = io.BytesIO()
    qr.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode()

    return jsonify({
        "status": "success",
        "qr_code": qr_base64,
        "name": name,
        "event": event
    })