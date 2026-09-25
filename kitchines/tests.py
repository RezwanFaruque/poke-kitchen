from django.test import TestCase
from django.urls import reverse


class RestaurantsUrlTests(TestCase):
    def test_homepage_redirects_or_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_restaurants_page_loads(self):
        response = self.client.get(reverse('restaruant'))
        self.assertEqual(response.status_code, 200)
