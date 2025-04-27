from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import UserProfile, Library, Item, Collection, ItemImage
from django.utils import timezone
from django.conf import settings

class UserProfileTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.profile = self.user.profile

    def test_profile_creation(self):
        self.assertTrue(isinstance(self.profile, UserProfile))
        self.assertEqual(self.profile.user, self.user)
        self.assertFalse(self.profile.is_librarian)

    def test_profile_str(self):
        self.assertEqual(str(self.profile), self.user.email)

class LibraryTest(TestCase):
    def setUp(self):
        self.library = Library.objects.create(
            name='Test Library',
            description='Test Description'
        )

    def test_library_creation(self):
        self.assertEqual(self.library.name, 'Test Library')
        self.assertEqual(self.library.description, 'Test Description')

    def test_library_str(self):
        self.assertEqual(str(self.library), 'Test Library')

class ItemTest(TestCase):
    def setUp(self):
        self.library = Library.objects.create(name='Test Library')
        self.item = Item.objects.create(
            title='Test Item',
            primary_identifier='TEST123',
            status='checked_in',
            library=self.library
        )

    def test_item_creation(self):
        self.assertEqual(self.item.title, 'Test Item')
        self.assertEqual(self.item.primary_identifier, 'TEST123')
        self.assertEqual(self.item.status, 'checked_in')
        self.assertEqual(self.item.library, self.library)

    def test_item_str(self):
        self.assertEqual(str(self.item), 'Test Item')

class ItemImageTest(TestCase):
    def setUp(self):
        self.library = Library.objects.create(name='Test Library')
        self.item = Item.objects.create(
            title='Test Item',
            primary_identifier='TEST123',
            status='checked_in',
            library=self.library
        )
        # Create a dummy image file
        self.image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'',
            content_type='image/jpeg'
        )
        self.item_image = ItemImage.objects.create(
            item=self.item,
            image=self.image
        )

    def test_item_image_creation(self):
        self.assertEqual(self.item_image.item, self.item)
        self.assertTrue(self.item_image.time)

    def test_item_image_str(self):
        self.assertEqual(str(self.item_image), f"Image for {self.item.title}")

