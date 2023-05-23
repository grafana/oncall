from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    """
    Create SQLite3 database file if it doesn't exist.
    """

    def handle(self, *args, **options):
        assert settings.DATABASE_TYPE == "sqlite3"

        # Creating a cursor creates the database file if it doesn't exist.
        connection.cursor()
