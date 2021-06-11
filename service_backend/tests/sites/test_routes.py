"""Functional tests using pytest-flask."""
from uuid import uuid4

from pytest import mark
from . import asserts

flavor_1 = {'name': 'f1', 'description': "text"}
flavor_2 = {'name': 'f2', 'description': "text"}
flavor_3 = {'name': 'f3', 'description': "text"}

site_1 = {'name': "s1", 'address': "addr1"}
site_1['description'] = "text"
site_1['flavors'] = []
site_1['flavors__description'] = ["site1 flavor"]

site_2 = {'name': "s2", 'address': "addr1"}
site_2['description'] = "text"
site_2['flavors'] = ["f1"]
site_2['flavors__description'] = ["site2 flavor"]


@mark.usefixtures('session', 'db_sites')
@mark.parametrize('endpoint', ['sites.Root'], indirect=True)
@mark.parametrize('db_sites', indirect=True, argvalues=[
    [site_1, site_2]
])
class TestRoot:
    """Tests for 'Root' route in blueprint."""

    @mark.usefixtures('grant_logged')
    @mark.parametrize('query', indirect=True, argvalues=[
        {'name': 's1', 'address': "addr1"},
        {'address': "addr1"},  # Query with 1 field
        {}  # Multiple results
    ])
    def test_GET_200(self, response_GET, url):
        """GET method succeeded 200."""
        assert response_GET.status_code == 200
        for element in response_GET.json:
            asserts.correct_site(element)
            asserts.match_query(element, url)

    @mark.parametrize('query', indirect=True, argvalues=[
        {'name': 's1'}
    ])
    def test_GET_401(self, response_GET):
        """GET method fails 401 if not logged in."""
        assert response_GET.status_code == 401

    @mark.usefixtures('grant_logged')
    @mark.parametrize('query', indirect=True, argvalues=[
        {'bad_key': "This is a non expected query key"}
    ])
    def test_GET_422(self, response_GET):
        """GET method fails 422 if bad request body."""
        assert response_GET.status_code == 422

    @mark.usefixtures('grant_logged')
    @mark.parametrize('body', indirect=True, argvalues=[
        {'name': "s3", 'address': "addr2", 'description': "Text"},
        {'name': "s3", 'address': "addr2", 'flavors': [
            {'name': 'f1', 'description': "text"},
            {'name': 'f2', 'description': "text"}
        ]}
    ])
    def test_POST_201(self, response_POST, url, body):
        """POST method succeeded 201."""
        assert response_POST.status_code == 201
        asserts.correct_site(response_POST.json)
        asserts.match_query(response_POST.json, url)
        asserts.match_body(response_POST.json, body)

    @mark.parametrize('body', indirect=True, argvalues=[
        {'name': "s3", 'address': "addr2", 'description': "Text"},
        {}  # Empty body
    ])
    def test_POST_401(self, response_POST):
        """POST method fails 401 if not authorized."""
        assert response_POST.status_code == 401

    @mark.usefixtures('grant_logged')
    @mark.parametrize('body', indirect=True, argvalues=[
        {'name': "s1", 'address': "addrX"},
        {'name': "s2", 'address': "addrX"}
    ])
    def test_POST_409(self, response_POST):
        """POST method fails 409 if resource already exists."""
        assert response_POST.status_code == 409

    @mark.usefixtures('grant_logged')
    @mark.parametrize('body', indirect=True, argvalues=[
        {'name': "site"},  # Missingaddress
        {'address': "address"},  # Missingname
        {}  # Empty body
    ])
    def test_POST_422(self, response_POST):
        """POST method fails 422 if missing required."""
        assert response_POST.status_code == 422


