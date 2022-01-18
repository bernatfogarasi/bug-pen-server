from pprint import pprint
from django.http import HttpResponseServerError, JsonResponse, HttpResponseForbidden
from .models import User
import json
import jwt
import requests


def public(request):
    return (
        request.path.startswith("/admin")
        or request.path.startswith("/favicon.ico")
        or request.path.startswith("/membership-count")
    )


class Authenticate:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if public(request):
            return self.get_response(request)

        DOMAIN = "dev-su34m38a.us.auth0.com"
        ISSUER = f"https://{DOMAIN}/"
        AUDIENCE = "http://localhost:8000"
        ALGORITHM = "RS256"
        JWKS_URL = f"{ISSUER}.well-known/jwks.json"

        try:
            authorization = request.headers.get("Authorization")
            request.token = authorization.split()[1]
        except Exception as error:
            print("ERROR", error)
            return HttpResponseForbidden("token not found")

        try:
            header = jwt.get_unverified_header(request.token)
            jwks = requests.get(JWKS_URL).json()
            for jwk in jwks["keys"]:
                if jwk["kid"] == header["kid"]:
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
            request.payload = jwt.decode(
                request.token,
                public_key,
                audience=AUDIENCE,
                issuer=ISSUER,
                algorithms=[ALGORITHM],
            )
            request.user_id = request.payload["sub"]
        except Exception as error:
            print("ERROR", error)
            return HttpResponseForbidden("token not valid")

        try:
            request.user_info = requests.get(
                request.payload["aud"][1],
                headers={"Authorization": f"Bearer {request.token}"},
            ).json()
        except Exception as error:
            print("ERROR", error)
            return HttpResponseServerError("cannot get user info")

        return self.get_response(request)


class UserFindCreate:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if public(request):
            return self.get_response(request)

        try:
            user, update = User.objects.update_or_create(
                user_id=request.user_id,
                email=request.user_info["email"],
                email_verified=request.user_info["email_verified"],
                last_name=request.user_info["family_name"],
                first_name=request.user_info["given_name"],
                locale=request.user_info["locale"],
                picture=request.user_info["picture"],
            )
            request.user = user
        except Exception as error:
            print("ERROR", error)
            return HttpResponseForbidden("cannot find or create user")

        return self.get_response(request)


class ParseBody:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if public(request):
            return self.get_response(request)

        if request.method == "POST":
            try:
                request.data = json.loads(request.body.decode("utf-8"))
            except Exception as error:
                print("ERROR", error)
                return HttpResponseForbidden("cannot read body")

        return self.get_response(request)
