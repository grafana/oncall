from migrator.resources.users import match_user


def test_match_user_not_found():
    pd_user = {"email": "test@test.com"}
    oncall_users = [{"email": "test1@test.com"}]

    match_user(pd_user, oncall_users)
    assert pd_user["oncall_user"] is None


def test_match_user_email_case_insensitive():
    pd_user = {"email": "test@test.com"}
    oncall_users = [{"email": "TEST@TEST.COM"}]

    match_user(pd_user, oncall_users)
    assert pd_user["oncall_user"] == oncall_users[0]
