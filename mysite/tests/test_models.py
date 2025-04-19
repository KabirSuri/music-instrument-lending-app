from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import UserProfile, Library, Item, Collection, ItemImage, ItemReview, LikeDislike
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

class ProfileLikesTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.library = Library.objects.create(name="Main Library")
        self.item1 = Item.objects.create(title='Item 1', primary_identifier='I1', status='available', library_id=1)
        self.item2 = Item.objects.create(title='Item 2', primary_identifier='I2', status='available', library_id=1)
        LikeDislike.objects.create(user=self.user, item=self.item1, vote=1)
        LikeDislike.objects.create(user=self.user, item=self.item2, vote=-1)

    def test_liked_and_disliked_items_in_profile_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/profile/')
        self.assertContains(response, 'Item 1')
        self.assertContains(response, 'Item 2')

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

class ItemReviewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.library = Library.objects.create(name='Test Library')
        self.item = Item.objects.create(
            title='Test Item',
            primary_identifier='TEST123',
            status='checked_in',
            library=self.library
        )
        self.review = ItemReview.objects.create(
            item=self.item,
            user=self.user,
            rating=5,
            comment='Great item!'
        )

    def test_review_creation(self):
        self.assertEqual(self.review.item, self.item)
        self.assertEqual(self.review.user, self.user)
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.comment, 'Great item!')
        self.assertTrue(self.review.time)

    def test_review_str(self):
        self.assertEqual(str(self.review), f"Review for {self.item.title} by {self.user.email}")

class BorrowRequestTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.library = Library.objects.create(name='Test Library')
        self.item = Item.objects.create(
            title='Test Item',
            primary_identifier='TEST123',
            status='checked_in',
            library=self.library
        )
        self.borrow_request = BorrowRequest.objects.create(
            item=self.item,
            user=self.user
        )

    def test_borrow_request_creation(self):
        self.assertEqual(self.borrow_request.item, self.item)
        self.assertEqual(self.borrow_request.user, self.user)
        self.assertFalse(self.borrow_request.approved)
        self.assertIsNone(self.borrow_request.due_date)
        self.assertTrue(self.borrow_request.requested_at)

    def test_borrow_request_approve(self):
        self.borrow_request.approve()
        self.assertTrue(self.borrow_request.approved)
        self.assertTrue(self.borrow_request.due_date)
        self.assertEqual(self.item.status, 'in_circulation')

    def test_borrow_request_str(self):
        self.assertEqual(str(self.borrow_request), f"{self.user.username} requested {self.item.title}")

class CollectionTest(TestCase):
    def setUp(self):
        self.library = Library.objects.create(name='Test Library')
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.collection = Collection.objects.create(
            title='Test Collection',
            description='Test Description',
            is_public=True,
            library=self.library
        )
        self.collection.allowed_users.add(self.user)

    def test_collection_creation(self):
        self.assertEqual(self.collection.title, 'Test Collection')
        self.assertEqual(self.collection.description, 'Test Description')
        self.assertTrue(self.collection.is_public)
        self.assertEqual(self.collection.library, self.library)

    def test_collection_allowed_users(self):
        self.assertIn(self.user, self.collection.allowed_users.all())

    def test_collection_str(self):
        self.assertEqual(str(self.collection), 'Test Collection')

