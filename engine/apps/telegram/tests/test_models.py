import pytest

from apps.telegram.models.verification.personal import TelegramVerificationCode


@pytest.mark.django_db
def test_user_verification_handler_process_update_another_account_already_linked(
    make_organization,
    make_user_for_organization,
    make_telegram_user_connector,
    make_telegram_verification_code,
):
    organization = make_organization()
    chat_id = 123
    user_1 = make_user_for_organization(organization)
    make_telegram_user_connector(user_1, telegram_chat_id=chat_id)

    user_2 = make_user_for_organization(organization)
    code = make_telegram_verification_code(user_2)
    connector, created = TelegramVerificationCode.verify_user(code.uuid_with_org_uuid, chat_id, "nickname")

    assert created
    assert connector.telegram_chat_id == chat_id
    assert connector.user == user_2


@pytest.mark.django_db
def test_user_verification_handler_process_update_user_already_linked(
    make_organization,
    make_user_for_organization,
    make_telegram_user_connector,
    make_telegram_verification_code,
):
    organization = make_organization()
    chat_id = 123
    user_1 = make_user_for_organization(organization)
    make_telegram_user_connector(user_1, telegram_chat_id=chat_id)

    other_chat_id = 321
    code = make_telegram_verification_code(user_1)
    connector, created = TelegramVerificationCode.verify_user(code.uuid_with_org_uuid, other_chat_id, "nickname")

    assert created is False
    assert connector.user == user_1
    assert connector.telegram_chat_id == chat_id
