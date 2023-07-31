import logging

from django.db import models

logger = logging.getLogger(__name__)


def sync_regions(regions: list[dict]):
    from apps.user_management.models import Region

    gcom_regions = {region["slug"]: region for region in regions}
    existing_region_slugs = set(Region.objects.all().values_list("slug", flat=True))

    # create new regions
    regions_to_create = tuple(
        Region(
            name=region["name"],
            slug=region["slug"],
            oncall_backend_url=region["oncallApiUrl"],
        )
        for region in gcom_regions.values()
        if region["slug"] not in existing_region_slugs
    )
    Region.objects.bulk_create(regions_to_create, batch_size=5000)

    # delete excess regions
    regions_to_delete = existing_region_slugs - gcom_regions.keys()
    Region.objects.filter(slug__in=regions_to_delete).delete()

    # update existing regions
    regions_to_update = []
    for region in Region.objects.filter(slug__in=existing_region_slugs):
        gcom_region = gcom_regions[region.slug]
        if region.name != gcom_region["name"] or region.oncall_backend_url != gcom_region["oncallApiUrl"]:
            region.name = gcom_region["name"]
            region.oncall_backend_url = gcom_region["oncallApiUrl"]
            regions_to_update.append(region)

    Region.objects.bulk_update(regions_to_update, ["name", "oncall_backend_url"], batch_size=5000)


class Region(models.Model):
    name = models.CharField(max_length=300)
    slug = models.CharField(max_length=50, unique=True)
    oncall_backend_url = models.URLField(null=True)
