from common.api_helpers.optional_slash_router import optional_slash_path

from .views.customers_migration_tool import MigrateAPIView, MigrationPlanAPIView, MigrationStatusAPIView

app_name = "migration-tool"


urlpatterns = [
    optional_slash_path("amixr_migration_plan", MigrationPlanAPIView.as_view(), name="amixr_migration_plan"),
    optional_slash_path("migrate_from_amixr", MigrateAPIView.as_view(), name="migrate_from_amixr"),
    optional_slash_path("amixr_migration_status", MigrationStatusAPIView.as_view(), name="amixr_migration_status"),
]
