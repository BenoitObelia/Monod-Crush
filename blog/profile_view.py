import logging
from typing import Any

from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet, Q
from django.forms import Form
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy as reverse
from django.views import View
from django.views.generic import UpdateView, ListView, DetailView

from auth.models import CustomUser

log = logging.getLogger(__name__)


class CustomUserMixin:
    model = CustomUser
    slug_url_kwarg = 'username'
    slug_field = 'username'


class ProfileView(CustomUserMixin, DetailView):
    template_name = 'blog/pages/profile.html'
    context_object_name = 'profile'


class ProfileEditView(CustomUserMixin, UserPassesTestMixin, UpdateView):
    fields = ['username', 'first_name', 'bio', "study", 'email', 'instagram', 'twitter', 'github', 'website']
    template_name = 'blog/pages/edit_profile.html'

    def test_func(self) -> bool:
        return self.get_object() == self.request.user and self.request.user.has_perm('blog.edit_own_profile') \
               or self.request.user.has_perm('blog.edit_other_users_profile')

    def form_valid(self, form: Form) -> HttpResponseRedirect:
        log.info(f"{self.request.user} - edited profile")
        return super().form_valid(form)

    def get_success_url(self) -> str:
        # redirect with new username
        return reverse('blog:profile', kwargs={'username': self.object.username})


class ProfileDeleteView(View):
    """" Delete user profile check if user is deleting his own profile """
    success_url = reverse('blog:index')
    staff_permission_required = 'blog.delete_other_profile'
    permission_denied_message = "Vous n'avez pas le droit d'effectuer cette action."

    def check_permission(self, account: CustomUser) -> None:
        if not (account == self.request.user or self.request.user.has_perm(self.staff_permission_required)):
            raise PermissionDenied(self.permission_denied_message)

    def post(self, request: Any, username: str) -> HttpResponseRedirect:
        account = get_object_or_404(CustomUser, username=username)
        self.check_permission(account)
        account.delete()
        log.info(f"{request.user} - deleted profile {account}")
        return HttpResponseRedirect(self.success_url)


class ProfileStarView(PermissionRequiredMixin, View):
    """ handle POST request to star a profile """

    permission_required = "blog.star_profiles"
    permission_denied_message = "Vous n'avez pas les droits pour marquer un profil."

    def post(self, request: Any, username: str) -> HttpResponse:
        profile = get_object_or_404(CustomUser, username=username)
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
    template_name = "blog/pages/search_results.html"
    context_object_name = "users"

    def get_queryset(self) -> QuerySet[CustomUser]:
        query = self.request.GET.get("q", "")
        users = CustomUser.objects.filter(Q(username__icontains=query) | Q(first_name__icontains=query))
        return users
