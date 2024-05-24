import pytest
from django.db.utils import IntegrityError


@pytest.mark.django_db
def test_team_uniqueness(make_organization):
    organization = make_organization()

    # Create a team
    organization.teams.create(name="Team 1", team_id=1)

    # Try to create another team with the same team_id
    with pytest.raises(IntegrityError):
        organization.teams.create(name="Team 2", team_id=1)
