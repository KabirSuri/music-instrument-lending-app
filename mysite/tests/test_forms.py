from django.test import TestCase
from ..forms import ItemForm
from ..models import Library, Item

class ItemFormTest(TestCase):
    def setUp(self):
        self.library = Library.objects.create(name='Test Library')

    def test_valid_item_form(self):
        form_data = {
            'title': 'Test Item',
            'primary_identifier': 'TEST123',
            'status': 'checked_in',
            'library': self.library.id
        }
        form = ItemForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_item_form_missing_title(self):
        form_data = {
            'primary_identifier': 'TEST123',
            'status': 'checked_in',
            'library': self.library.id
        }
        form = ItemForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_invalid_item_form_missing_primary_identifier(self):
        form_data = {
            'title': 'Test Item',
            'status': 'checked_in',
            'library': self.library.id
        }
        form = ItemForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('primary_identifier', form.errors)

    def test_invalid_item_form_missing_status(self):
        form_data = {
            'title': 'Test Item',
            'primary_identifier': 'TEST123',
            'library': self.library.id
        }
        form = ItemForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)

    def test_invalid_item_form_missing_library(self):
        form_data = {
            'title': 'Test Item',
            'primary_identifier': 'TEST123',
            'status': 'checked_in'
        }
        form = ItemForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('library', form.errors)

    def test_invalid_item_form_duplicate_primary_identifier(self):
        # Create an item first
        Item.objects.create(
            title='Existing Item',
            primary_identifier='TEST123',
            status='checked_in',
            library=self.library
        )

        # Try to create another item with the same primary identifier
        form_data = {
            'title': 'New Item',
            'primary_identifier': 'TEST123',
            'status': 'checked_in',
            'library': self.library.id
        }
        form = ItemForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('primary_identifier', form.errors)

    def test_item_form_save(self):
        form_data = {
            'title': 'Test Item',
            'primary_identifier': 'TEST123',
            'status': 'checked_in',
            'library': self.library.id
        }
        form = ItemForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        item = form.save()
        self.assertEqual(item.title, 'Test Item')
        self.assertEqual(item.primary_identifier, 'TEST123')
        self.assertEqual(item.status, 'checked_in')
        self.assertEqual(item.library, self.library) 