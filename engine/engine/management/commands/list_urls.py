from django.core.management.base import BaseCommand
from django.urls import get_resolver

class Command(BaseCommand):
    help = 'List all URL paths in the project'

    def handle(self, *args, **kwargs):
        resolver = get_resolver()
        urls = resolver.url_patterns
        for url in self.extract_urls(urls):
            self.stdout.write(url)

    def extract_urls(self, urlpatterns, prefix=''):
        url_list = []
        for pattern in urlpatterns:
            if hasattr(pattern, 'url_patterns'):
                # Include namespace in the prefix if available
                namespace = pattern.namespace or ''
                if namespace:
                    namespace += ':'
                url_list.extend(self.extract_urls(pattern.url_patterns, prefix + namespace))
            else:
                url_list.append(prefix + str(pattern.pattern))
        return url_list
