import logging
from datetime import date, datetime
from typing import Any, Dict, Union

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet, Exists, OuterRef
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy as reverse
from django.views import View
from django.views.generic import CreateView, UpdateView, ListView
from django.views.generic.edit import ModelFormMixin

from auth.models import CustomUser
from .models import Comment, Post, PostReport, Like

log = logging.getLogger(__name__)


class PostListView(ListView):
    """ Home page view """

    template_name = 'blog/pages/index.html'
    queryset = Post.objects.filter(status__in=Post.VISIBLE_STATUSES)
    ordering = ['-created_at']

    paginate_by = 15

    def get_queryset(self) -> QuerySet[Post]:
        queryset = super().get_queryset()
        if self.request.user.is_authenticated:
            # add to each post if it is liked by the user **{slug_field: slug}
            queryset = queryset.annotate(liked=Exists(Like.objects.filter(post=OuterRef('id'), user=self.request.user)))
        return queryset


class PostCreateView(PermissionRequiredMixin, CreateView):
    """ View for creating a new post """

    model = Post
    fields = ['text', "is_anonymous"]
    template_name = 'blog/pages/create_post.html'
    success_url = reverse('blog:index')

    permission_required = 'blog.create_posts'
    permission_denied_message = "Vous n'avez pas les droits pour créer un post."

    def form_valid(self, form) -> HttpResponseRedirect:
        form.instance.author = self.request.user
        log.info(f"created new post", extra={'user': self.request.user})
        return super().form_valid(form)


class PostEditView(PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['text']
    template_name = 'blog/pages/edit_post.html'
    success_url = reverse('blog:index')

    permission_required = 'blog.edit_own_posts'
    permission_denied_message = "Vous n'avez pas les droits pour modifier ce post."

    def test_func(self) -> bool:
        return self.get_object().author == self.request.user

    def form_valid(self, form) -> HttpResponseRedirect:
        log.info(f"{self.request.user} - edited post {self.object}")
        return super().form_valid(form)


class PostDeleteView(LoginRequiredMixin, View):
    success_url = reverse('blog:index')

    permission_required = 'blog.delete_own_posts'
    staff_permission_required = 'blog.delete_posts_from_other_users'
    permission_denied_message = "Vous n'avez pas les droits pour supprimer ce post."

    def check_permission(self, post: Post) -> None:
        if not ((post.author == self.request.user and self.request.user.has_perm(self.permission_required)) \
                or self.request.user.has_perm(self.staff_permission_required)):
            raise PermissionDenied(self.permission_denied_message)

    def post(self, request: Any, pk: int) -> HttpResponseRedirect:
        post = get_object_or_404(Post, pk=pk)
        self.check_permission(post)
        log.info(f"{request.user} - deleted post {post}")
        post.delete()
        return HttpResponseRedirect(self.success_url)


class GetCommentView(View):
    """ retrieves all comments related to a post """
    template_name = 'blog/components/list-of-comments.html'

    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        post = get_object_or_404(Post, pk=pk)
        comments = post.comments.order_by('-created_at').all()
        return render(request, self.template_name, {'comments': comments})


class AddCommentView(PermissionRequiredMixin, ModelFormMixin, View):
    """ handle POST request to add a comment to a post without template """
    model = Comment
    fields = ['text']

    permission_required = "blog.add_comments"
    permission_denied_message = "Vous n'avez pas les droits pour ajouter un commentaire."

    def post(self, request: Any, pk: int) -> HttpResponse:
        form = self.get_form()

        if form.is_valid():
            log.critical(f"{request.user} - added comment to post {pk}")
            form.instance.author = request.user
            form.instance.post = get_object_or_404(Post, pk=pk)
            form.save()
            return render(request, 'blog/pages/response.html', {'comment': form.instance, "post": form.instance.post})
        else:
            messages.error(request, f"Erreur lors de l'ajout du commentaire : {form.errors}")
            return HttpResponse(status=400)


class PostLikeView(PermissionRequiredMixin, View):
    """ handle POST request to like a post """

    permission_required = "blog.like_posts"
    permission_denied_message = "Vous n'avez pas les droits pour aimer un post."

    def post(self, request: Any, pk: int) -> HttpResponse:
        post = get_object_or_404(Post, pk=pk)

        if post.likes.filter(user=request.user).exists():
            post.likes.filter(user=request.user).delete()
            log.info(f"User {request.user} unliked post {post}")
            post.liked = False
            return render(request, 'blog/elements/post-like-button.html', {'post': post})
        else:
            post.likes.create(user=request.user)
            log.info(f"User {request.user} liked post {post}")
            post.liked = True
            return render(request, 'blog/elements/post-like-button.html', {'post': post})


class PostReportView(PermissionRequiredMixin, View):
    """ handle POST request to report a post """

    permission_required = 'blog.report_posts'
    permission_denied_message = "Vous n'avez pas les droits pour signaler un post."

    def post(self, request: Any, pk: int) -> HttpResponse:
        post = get_object_or_404(Post, pk=pk)
        post.reports.create(user=request.user)
        messages.success(request, "Votre signalement a bien été pris en compte.")
        log.info(f"User {request.user} reported post {post}")
        return HttpResponse(status=201)


class PostHideView(PermissionRequiredMixin, View):
    """ handle POST request to hide a post """

    permission_required = 'blog.hide_posts_from_other_users'
    permission_denied_message = "Vous n'avez pas les droits pour masquer ce post."

    def post(self, request: Any, pk: int) -> HttpResponse:
        post = get_object_or_404(Post, pk=pk)
        post.status = Post.HIDDEN
        post.save()
        log.info(f"User {request.user} hid post {post}")
        return HttpResponse(status=201)


