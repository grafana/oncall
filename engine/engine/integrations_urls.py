from django.urls import URLPattern, URLResolver, include, path

from .urls import paths_to_work_even_when_maintenance_mode_is_active

urlpatterns: list[URLPattern | URLResolver] = paths_to_work_even_when_maintenance_mode_is_active

urlpatterns += [
    path("integrations/v1/", include("apps.integrations.urls", namespace="integrations")),
]
