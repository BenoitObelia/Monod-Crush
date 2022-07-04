from django.template.response import TemplateResponse
from django.test import TestCase
from django.urls import reverse

from auth.models import CustomUser
from .models import Post


def create_user(username: str = "test") -> CustomUser:
    return CustomUser.objects.create_user(username=username, password="test", date_of_birth="2000-01-01")


class PostModelTests(TestCase):

    def test_create_post(self) -> None:
        """
        Test that a post can be created.
        """
        user = create_user()
        post = Post.objects.create(author=user, text='test', is_anonymous=False)
        self.assertEqual(post.text, 'test')
        self.assertEqual(post.author, user)
        self.assertFalse(post.is_anonymous)
        self.assertEqual(post.status, Post.NORMAl)

    def test_create_anonymous_post(self) -> None:
        """
        Test that a post can be created with anonymous.
        """
        user = create_user()
        post = Post.objects.create(author=user, text='test')
        self.assertEqual(post.text, 'test')
        self.assertEqual(post.author, user)
        self.assertTrue(post.is_anonymous)
        self.assertEqual(post.status, Post.NORMAl)

        post = Post.objects.create(author=user, text='test', is_anonymous=True)
        self.assertEqual(post.text, 'test')
        self.assertEqual(post.author, user)
        self.assertTrue(post.is_anonymous)
        self.assertEqual(post.status, Post.NORMAl)

    def test_bad_post_creation(self) -> None:
        """
        Test that a post can't be created with bad data.
        """
        user = create_user()
        self.assertRaises(ValueError, Post.objects.create, author=user, text='a' * 501)
        self.assertRaises(ValueError, Post.objects.create, author=user, text='')

    def test_post_status(self) -> None:
        """
        Test that a post can be created with different statuses.
        """
        user = create_user()
        post = Post.objects.create(author=user, text='test')
        self.assertEqual(post.status, Post.NORMAl)
        self.assertIn(post.status, Post.VISIBLE_STATUSES)

        post.status = Post.AWAITING_VERIFICATION
        self.assertEqual(post.status, Post.AWAITING_VERIFICATION)
        self.assertNotIn(post.status, Post.VISIBLE_STATUSES)

        post.status = Post.HIDDEN
        self.assertEqual(post.status, Post.HIDDEN)
        self.assertNotIn(post.status, Post.VISIBLE_STATUSES)


class PostIndexViewTests(TestCase):
    def test_no_post(self):
        """
        If no post exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('blog:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Il n'y pas encore de post soyez le premier à en poster un")
        self.assertQuerysetEqual(response.context['posts'], [])

    def test_post_list(self):
        """
        If posts exist, they are displayed.
        """
        user = create_user()
        p1 = Post.objects.create(author=user, text='test')
        p2 = Post.objects.create(author=user, text='test')
        response = self.client.get(reverse('blog:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, p1.text)
        self.assertContains(response, p2.text)
        self.assertNotContains(response, "Il n'y pas encore de post soyez le premier à en poster un")
        self.assertQuerysetEqual(response.context['posts'], [p1, p2])

    def test_post_list_anonymous(self) -> None:
        """
        If posts exist, they are displayed.
        """

        user = create_user("usertest3")
        p2 = Post.objects.create(author=user, text='test', is_anonymous=False)
        response = self.client.get(reverse('blog:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, p2.text)
        self.assertContains(response, p2.author.username)
