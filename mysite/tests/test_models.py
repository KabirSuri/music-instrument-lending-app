from django.test import TestCase
from django.contrib.auth.models import User
from ..models import UserProfile, Library, Item, Collection, ItemImage, ItemReview

class ItemModelTest(TestCase):
    def setUp(self):
        # Create a Library to represent the full catalog.
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
        image = ItemImage.objects.create(item=self.item, image_url="http://s3.amazonaws.com/bucket/image.jpg")
        self.assertEqual(self.item.images.count(), 1)
    
    def test_add_review(self):
        user = User.objects.create(username="testuser", email="test@example.com")
        review = ItemReview.objects.create(item=self.item, user=user, rating=5, comment="Great!")
        self.assertEqual(self.item.reviews.count(), 1)

class CollectionModelTest(TestCase):
    def setUp(self):
        # Create a Library for collections.
        self.library = Library.objects.create(name="Test Library", description="A library for testing")
        self.user = User.objects.create(username="patron", email="patron@example.com")
        # Associate the collection with the library.
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
        # Ensure the collection is linked to the correct library.
        self.assertEqual(self.collection.library, self.library)

