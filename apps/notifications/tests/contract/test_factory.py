import pytest
from pytest_django.fixtures import Settings

from apps.notifications.clients.factory import get_messenger_client, get_sms_client
from apps.notifications.clients.fake import FakeMessengerClient, FakeSmsClient


def test_returns_fake_sms_client_when_configured(settings: Settings) -> None:
    settings.SMS_PROVIDER = "fake"

    assert isinstance(get_sms_client(), FakeSmsClient)


def test_returns_fake_messenger_client_when_configured(settings: Settings) -> None:
    settings.MESSENGER_PROVIDER = "fake"

    assert isinstance(get_messenger_client(), FakeMessengerClient)


def test_raises_for_unimplemented_sms_provider(settings: Settings) -> None:
    settings.SMS_PROVIDER = "turbosms"

    with pytest.raises(NotImplementedError):
        get_sms_client()
