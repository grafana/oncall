import logging

from django.conf import settings
from django.shortcuts import resolve_url
from django.utils.encoding import force_text
from django.utils.functional import Promise
from social_django.strategy import DjangoStrategy

from apps.base.utils import live_settings
from common.api_helpers.utils import create_engine_url

logger = logging.getLogger(__name__)


class LiveSettingDjangoStrategy(DjangoStrategy):
    """
    This strategy is used for social auth.

    It allows to give aliases to original social auth settings and take them from live settings by these aliases.
    Originally it was introduced for onprem to make names of social auth settings more obvious for users.
    """

    def get_setting(self, name):
        name_to_live_setting_map = settings.SOCIAL_AUTH_SETTING_NAME_TO_LIVE_SETTING_NAME
        if name in name_to_live_setting_map:
            value = getattr(live_settings, name_to_live_setting_map[name])
        else:
            value = getattr(settings, name)
        # Force text on URL named settings that are instance of Promise
        if name.endswith("_URL"):
            if isinstance(value, Promise):
                value = force_text(value)
            value = resolve_url(value)
        return value

    def build_absolute_uri(self, path=None):
        """
        Overridden DjangoStrategy's method to substitute and force the host value from ENV
        """
        if live_settings.SLACK_INSTALL_RETURN_REDIRECT_HOST is not None and path is not None:
            return create_engine_url(path, override_base=live_settings.SLACK_INSTALL_RETURN_REDIRECT_HOST)
        if self.request:
            return self.request.build_absolute_uri(path)
        else:
            return path
