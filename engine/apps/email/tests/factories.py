import factory

from apps.email.models import EmailMessage


class EmailMessageFactory(factory.DjangoModelFactory):
    class Meta:
        model = EmailMessage
