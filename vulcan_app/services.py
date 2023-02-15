import requests
from .configuration import get_config
from datetime import datetime
from pydantic import BaseModel


async def login(token: str):
    address = get_config("authentication_service_address")
    if address:
        headers = {
            "Authorization": "Bearer " + token
        }
        response = requests.get(address, headers=headers)
        try:
            response.raise_for_status()
            data = response.json()
            return True, {'email': data['email'], 'disability': data['disability']}
        except requests.exceptions.HTTPError as exc:
            print("Login failed", exc)
            return False, None
    return True, {'email': "testuser@vulcan", 'disability': 0}


async def admin_login(username: str, password: str):
    login_address = get_config("admin_authentication_service_address")
    user_address = get_config("admin_verify_service_address")
    if login_address and user_address:

        r = requests.post(login_address, data={'username': username, 'password': password})
        if r.status_code < 400:
            data = r.json()
            headers = {
                "Authorization": "Bearer " + data["access_token"]
            }
            response = requests.get(user_address, headers=headers)
            try:
                response.raise_for_status()
                data = response.json()
                if "performanceManager" in data["claims"]:
                    return True, {'email': data['email']}
                return False, None
            except requests.exceptions.HTTPError as exc:
                print("Login failed", exc)
                return False, None
        else:
            return False, None

    return False, None


class Worklog(BaseModel):
    stamp: datetime
    app_id: str
    user_id: str
    disability: int
    amount: float
    duration: float
    score: float

    def serialize(self):
        d = self.dict()
        d["stamp"] = d["stamp"].strftime('%Y-%m-%dT%H:%M:%S.%f%z')
        return d


async def log_all(worklogs):
    address = get_config('logging_service_address')
    if address:
        response = requests.post(address, json=[w.serialize() for w in worklogs])
        try:
            response.raise_for_status()
            return True
        except requests.exceptions.HTTPError as exc:
            print("Logging failed", exc)
            return False
    return True


if __name__ == '__main__':
    pass
