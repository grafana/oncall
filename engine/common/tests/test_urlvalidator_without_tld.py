import pytest
from django.core.validators import ValidationError

from common.api_helpers.utils import URLValidatorWithoutTLD

valid_urls = ["https://www.google.com", "https://www.google", "http://conatainer1"]
invalid_urls = ["https:/www.google.com", "htt://www.google.com/"]


@pytest.mark.parametrize("url", valid_urls)
def test_urlvalidator_without_tld_valid_urls(url):
    # Test valid URLs
    URLValidatorWithoutTLD()(url)


@pytest.mark.parametrize("url", invalid_urls)
def test_urlvalidator_without_tld_invalid_urls(url):
    # Test an invalid URL
    with pytest.raises(ValidationError):
        URLValidatorWithoutTLD()(url)
