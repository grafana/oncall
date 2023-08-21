from django.conf import settings
from django.utils.module_loading import import_string


class BaseMessagingBackend:
    backend_id = "SOMEID"
    label = "The Backend"
    short_label = "Backend"
    available_for_use = False

    templater = None
    template_fields = ("title", "message", "image_url")

    def __init__(self, *args, **kwargs):
        self.notification_channel_id = kwargs.get("notification_channel_id")

    def get_templater_class(self):
        if self.templater:
            return import_string(self.templater)

    def validate_channel_filter_data(self, organization, data):
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

    @staticmethod
    def is_enabled_for_organization(organization):
        return True

    def serialize_user(self, user):
        """Return a serialized backend user representation."""
        raise NotImplementedError("serialize_user method missing implementation")

    def notify_user(self, user, alert_group, notification_policy):
        """Send user a notification for the given alert group.

        The notification policy links to the backend as the notification channel.

        """
        raise NotImplementedError("notify_user method missing implementation")

    @property
    def slug(self):
        return self.backend_id.lower()

    @property
    def customizable_templates(self):
        """
        customizable_templates indicates if templates for messaging backend can be changes by user
        """
        return True


def load_backend(path, *args, **kwargs):
    return import_string(path)(*args, **kwargs)


def get_messaging_backends():
    global _messaging_backends
    if _messaging_backends is None:
        _messaging_backends = {}
        for backend_path, notification_channel_id in settings.EXTRA_MESSAGING_BACKENDS:
            backend = load_backend(backend_path, notification_channel_id=notification_channel_id)
            _messaging_backends[backend.backend_id] = backend
    return _messaging_backends.items()


def get_messaging_backend_from_id(backend_id):
    return _messaging_backends.get(backend_id)


_messaging_backends = None
