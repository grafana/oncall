from django.core.management import BaseCommand
from django.db import connection
from django.db.migrations import Migration
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.writer import MigrationWriter

from common.migrations.remove_field import RemoveFieldDB, RemoveFieldState


class Command(BaseCommand):
    """
    Generate two migrations that remove a field from the state and the database separately.
    This allows removing a field in 2 separate releases and avoid downtime.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "args", nargs=3, help="app_label model_name field_name, example: alerts AlertReceiveChannel restricted_at"
        )

    def handle(self, *args, **options):
        app_label, model_name, field_name = args

        # Check that the app, the model, and the field to be removed exist
        project_state = MigrationLoader(connection).project_state()
        model_state = project_state.apps.get_model(app_label, model_name)
        model_state._meta.get_field(field_name)

        # Write migration that removes the field from the state
        remove_state_migration = self.write_operation(
            app_label, RemoveFieldState(model_name=model_name, name=field_name), project_state
        )

        # Write migration that removes the field from the database
        self.write_operation(
            app_label,
            RemoveFieldDB(
                model_name=model_name, name=field_name, remove_state_migration=(app_label, remove_state_migration.name)
            ),
            project_state,
        )

    @staticmethod
    def write_operation(app_label, operation, project_state):
        """
        Some Django magic to write a single-operation migration to a file, so it's similar to what Django would generate
        when running the "makemigrations" command.
        """

        migration_class = type("Migration", (Migration,), {"operations": [operation]})

        changes = MigrationAutodetector(project_state, project_state).arrange_for_graph(
            changes={app_label: [migration_class(None, app_label)]},
            graph=MigrationLoader(connection).graph,
            migration_name=operation.migration_name_fragment,
        )

        migration = changes[app_label][0]
        writer = MigrationWriter(migration)
        with open(writer.path, "w", encoding="utf-8") as file:
            file.write(writer.as_string())

        return migration
