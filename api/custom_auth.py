from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from django.conf import settings
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomAuth(BaseAuthentication):

    def authenticate(self, request):
        token = self.get_token(request)
        if not token:
            return None
        
        try:
            payload = jwt.decode(jwt=token, key=settings.SECRET_KEY,algorithms='HS256')
            self.verify_token(payload=payload)
            user_id = payload['id']
            user = User.objects.get(id=user_id)
            return (user, None)
        except (InvalidTokenError, ExpiredSignatureError, User.DoesNotExist) as e:
            raise AuthenticationFailed("Invalid token!")

    def get_token(self, request):
        auth_header = request.headers.get('Authorization', None)
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split(" ")[1]
        return None
    
    def generate_token(payload):
        expiration = datetime.now() + timedelta(days=1)
        payload['exp'] = expiration
        token = jwt.encode(payload=payload, key=settings.SECRET_KEY,)
        return token

    def verify_token(self, payload):
        if 'exp' not in payload:
            raise InvalidTokenError("Token has no expriration")
        exp_time = payload['exp']
        current_time = datetime.now().timestamp()
        if current_time > exp_time:
            raise ExpiredSignatureError("Token expired!")
