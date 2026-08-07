import pytest

from apps.notifications.clients.dto import SmsStatus
from apps.notifications.clients.errors import MessengerClientError, SmsClientError
from apps.notifications.clients.fake import FakeMessengerClient, FakeSmsClient


def test_sms_send_records_message() -> None:
    client = FakeSmsClient()

    result = client.send("+380671234567", "Ваше замовлення підтверджено")

    assert result.status == SmsStatus.SENT
    assert client.sent == [("+380671234567", "Ваше замовлення підтверджено")]


def test_sms_send_raises_on_fail_flag() -> None:
    with pytest.raises(SmsClientError):
        FakeSmsClient(fail=True).send("+380671234567", "text")


def test_messenger_send_message_records() -> None:
    client = FakeMessengerClient()

    client.send_message("123456", "Новий заказ")

    assert client.sent == [("123456", "Новий заказ")]


def test_messenger_send_message_raises_on_fail_flag() -> None:
    with pytest.raises(MessengerClientError):
        FakeMessengerClient(fail=True).send_message("123456", "text")
