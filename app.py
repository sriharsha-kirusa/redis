from flask import Flask, request, jsonify
from flask_mail import Mail, Message
import pyotp
import redis

# Initialize Flask app
app = Flask(__name__)

# Initialize Redis client
redis_client = redis.Redis(host='redis', port=6379)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'maiid'
app.config['MAIL_PASSWORD'] = 'password'

mail = Mail(app)

def generate_totp(secret_key):
    totp = pyotp.TOTP(secret_key)
    return totp.now()

# Example usage
secret_key = pyotp.random_base32()

# Endpoint to generate a token
@app.route('/generate_token', methods=['POST'])
def generate_token():
    token = request.json.get('token')
    if token:
        # Set token in Redis with status 'active'
        redis_client.set(token, 'active')
        return jsonify({'message': 'Token generated successfully'}), 201
    else:
        return jsonify({'error': 'Token not provided'}), 400

# Endpoint to block a token
@app.route('/block_token', methods=['POST'])
def block_token():
    token = request.json.get('token')
    if token:
        # Set token status to 'blocked' in Redis
        redis_client.set(token, 'blocked')
        return jsonify({'message': 'Token blocked successfully'}), 200
    else:
        return jsonify({'error': 'Token not provided'}), 400

    
# Endpoint to check the status of a token
@app.route('/check_token', methods=['GET'])
def check_token():
    token = request.args.get('token')
    if token:
        # Check if token exists in Redis
        status = redis_client.get(token)
        if status is not None:
            return jsonify({'status': status.decode()}), 200
        else:
            return jsonify({'status': 'Token not found'}), 404
    else:
        return jsonify({'error': 'Token not provided'}), 400
    
# Endpoint to unblock a token
@app.route('/unblock_token', methods=['POST'])
def unblock_token():
    token = request.json.get('token')
    if token:
        # Check if token exists in Redis
        if redis_client.exists(token):
            # Set token status to 'active' in Redis
            redis_client.set(token, 'active')
            return jsonify({'message': 'Token unblocked successfully'}), 200
        else:
            return jsonify({'error': 'Token not found'}), 404
    else:
        return jsonify({'error': 'Token not provided'}), 400

@app.route("/sendmail", methods=['POST'])
def send_email():
    data = request.json  # Get JSON data from the request body
    
    subject = "KIRUSA FIT EMAIL VERIFICATION"
    recipient = data.get('recipient')

    if not all([subject, recipient]):
        return "Missing required fields", 400

    otp =  generate_totp(secret_key)

    msg = Message(subject, sender='your_email@example.com', recipients=[recipient])
    msg.body = f"Your One-Time Password (OTP) for Kirusa Fit is: {otp}"
    mail.send(msg)
    return jsonify({"otp": otp, "message": "Email sent with the OTP!"})
    
# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
