from django.http import JsonResponse, HttpResponseForbidden
from .models import User
import json
import jwt
import requests


class Authenticate:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin"):
            return self.get_response(request)

        DOMAIN = "dev-su34m38a.us.auth0.com"
        ISSUER = f"https://{DOMAIN}/"
        AUDIENCE = "http://localhost:8000"
        ALGORITHM = "RS256"
        JWKS_URL = f"{ISSUER}.well-known/jwks.json"

        try:
            token = request.headers.get("Authorization")
            token = token.split()[1]
        except Exception:
            return HttpResponseForbidden("token not found")

        try:
            header = jwt.get_unverified_header(token)
            jwks = requests.get(JWKS_URL).json()
            for jwk in jwks["keys"]:
                if jwk["kid"] == header["kid"]:
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
            request.payload = jwt.decode(
                token,
                public_key,
                audience=AUDIENCE,
                issuer=ISSUER,
                algorithms=[ALGORITHM],
            )
            request.userId = request.payload["sub"]
        except Exception:
            return HttpResponseForbidden("token not valid")

        return self.get_response(request)


class UserFindCreate:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin"):
            return self.get_response(request)

        try:
            user, created = User.objects.get_or_create(userId=request.userId)
            if created:
                user.save()
            request.user = user
        except Exception:
            return HttpResponseForbidden("cannot find/create user")

        return self.get_response(request)


class ParseBody:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin"):
            return self.get_response(request)

        if request.method == "POST":
            try:
                request.data = json.loads(request.body.decode("utf-8"))
            except Exception:
                return HttpResponseForbidden("cannot read body")

        return self.get_response(request)
