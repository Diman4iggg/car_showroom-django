import pytest

from .models import phone_validator


@pytest.mark.parametrize('phone', [
    '+375 (29) 123-45-67',
    '+375 (33) 111-22-33',
    '+375 (44) 999-88-77',
])
def test_phone_validator_accepts_mobile_operator_codes(phone):
    phone_validator(phone)
