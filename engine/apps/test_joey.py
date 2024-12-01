def test_external_network_call():
    import requests

    response = requests.get('https://www.example.com')
    assert response.status_code == 200
