from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Kitchen, KitchenOrder
from .vectorstore import query_orders, reset_vector_store


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

    def test_order_details_page_loads(self):
        kitchen = Kitchen.objects.create(name='Main Kitchen', member=3)
        order = KitchenOrder.objects.create(
            kitchen=kitchen,
            customer_name='Alice',
            item_name='Burger',
            quantity=2,
            notes='No onions',
        )

        response = self.client.get(reverse('view_kitchen_order', args=[order.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['order'], order)
        self.assertContains(response, 'No onions')

    def test_missing_order_details_return_404(self):
        response = self.client.get(reverse('view_kitchen_order', args=[999]))
        self.assertEqual(response.status_code, 404)

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
                'status': 'pending',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(KitchenOrder.objects.filter(customer_name='Alice').exists())

    def test_order_status_can_be_updated(self):
        kitchen = Kitchen.objects.create(name='Main Kitchen', member=3)
        order = KitchenOrder.objects.create(
            kitchen=kitchen,
            customer_name='Alice',
            item_name='Burger',
        )

        response = self.client.post(
            reverse('update_order_status', args=[order.pk]),
            {'status': 'preparing'},
        )

        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, 'preparing')

    def test_invalid_order_status_is_rejected(self):
        kitchen = Kitchen.objects.create(name='Main Kitchen', member=3)
        order = KitchenOrder.objects.create(
            kitchen=kitchen,
            customer_name='Alice',
            item_name='Burger',
        )

        response = self.client.post(
            reverse('update_order_status', args=[order.pk]),
            {'status': 'invalid'},
        )

        self.assertEqual(response.status_code, 400)
        order.refresh_from_db()
        self.assertEqual(order.status, 'pending')


class OrderVectorStoreTests(TestCase):
    def setUp(self):
        self._tmpdir = TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.addCleanup(reset_vector_store)
        chroma_dir = Path(self._tmpdir.name)
        settings_override = override_settings(
            VECTOR_STORE_ENABLED=True,
            VECTOR_STORE_DIR=chroma_dir,
        )
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        reset_vector_store()

        self.kitchen = Kitchen.objects.create(name='Main Kitchen', member=3)

    def test_created_order_is_stored_in_vector_db(self):
        KitchenOrder.objects.create(
            kitchen=self.kitchen,
            customer_name='Alice',
            item_name='Mushroom risotto',
            quantity=2,
            notes='No garlic',
        )

        matches = query_orders('risotto without garlic', n_results=3)

        self.assertEqual(len(matches), 1)
        self.assertIn('Mushroom risotto', matches[0]['document'])
        self.assertEqual(matches[0]['metadata']['customer_name'], 'Alice')

    def test_deleted_order_is_removed_from_vector_db(self):
        order = KitchenOrder.objects.create(
            kitchen=self.kitchen,
            customer_name='Bob',
            item_name='Soup',
        )
        order.delete()

        self.assertEqual(query_orders('soup', n_results=3), [])
