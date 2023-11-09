from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import auth as authh
import pyrebase

app = Flask(__name__)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("./authwithpy-firebase-adminsdk-sso9f-04541d6e1e.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

config = {
    "apiKey": "AIzaSyAlYzwn-3Kx5J28NEUDKSDDrNVISm4ufGE",
    "authDomain": "authwithpy.firebaseapp.com",
    "projectId": "authwithpy",
    "storageBucket": "authwithpy.appspot.com",
    "messagingSenderId": "565009789463",
    "appId": "1:565009789463:web:87b4dd2435becb3130a252",
    "measurementId": "G-8FD2SSM15R",
    "databaseURL" : ""
}

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()

# Register a new user
@app.route('/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        email = data['email']
        password = data['password']

        # Create a Firebase user
        user = authh.create_user(
            email=email,
            password=password
        )

        username = data.get('username', '')
        full_name = data.get('full_name', '')

        # Store user information in Firestore
        user_ref = db.collection('users').document(user.uid)
        user_ref.set({
            'username': username,
            'email': email,
            'full_name': full_name,
            'created_at': firestore.SERVER_TIMESTAMP
        })

        return jsonify({'message': 'User registered successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Login a user and return a Firebase Auth token
@app.route('/login', methods=['POST'])
def login_user():
    try:
        data = request.get_json()
        email = data['email']
        password = data['password']

        user = auth.sign_in_with_email_and_password(email,password)
        token = user['idToken']
        print(token)
        # Return the Firebase Auth token
        # token = authh.create_custom_token(user['localId'])

        return jsonify({'token': token}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 401
    

# Retrieve user profile (excluding password)
@app.route('/profile', methods=['GET'])
def get_user_profile():
    try:
        user = authh.verify_id_token(request.headers['Authorization'])
        user_ref = db.collection('users').document(user['uid'])
        user_data = user_ref.get().to_dict()

        if user_data:
            # user_data.pop('email', None)
            return jsonify(user_data), 200
        else:
            return jsonify({'message': 'User not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 401

# Update user profile (excluding password)
@app.route('/profile', methods=['PUT'])
def update_user_profile():
    try:
        user = authh.verify_id_token(request.headers['Authorization'])
        user_ref = db.collection('users').document(user['uid'])
        data = request.get_json()

        user_ref.update(data)
        return jsonify({'message': 'Profile updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Delete user account
@app.route('/delete', methods=['DELETE'])
def delete_user_account():
    try:
        user = authh.verify_id_token(request.headers['Authorization'])
        user_ref = db.collection('users').document(user['uid'])

        # Delete the user's Firestore document and Firebase Authentication account
        user_ref.delete()
        authh.delete_user(user['uid'])

        return jsonify({'message': 'User account deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
