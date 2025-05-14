admin_from_user_id_prefixes = {
    "1053425852047700048",  # ilike3pancakes
    "spacecat4712",
}


def auth(user_id: int) -> bool:
    return any(str(user_id).startswith(prefix) for prefix in admin_from_user_id_prefixes)


if __name__ == "__main__":
    assert auth("ilike3pancakes0_xyz")
    assert not auth("someuser_123")
    print("Ok")
