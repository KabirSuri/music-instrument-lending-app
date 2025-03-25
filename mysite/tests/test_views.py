from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Library, Item, BorrowRequest, ItemImage, Collection
from ..forms import ItemForm

class ViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')
        self.librarian = User.objects.create_user(username='librarian', email='librarian@example.com', password='testpass123')
        self.librarian.profile.is_librarian = True
        self.librarian.profile.save()
        
        self.library = Library.objects.create(name='Test Library')
        self.item = Item.objects.create(
            title='Test Item',
            primary_identifier='TEST123',
            status='checked_in',
            library=self.library
        )

    def test_login_view(self):
        # Test unauthenticated access
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        
        # Test authenticated user access
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('login'))
        self.assertRedirects(response, reverse('patron-landing'))

    def test_logout_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))

    def test_patron_login(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('patron-landing'))
        self.assertEqual(response.status_code, 200)

    def test_librarian_login(self):
        self.client.login(username='librarian', password='testpass123')
        response = self.client.get(reverse('librarian-landing'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('items', response.context)
        self.assertIn('requests', response.context)

    def test_profile_view(self):
        # Test unauthenticated access
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")

        # Test patron profile
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['profile'], self.user.profile)

        # Test librarian profile
        self.client.login(username='librarian', password='testpass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['profile'], self.librarian.profile)

    def test_image_upload_view(self):
        self.client.login(username='testuser', password='testpass123')
        
        # Test GET request
        response = self.client.get(reverse('image_upload'))
        self.assertEqual(response.status_code, 200)

        # Test POST request with profile image
        image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'',
            content_type='image/jpeg'
        )
        response = self.client.post(reverse('image_upload'), {
            'profile_image_file': image
        })
        self.assertRedirects(response, reverse('profile'))

        # Test librarian item image upload
        self.client.login(username='librarian', password='testpass123')
        response = self.client.post(reverse('image_upload'), {
            'item_id': self.item.id,
            'item_image_file': image
        })
        self.assertRedirects(response, reverse('profile'))

    def test_borrow_item(self):
        self.client.login(username='testuser', password='testpass123')
        
        # Test successful borrow request
        response = self.client.post(reverse('borrow_item', args=[self.item.id]))
        self.assertRedirects(response, reverse('item_detail', args=[self.item.id]))
        
        # Test duplicate request prevention
        response = self.client.post(reverse('borrow_item', args=[self.item.id]))
        self.assertRedirects(response, reverse('item_detail', args=[self.item.id]))

    def test_search_items(self):
        response = self.client.get(reverse('search_items'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('items', response.context)
        
        # Test search with query
        response = self.client.get(f"{reverse('search_items')}?q=Test")
        self.assertEqual(response.status_code, 200)
        self.assertIn('items', response.context)
        self.assertEqual(response.context['query'], 'Test')

    def test_item_detail(self):
        response = self.client.get(reverse('item_detail', args=[self.item.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['item'], self.item)

    def test_create_item(self):
        # Test unauthenticated access
        response = self.client.get(reverse('create_item'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('create_item')}")

        # Test non-librarian access
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('create_item'))
        self.assertRedirects(response, reverse('librarian-landing'))

        # Test librarian access
        self.client.login(username='librarian', password='testpass123')
        response = self.client.get(reverse('create_item'))
        self.assertEqual(response.status_code, 200)

        # Test item creation
        form_data = {
            'title': 'New Item',
            'primary_identifier': 'NEW123',
            'status': 'checked_in',
            'library': self.library.id
        }
        response = self.client.post(reverse('create_item'), form_data)
        self.assertRedirects(response, reverse('item_detail', args=[Item.objects.latest('id').id]))

    def test_edit_item(self):
        # Test unauthenticated access
        response = self.client.get(reverse('edit_item', args=[self.item.id]))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('edit_item', args=[self.item.id])}")

        # Test non-librarian access
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('edit_item', args=[self.item.id]))
        self.assertRedirects(response, reverse('librarian-landing'))

        # Test librarian access
        self.client.login(username='librarian', password='testpass123')
        response = self.client.get(reverse('edit_item', args=[self.item.id]))
        self.assertEqual(response.status_code, 200)

        # Test item update
        form_data = {
            'title': 'Updated Item',
            'primary_identifier': self.item.primary_identifier,
            'status': self.item.status,
            'library': self.library.id
        }
        response = self.client.post(reverse('edit_item', args=[self.item.id]), form_data)
        self.assertRedirects(response, reverse('item_detail', args=[self.item.id])) 