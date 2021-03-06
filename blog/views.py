import logging

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet, Q
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, UpdateView, ListView, DetailView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import DeletionMixin

from auth.models import CustomUser
from .models import Comment, Post, PostReport, Like

log = logging.getLogger(__name__)


def test(request: HttpRequest) -> HttpResponse:
    return render(request, 'blog/test.html')


class PostMixin:
    model = Post
    slug_url_kwarg = 'post_id'
    slug_field = 'id'


class PostListView(ListView):
    model = Post
    template_name = 'blog/index.html'
    context_object_name = 'posts'

    paginate_by = 30

    def get_queryset(self) -> QuerySet[Post]:
        posts = Post.objects.filter(status__in=Post.PUBLIC).order_by('-created_at')
        if self.request.user.is_authenticated:
            for post in posts:
                post.liked = post.likes.filter(user=self.request.user).exists()
        return posts


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['text', "is_anonymous"]
    template_name = 'blog/create_post.html'
    success_url = '/'

    def form_valid(self, form) -> HttpResponseRedirect:
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostEditView(PostMixin, LoginRequiredMixin, UpdateView):
    fields = ['text']
    template_name = 'blog/edit_post.html'
    success_url = '/'

    def get_object(self, queryset=None) -> Post:
        post = super().get_object()
        if post.author == self.request.user or self.request.user.has_perm('blog.edit_post'):
            return post
        raise PermissionDenied


class PostDeleteView(PostMixin, LoginRequiredMixin, SingleObjectMixin, DeletionMixin, View):
    success_url = reverse_lazy('blog:index')

    def get_object(self, queryset=None) -> Post:
        post = super().get_object()
        if post.author == self.request.user or self.request.user.has_perm('blog.edit_post'):
            return post
        raise PermissionDenied


# TODO maybe use SingleObjectTemplateResponseMixin
class PostCommentView(PostMixin, SingleObjectMixin, View):
    """ login required for post """

    def post(self, request: HttpRequest, post_id) -> HttpResponse:
        if not request.user.is_authenticated:
            return HttpResponse(status=401)

        post = super().get_object()
        comment = request.POST['comment']

        Comment.objects.create(post=post, author=request.user, text=comment, is_anonymous=True)

        comments = post.comments.order_by('-created_at')
        return render(request, 'blog/partials/rep.html', {'comments': comments, 'post': post})

    def get(self, request: HttpRequest, post_id) -> HttpResponse:
        post = super().get_object()
        comments = post.comments.order_by('-created_at')
        return render(request, 'blog/partials/rep.html', {'comments': comments, 'post': post})


# TODO Delete comment
# TODO remove post_id
class PostLikeView(PostMixin, LoginRequiredMixin, SingleObjectMixin, View):
    def post(self, request: HttpRequest, post_id) -> HttpResponse:
        post = super().get_object()

        if post.likes.filter(user=request.user).exists():
            post.likes.filter(user=request.user).delete()
            log.info(f"User {request.user} unliked post {post}")
            post.liked = False
            return render(request, 'blog/components/post-like-button.html', {'post': post})

        else:
            post.likes.create(user=request.user)
            log.info(f"User {request.user} liked post {post}")
            post.liked = True
            return render(request, 'blog/components/post-like-button.html', {'post': post})


class PostReportView(PostMixin, LoginRequiredMixin, SingleObjectMixin, View):
    def post(self, request: HttpRequest, post_id) -> HttpResponse:
        post = super().get_object()

        if not post.reports.filter(user=request.user).exists():
            post.reports.create(user=request.user)
            log.info(f"User {request.user} reported post {post}")
            return HttpResponse(status=201)

        # TODO notify user
        log.info(f"User {request.user} already reported post {post}")
        return HttpResponse(status=400)


class PostHideView(PostMixin, LoginRequiredMixin, SingleObjectMixin, View):
    def post(self, request: HttpRequest, post_id) -> HttpResponse:
        post = super().get_object()

        if request.user.has_perm('blog.hide_post'):
            post.status = Post.HIDDEN
            post.save()
            log.info(f"User {request.user} hid post {post}")
            return HttpResponse(status=201)

        raise PermissionDenied


class CustomUserMixin:
    model = CustomUser
    slug_url_kwarg = 'username'
    slug_field = 'username'


class ProfileView(CustomUserMixin, DetailView):
    template_name = 'blog/profile.html'
    context_object_name = 'profile'


class ProfileEditView(CustomUserMixin, LoginRequiredMixin, UpdateView):
    fields = ['username', 'first_name', 'bio', "study", 'email', 'instagram', 'twitter', 'github', 'website']
    template_name = 'blog/edit_profile.html'

    def get_object(self, queryset=None) -> CustomUser:
        user = super().get_object()
        if user == self.request.user or self.request.user.has_perm('blog.edit_other_profile'):
            return user
        raise PermissionDenied

    def get_success_url(self) -> str:
        # redirect with new username
        return reverse_lazy('blog:profile', kwargs={'username': self.object.username})
    # TODO replace with reverse_lazy by reverse


class ProfileDeleteView(CustomUserMixin, LoginRequiredMixin, SingleObjectMixin, DeletionMixin, View):
    """" Delete user profile check if user is deleting his own profile """
    success_url = reverse_lazy('blog:index')

    def get_object(self, queryset=None) -> CustomUser:
        user = super().get_object()
        if user == self.request.user or self.request.user.has_perm('blog.delete_user'):
            return user
        raise PermissionDenied


class ProfileStarView(CustomUserMixin, LoginRequiredMixin, SingleObjectMixin, View):
    def post(self, request: HttpRequest) -> HttpResponse:
        user = super().get_object()
        return HttpResponse(status=200)
        # if user.stars.filter(user=request.user).exists():
        #     user.stars.filter(user=request.user).delete()
        #     log.info(f"User {request.user} unstarred user {user}")
        #     return HttpResponse(status=200)
        # else:
        #     user.stars.create(user=request.user)
        #     log.info(f"User {request.user} starred user {user}")
        #     return HttpResponse(status=200)


class ProfilSearchView(ListView):
    model = CustomUser
    template_name = "blog/search_results.html"
    context_object_name = "users"

    def get_queryset(self) -> QuerySet[CustomUser]:
        query = self.request.GET.get("q", "")
        users = CustomUser.objects.filter(Q(username__icontains=query) | Q(first_name__icontains=query))
        return users


class ModerationView(LoginRequiredMixin, View):
    """ moderation panel with statistics """

    def get(self, request: HttpRequest) -> HttpResponse:
        if not request.user.is_superuser:
            raise PermissionDenied

        nb_posts = Post.objects.all().count()
        nb_users = CustomUser.objects.all().count()
        nb_comments = Comment.objects.all().count()
        nb_reports = PostReport.objects.all().count()
        nb_likes = Like.objects.all().count()

        context = {
            'nb_posts': nb_posts,
            'nb_users': nb_users,
            'nb_comments': nb_comments,
            'nb_reports': nb_reports,
            'nb_likes': nb_likes,
        }

        return render(request, 'blog/moderation.html', context)
