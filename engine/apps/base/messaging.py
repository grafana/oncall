from django.conf import settings
from django.utils.module_loading import import_string


class BaseMessagingBackend:
    backend_id = "SOMEID"
    label = "The Backend"
    short_label = "Backend"
    available_for_use = False
    templater = None

    def get_templater_class(self):
        if self.templater:
            return import_string(self.templater)

    def validate_channel_filter_data(self, channel_filter, data):
        """Validate JSON channel data for a channel filter update.

        Ensure the required/expected data is provided as needed by the backend.

        """
        return data

    def generate_channel_verification_code(self, organization):
        """Return a verification code for a channel registration."""
        raise NotImplementedError("generate_channel_verification_code method missing implementation")

    def generate_user_verification_code(self, user):
        """Return a verification code to link a user with an account."""
        raise NotImplementedError("generate_user_verification_code method missing implementation")

    def unlink_user(self, user):
        """Remove backend link to user account."""
        return

    def serialize_user(self, user):
        """Return a serialized backend user representation."""
        raise NotImplementedError("serialize_user method missing implementation")

    def notify_user(self, user, alert_group, notification_policy):
        """Send user a notification for the given alert group.

        The notification policy links to the backend as the notification channel.

        """
        raise NotImplementedError("notify_user method missing implementation")


def load_backend(path):
    return import_string(path)()


def get_messaging_backends():
    global _messaging_backends
    if not settings.FEATURE_EXTRA_MESSAGING_BACKENDS_ENABLED:
        return {}

    if _messaging_backends is None:
        _messaging_backends = {}
        for backend_path in settings.EXTRA_MESSAGING_BACKENDS:
            backend = load_backend(backend_path)
            _messaging_backends[backend.backend_id] = backend
    return _messaging_backends.items()


def get_messaging_backend_from_id(backend_id):
    backend = None
    if settings.FEATURE_EXTRA_MESSAGING_BACKENDS_ENABLED:
        backend = _messaging_backends.get(backend_id)
    return backend


_messaging_backends = None
