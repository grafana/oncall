from .models import Organization


class OrganizationDeletedException(Exception):
    def __init__(self, organization: Organization):
        self.organization = organization


class OrganizationMovedException(Exception):
    def __init__(self, organization: Organization):
        self.organization = organization
