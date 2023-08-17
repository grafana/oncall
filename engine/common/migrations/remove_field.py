from django.db import connection
from django.db.migrations import RemoveField
from django.db.migrations.loader import MigrationLoader


class RemoveFieldState(RemoveField):
    """
    Remove field from Django's migration state, but not from the database.
    This is essentially the same as RemoveField, but database_forwards and database_backwards methods are modified
    to do nothing.
    """

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        pass

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        pass

    def describe(self):
        return f"{super().describe()} (state)"

    @property
    def migration_name_fragment(self):
        return f"{super().migration_name_fragment}_state"


class RemoveFieldDB(RemoveField):
    """
    Remove field from the database, but not from Django's migration state.
    This is implemented as a custom operation, because Django's RemoveField operation does not support
    removing fields from the database after it has been removed from the state. The workaround is to use the state
    that was in effect before the field was removed from the state (i.e. just before the RemoveFieldState migration).
    """

    def __init__(self, model_name, name, remove_state_migration):
        """
        Specifying "remove_state_migration" allows database operations to run against a particular historical state.
        Example: remove_state_migration = ("alerts", "0014_alertreceivechannel_restricted_at") will "trick" Django
        into thinking that the last applied migration in the "alerts" app is 0013.
        """
        super().__init__(model_name, name)
        self.remove_state_migration = remove_state_migration

    def deconstruct(self):
        """Update serialized representation of the operation."""
        deconstructed = super().deconstruct()
        return (
            deconstructed[0],
            deconstructed[1],
            deconstructed[2] | {"remove_state_migration": self.remove_state_migration}
        )

    def state_forwards(self, app_label, state):
        """Skip any state changes."""
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        # use historical state instead of what Django provides
        from_state = self.state_before_remove_state_migration

        super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        # use historical state instead of what Django provides
        to_state = self.state_before_remove_state_migration

        super().database_backwards(app_label, schema_editor, from_state, to_state)

    def describe(self):
        return f"{super().describe()} (db)"

    @property
    def migration_name_fragment(self):
        return f"{super().migration_name_fragment}_db"

    @property
    def state_before_remove_state_migration(self):
        """Get project state just before migration "remove_state_migration" was applied."""
        return MigrationLoader(connection).project_state(self.remove_state_migration, at_end=False)
