from django.conf import settings


def custom_preprocessing_hook(endpoints):
    filtered = []
    for path, path_regex, method, callback in endpoints:
        if any(path_prefix in path for path_prefix in settings.SPECTACULAR_INCLUDED_PATHS):
            filtered.append((path, path_regex, method, callback))
    return filtered
