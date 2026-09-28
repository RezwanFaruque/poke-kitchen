from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Kitchen, KitchenOrder
from .vectorstore import query_orders, reset_vector_store


class AuthenticationTests(TestCase):
    def test_registration_creates_account_and_logs_user_in(self):
        response = self.client.post(
            reverse('register'),
            {
                'email': 'Chef@example.com',
                'password1': 'secure-password-123',
                'password2': 'secure-password-123',
            },
        )

        self.assertRedirects(response, reverse('home'))
        user = get_user_model().objects.get(email='chef@example.com')
        self.assertEqual(user.username, 'chef@example.com')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_registration_rejects_duplicate_email_case_insensitively(self):
        get_user_model().objects.create_user(
            username='existing@example.com',
            email='existing@example.com',
            password='secure-password-123',
        )

        response = self.client.post(
            reverse('register'),
            {
                'email': 'EXISTING@example.com',
                'password1': 'secure-password-123',
                'password2': 'secure-password-123',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'An account with this email already exists.')

    def test_login_uses_email_and_password(self):
        get_user_model().objects.create_user(
            username='chef@example.com',
            email='chef@example.com',
            password='secure-password-123',
        )

        response = self.client.post(
            reverse('login'),
            {'username': 'CHEF@example.com', 'password': 'secure-password-123'},
        )

        self.assertRedirects(response, reverse('home'))
        self.assertIn('_auth_user_id', self.client.session)

    def test_login_rejects_incorrect_password(self):
        get_user_model().objects.create_user(
            username='chef@example.com',
            email='chef@example.com',
            password='secure-password-123',
        )

        response = self.client.post(
            reverse('login'),
            {'username': 'chef@example.com', 'password': 'wrong-password'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_requires_post_and_ends_session(self):
        user = get_user_model().objects.create_user(
            username='chef@example.com',
            email='chef@example.com',
            password='secure-password-123',
        )
        self.client.force_login(user)

        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)


class RestaurantsUrlTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='owner@example.com',
            email='owner@example.com',
            password='secure-password-123',
        )
        self.client.force_login(self.user)

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
            created_by=self.user,
        )

        response = self.client.get(reverse('view_kitchen_order', args=[order.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['order'], order)
        self.assertContains(response, 'No onions')

    def test_missing_order_details_return_404(self):
        response = self.client.get(reverse('view_kitchen_order', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_user_sees_only_their_orders(self):
        kitchen = Kitchen.objects.create(name='Main Kitchen', member=3)
        other_user = get_user_model().objects.create_user(
            username='other@example.com',
            email='other@example.com',
            password='secure-password-123',
        )
        KitchenOrder.objects.create(
            kitchen=kitchen,
            customer_name='Alice',
            item_name='My order',
            created_by=self.user,
        )
        other_order = KitchenOrder.objects.create(
            kitchen=kitchen,
            customer_name='Bob',
            item_name='Private order',
            created_by=other_user,
        )

        response = self.client.get(reverse('kitchen_orders'))

        self.assertContains(response, 'My order')
        self.assertNotContains(response, 'Private order')
        self.assertEqual(
            self.client.get(reverse('view_kitchen_order', args=[other_order.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(
                reverse('update_order_status', args=[other_order.pk]),
                {'status': 'ready'},
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(reverse('delete_kitchen_order', args=[other_order.pk])).status_code,
            404,
        )
        self.assertTrue(KitchenOrder.objects.filter(pk=other_order.pk).exists())

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
        order = KitchenOrder.objects.get(customer_name='Alice')
        self.assertEqual(order.created_by, self.user)

    def test_order_status_can_be_updated(self):
        kitchen = Kitchen.objects.create(name='Main Kitchen', member=3)
        order = KitchenOrder.objects.create(
            kitchen=kitchen,
            customer_name='Alice',
            item_name='Burger',
            created_by=self.user,
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
            created_by=self.user,
        )

        response = self.client.post(
            reverse('update_order_status', args=[order.pk]),
            {'status': 'invalid'},
        )

        self.assertEqual(response.status_code, 400)
        order.refresh_from_db()
        self.assertEqual(order.status, 'pending')

    def test_order_can_be_deleted_from_list(self):
        kitchen = Kitchen.objects.create(name='Main Kitchen', member=3)
        order = KitchenOrder.objects.create(
            kitchen=kitchen,
            customer_name='Alice',
            item_name='Burger',
            created_by=self.user,
        )

        response = self.client.post(
            reverse('delete_kitchen_order', args=[order.pk]),
            {'next': reverse('kitchen_orders')},
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('kitchen_orders'))
        self.assertFalse(KitchenOrder.objects.filter(pk=order.pk).exists())

    def test_missing_order_delete_returns_404(self):
        response = self.client.post(reverse('delete_kitchen_order', args=[999]))
        self.assertEqual(response.status_code, 404)


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