@mark.usefixtures('session', 'site')
@mark.parametrize('endpoint', ['sites.Site'], indirect=True)
@mark.parametrize('site_id', [uuid4()], indirect=True)
class TestSite:
    """Tests for 'Site' route in blueprint."""

    def test_GET_200(self, site, response_GET):
        """GET method succeeded 200."""
        assert response_GET.status_code == 200
        asserts.correct_site(response_GET.json)
        asserts.match_site(response_GET.json, site)

    @mark.parametrize('site__id', [uuid4()])
    def test_GET_404(self, response_GET):
        """GET method fails 404 if no id found."""
        assert response_GET.status_code == 404

    @mark.usefixtures('grant_admin')
    @mark.parametrize('body', indirect=True, argvalues=[
        {'name': "new_name", 'address': "addr1"},
        {'name': "new_name"},
        {'address': "new_addr"}
    ])
    def test_PUT_204(self, response_PUT, response_GET, body):
        """PUT method succeeded 204."""
        assert response_PUT.status_code == 204
        assert response_GET.status_code == 200
        asserts.correct_site(response_GET.json)
        asserts.match_body(response_GET.json, body)

    @mark.parametrize('body', indirect=True, argvalues=[
        {'name': 'new_name', 'address': "new_addr"}
    ])
    def test_PUT_401(self, response_PUT):
        """PUT method fails 401 if not authorized."""
        assert response_PUT.status_code == 401

    @mark.usefixtures('grant_admin')
    @mark.parametrize('site__id', [uuid4()])
    @mark.parametrize('body', indirect=True, argvalues=[
        {'name': 'new_name', 'address': "new_addr"}
    ])
    def test_PUT_404(self, response_PUT):
        """PUT method fails 404 if no id found."""
        assert response_PUT.status_code == 404

    @mark.usefixtures('grant_admin')
    @mark.parametrize('body', indirect=True, argvalues=[
        {'bad_field': ""}
    ])
    def test_PUT_422(self, response_PUT):
        """PUT method fails 422 if bad request body."""
        assert response_PUT.status_code == 422

    @mark.usefixtures('grant_admin')
    def test_DELETE_204(self, response_DELETE, response_GET):
        """DELETE method succeeded 204."""
        assert response_DELETE.status_code == 204
        assert response_GET.status_code == 404

    def test_DELETE_401(self, response_DELETE):
        """DELETE method fails 401 if not authorized."""
        assert response_DELETE.status_code == 401

    @mark.usefixtures('grant_admin')
    @mark.parametrize('site__id', [uuid4()])
    def test_DELETE_404(self, response_DELETE):
        """DELETE method fails 404 if no id found."""
        assert response_DELETE.status_code == 404


@mark.usefixtures('session', 'site', 'db_flavors')
@mark.parametrize('endpoint', ['sites.Flavors'], indirect=True)
@mark.parametrize('site_id', [uuid4()], indirect=True)
@mark.parametrize('db_flavors', indirect=True, argvalues=[
    [flavor_1, flavor_2]
])
class TestFlavors:
    """Tests for 'Flavors' route in blueprint."""

    @mark.usefixtures('grant_logged')
    @mark.parametrize('query', indirect=True, argvalues=[
        {'name': 'f1'},
        {'name': 'f2'},
        {}  # Multiple results
    ])
    def test_GET_200(self, response_GET, url):
        """GET method succeeded 200."""
        assert response_GET.status_code == 200
        for element in response_GET.json:
            asserts.correct_flavor(element)
            asserts.match_query(element, url)

    @mark.parametrize('query', indirect=True, argvalues=[
        {'name': 'f1'}
    ])
    def test_GET_401(self, response_GET):
        """GET method fails 401 if not logged in."""
        assert response_GET.status_code == 401

    @mark.usefixtures('grant_logged')
    @mark.parametrize('query', indirect=True, argvalues=[
        {'bad_key': "This is a non expected query key"}
    ])
    def test_GET_422(self, response_GET):
        """GET method fails 422 if bad request body."""
        assert response_GET.status_code == 422

    @mark.usefixtures('grant_logged')
    @mark.parametrize('body', indirect=True, argvalues=[
        flavor_3
    ])
    def test_POST_201(self, response_POST, url, body):
        """POST method succeeded 201."""
        assert response_POST.status_code == 201
        asserts.correct_flavor(response_POST.json)
        asserts.match_query(response_POST.json, url)
        asserts.match_body(response_POST.json, body)
        asserts.site_has_flavor(response_POST.json, url)

    @mark.parametrize('body', indirect=True, argvalues=[
        flavor_3,
        {}  # Empty body
    ])
    def test_POST_401(self, response_POST):
        """POST method fails 401 if not authorized."""
        assert response_POST.status_code == 401

    @mark.usefixtures('grant_logged')
    @mark.parametrize('body', indirect=True, argvalues=[
        flavor_1,
        flavor_2
    ])
    def test_POST_409(self, response_POST):
        """POST method fails 409 if resource already exists."""
        assert response_POST.status_code == 409

    @mark.usefixtures('grant_logged')
    @mark.parametrize('body', indirect=True, argvalues=[
        {k: flavor_1[k] for k in flavor_1.keys() - {'name'}},  # Missingname
        {}  # Empty body
    ])
    def test_POST_422(self, response_POST):
        """POST method fails 422 if missing required."""
        assert response_POST.status_code == 422


