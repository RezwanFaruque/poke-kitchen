from django.test import TestCase
from django.urls import reverse

from .models import Kitchen, KitchenOrder


class RestaurantsUrlTests(TestCase):
    def test_homepage_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_restaurants_page_loads(self):
        response = self.client.get(reverse('restaurants'))
        self.assertEqual(response.status_code, 200)

    def test_kitchen_orders_page_loads(self):
        response = self.client.get(reverse('kitchen_orders'))
        self.assertEqual(response.status_code, 200)

    def test_order_can_be_created(self):
        kitchen = Kitchen.objects.create(name='Main Kitchen', member=3)
        response = self.client.post(
            reverse('create_kitchen_order'),
            {
                'kitchen': kitchen.pk,
                'customer_name': 'Alice',
                'item_name': 'Burger',
                'quantity': 2,
                'notes': 'No onions',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(KitchenOrder.objects.filter(customer_name='Alice').exists())
