from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import UserProfile, Library, Item, Collection, ItemImage, ItemReview

class ItemModelTest(TestCase):
    def setUp(self):
        self.library = Library.objects.create(name="Test Library", description="A library for testing")
        self.item = Item.objects.create(
            title="Test Book",
            primary_identifier="12345",
            status="checked_in",
            library=self.library,
            description="A test book description"
        )
    
    def test_item_str(self):
        self.assertEqual(str(self.item), "Test Book")

    def test_add_image(self):
        dummy_image = SimpleUploadedFile(
            "test_image.jpg", b"dummy image content", content_type="image/jpeg"
        )
        image = ItemImage.objects.create(item=self.item, image=dummy_image)
        self.assertEqual(self.item.images.count(), 1)

    
    def test_add_review(self):
        user = User.objects.create(username="testuser", email="test@example.com")
        review = ItemReview.objects.create(item=self.item, user=user, rating=5, comment="Great!")
        self.assertEqual(self.item.reviews.count(), 1)

class CollectionModelTest(TestCase):
    def setUp(self):
        self.library = Library.objects.create(name="Test Library", description="A library for testing")
        self.user = User.objects.create(username="patron", email="patron@example.com")
        self.collection = Collection.objects.create(
            title="New Arrivals", 
            description="Latest books",
            is_public=False,
            library=self.library
        )
        self.collection.allowed_users.add(self.user)
    
    def test_collection_allowed_users(self):
        self.assertEqual(self.collection.allowed_users.count(), 1)
    
    def test_collection_library_relationship(self):
        self.assertEqual(self.collection.library, self.library)