@mark.usefixtures('session', 'site', 'flavor')
@mark.parametrize('endpoint', ['sites.Flavor'], indirect=True)
@mark.parametrize('site_id', [uuid4()], indirect=True)
@mark.parametrize('flavor_name', ["f1"], indirect=True)
class TestFlavor:
    """Tests for 'Flavor' route in blueprint."""

    def test_GET_200(self, flavor, response_GET):
        """GET method succeeded 200."""
        assert response_GET.status_code == 200
        asserts.correct_flavor(response_GET.json)
        asserts.match_flavor(response_GET.json, flavor)

    @mark.parametrize('flavor__name', ["f2"])
    def test_GET_404(self, response_GET):
        """GET method fails 404 if no id found."""
        assert response_GET.status_code == 404

    @mark.usefixtures('grant_admin')
    @mark.parametrize('body', indirect=True, argvalues=[
        {'description': "new_text"},
        {}  # Note, edit name changes url for response_GET
    ])
    def test_PUT_204(self, response_PUT, response_GET, body):
        """PUT method succeeded 204."""
        assert response_PUT.status_code == 204
        asserts.correct_flavor(response_GET.json)
        asserts.match_body(response_GET.json, body)

    @mark.parametrize('body', indirect=True, argvalues=[
        {'description': "new_text"}
    ])
    def test_PUT_401(self, response_PUT):
        """PUT method fails 401 if not authorized."""
        assert response_PUT.status_code == 401

    @mark.usefixtures('grant_admin')
    @mark.parametrize('flavor__name', ["f2"])
    @mark.parametrize('body', indirect=True, argvalues=[
        {'description': "new_text"}
    ])
    def test_PUT_404(self, response_PUT):
        """PUT method fails 404 if no id found."""
        assert response_PUT.status_code == 404

    @mark.usefixtures('grant_admin')
    @mark.parametrize('body', indirect=True, argvalues=[
        {'bad_field': ""}
    ])
    def test_PUT_422(self, response_PUT):
        """PUT method fails 422 if bad request body."""
        assert response_PUT.status_code == 422

    @mark.usefixtures('grant_admin')
    def test_DELETE_204(self, response_DELETE, response_GET):
        """DELETE method succeeded 204."""
        assert response_DELETE.status_code == 204
        assert response_GET.status_code == 404

    def test_DELETE_401(self, response_DELETE):
        """DELETE method fails 401 if not authorized."""
        assert response_DELETE.status_code == 401

    @mark.usefixtures('grant_admin')
    @mark.parametrize('flavor__name', ["f2"])
    def test_DELETE_404(self, response_DELETE):
        """DELETE method fails 404 if no id found."""
        assert response_DELETE.status_code == 404