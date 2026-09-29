from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Kitchen, KitchenOrder
from .suggestions import generate_order_suggestion, retrieve_order_history


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
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Orders')
        self.assertContains(response, 'Log out')

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

    def test_create_order_form_renders_suggestion_controls(self):
        response = self.client.get(reverse('create_kitchen_order'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Order suggestion')
        self.assertContains(response, 'Use suggestion')

    def test_anonymous_order_page_redirects_to_project_login(self):
        self.client.logout()

        response = self.client.get(reverse('create_kitchen_order'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            f'{reverse("login")}?next={reverse("create_kitchen_order")}',
        )

    @patch('kitchines.views.generate_order_suggestion')
    @override_settings(GROQ_API_KEY='test-key')
    def test_order_suggestion_uses_current_user_and_selected_kitchen(self, suggest):
        kitchen = Kitchen.objects.create(name='Main Kitchen', member=3)
        suggest.return_value = {'item_name': 'Mushroom risotto', 'quantity': 2, 'notes': 'No garlic'}

        response = self.client.post(
            reverse('order_suggestions'),
            {'kitchen_id': kitchen.pk, 'item_name': 'risotto', 'notes': 'no garlic'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['suggestion']['item_name'], 'Mushroom risotto')
        suggest.assert_called_once_with(
            'Kitchen: Main Kitchen. Item: risotto. Notes: no garlic',
            self.user.pk,
            kitchen.pk,
        )

    @override_settings(GROQ_API_KEY='')
    def test_order_suggestion_reports_missing_groq_key(self):
        kitchen = Kitchen.objects.create(name='Main Kitchen', member=3)

        response = self.client.post(
            reverse('order_suggestions'),
            {'kitchen_id': kitchen.pk, 'item_name': 'Soup', 'notes': ''},
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn('GROQ_API_KEY', response.json()['message'])

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


class OrderSuggestionTests(TestCase):
    def setUp(self):
        self.kitchen = Kitchen.objects.create(name='Main Kitchen', member=3)
        self.user = get_user_model().objects.create_user(username='chef@example.com')

    def test_history_is_scoped_to_current_user_and_kitchen(self):
        other_user = get_user_model().objects.create_user(username='other@example.com')
        other_kitchen = Kitchen.objects.create(name='Other Kitchen')
        KitchenOrder.objects.create(
            kitchen=self.kitchen,
            customer_name='Alice',
            item_name='Mushroom risotto',
            created_by=self.user,
        )
        KitchenOrder.objects.create(
            kitchen=self.kitchen,
            customer_name='Bob',
            item_name='Soup',
            created_by=other_user,
        )
        KitchenOrder.objects.create(
            kitchen=other_kitchen,
            customer_name='Carol',
            item_name='Pasta',
            created_by=self.user,
        )

        history = retrieve_order_history(self.user.pk, self.kitchen.pk)

        self.assertEqual(history, [{'item_name': 'Mushroom risotto', 'quantity': 1, 'notes': ''}])

    @patch('kitchines.suggestions._suggestion_chain')
    @override_settings(GROQ_API_KEY='test-key')
    def test_suggestion_passes_retrieved_order_context_to_langchain(self, chain_factory):
        KitchenOrder.objects.create(
            kitchen=self.kitchen,
            customer_name='Private customer',
            item_name='Mushroom risotto',
            quantity=2,
            notes='No garlic',
            created_by=self.user,
        )
        generated_order = {'item_name': 'Mushroom risotto', 'quantity': 2, 'notes': 'No garlic'}
        chain_factory.return_value.invoke.return_value = generated_order

        suggestion = generate_order_suggestion('risotto without garlic', self.user.pk, self.kitchen.pk)

        self.assertEqual(suggestion, generated_order)
        chain_factory.assert_called_once_with('test-key', 'openai/gpt-oss-20b')
        chain_factory.return_value.invoke.assert_called_once_with(
            {
                'query': 'risotto without garlic',
                'history': '[{"item_name": "Mushroom risotto", "quantity": 2, "notes": "No garlic"}]',
            },
        )

    @patch('kitchines.suggestions._suggestion_chain')
    @override_settings(GROQ_API_KEY='')
    def test_suggestion_skips_hosted_model_without_api_key(self, chain_factory):
        KitchenOrder.objects.create(
            kitchen=self.kitchen,
            customer_name='Alice',
            item_name='Soup',
            created_by=self.user,
        )

        suggestion = generate_order_suggestion('soup', self.user.pk, self.kitchen.pk)

        self.assertIsNone(suggestion)
        chain_factory.assert_not_called()

    @patch('kitchines.suggestions._suggestion_chain')
    @override_settings(GROQ_API_KEY='test-key')
    def test_suggestion_skips_model_when_user_has_no_order_history(self, chain_factory):
        suggestion = generate_order_suggestion('soup', self.user.pk, self.kitchen.pk)

        self.assertIsNone(suggestion)
        chain_factory.assert_not_called()

    @patch('kitchines.suggestions._suggestion_chain')
    @override_settings(GROQ_API_KEY='test-key')
    def test_groq_error_logs_provider_message(self, chain_factory):
        KitchenOrder.objects.create(
            kitchen=self.kitchen,
            customer_name='Alice',
            item_name='Soup',
            created_by=self.user,
        )
        error = RuntimeError('Error code: 400')
        error.status_code = 400
        error.body = {'error': {'message': 'The selected model is unavailable.'}}
        chain_factory.return_value.invoke.side_effect = error

        with self.assertLogs('kitchines.suggestions', level='ERROR') as logs:
            suggestion = generate_order_suggestion('soup', self.user.pk, self.kitchen.pk)

        self.assertIsNone(suggestion)
        self.assertIn('The selected model is unavailable.', '\n'.join(logs.output))
