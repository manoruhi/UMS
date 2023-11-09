from fastapi import FastAPI, HTTPException, Request
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import auth as authh
import pyrebase

app = FastAPI()

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

@app.post("/register")
async def register_user(user_data: dict):
    try:
        email = user_data['email']
        password = user_data['password']

        # Create a Firebase user
        user = authh.create_user(
            email=email,
            password=password
        )

        username = user_data.get('username', '')
        full_name = user_data.get('full_name', '')

        # Store user information in Firestore
        user_ref = db.collection('users').document(user.uid)
        user_ref.set({
            'username': username,
            'email': email,
            'full_name': full_name,
            'created_at': firestore.SERVER_TIMESTAMP
        })

        return {'message': 'User registered successfully'}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/login')
async def login_user(data:dict):
    try:
        email = data['email']
        password = data['password']

        print(email)
        print(password)

        user = auth.sign_in_with_email_and_password(email,password)
        token = user['idToken']
        print(token)

        return ({'token': token}), 200

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    
@app.post("/reset-password")
async def reset_password(data: dict):
    try:
        user = authh.get_user_by_email(data.get('email'))
        authh.generate_password_reset_link(user.email)
        return {"message": "Password reset email sent. Please check your inbox."}
    except auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profile")
async def get_user_profile(request:Request):
    try:
        authorization_header = request.headers.get('Authorization')

        if not authorization_header:
            raise HTTPException(status_code=401, detail='Authorization header is missing')

        # Verify the user's ID token
        user = authh.verify_id_token(authorization_header)

        user_ref = db.collection('users').document(user['uid'])
        user_data = user_ref.get().to_dict()

        if user_data:
            # You can remove sensitive information if needed
            # user_data.pop('email', None)
            return user_data

        raise HTTPException(status_code=404, detail='User not found')

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    

@app.put('/profile')
async def update_user_profile(request: Request, data:dict):
    try:
        user = authh.verify_id_token(request.headers['Authorization'])
        user_ref = db.collection('users').document(user['uid'])

        user_ref.update(data)
        return ({'message': 'Profile updated successfully'}), 200

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.delete('/delete')
async def delete_user_account(request:Request):
    try:
        user = authh.verify_id_token(request.headers['Authorization'])
        user_ref = db.collection('users').document(user['uid'])

        # Delete the user's Firestore document and Firebase Authentication account
        user_ref.delete()
        authh.delete_user(user['uid'])

        return ({'message': 'User account deleted successfully'}), 200

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
