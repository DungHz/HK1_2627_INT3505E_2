from itertools import count

USERS = {
    1: {"first_name": "Văn", "last_name": "Nguyễn", "email": "a@vnu.vn"},
    2: {"first_name": "Trang", "last_name": "Trần", "email": "b@vnu.vn"},
}
_next_id = count(3)


def get_user(uid):
    return USERS.get(uid)


def email_exists(email):
    return any(u["email"].lower() == email.lower() for u in USERS.values())


def create_user(first_name, last_name, email):
    uid = next(_next_id)
    USERS[uid] = {"first_name": first_name, "last_name": last_name, "email": email}
    return uid