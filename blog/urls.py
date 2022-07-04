from django.urls import path
from django.views.generic import RedirectView

from .post_view import PostCreateView, PostEditView, PostListView, PostDeleteView, GetCommentView, PostLikeView, \
    PostReportView, PostHideView, AddCommentView
from .profile_view import ProfileView, ProfileEditView, ProfileDeleteView, ProfilSearchView
from .views import ModerationView

app_name = 'blog'

urlpatterns = [
    path('', PostListView.as_view(), name='index'),
    path('post/latest', RedirectView.as_view(url='https://youtu.be/dQw4w9WgXcQ')),

    path('post/new', PostCreateView.as_view(), name='new-post'),
    path('post/<int:pk>/edit', PostEditView.as_view(), name='edit-post'),
    path('post/<int:pk>/delete', PostDeleteView.as_view(), name='delete-post'),
    path('post/<int:pk>/like', PostLikeView.as_view(), name='like-post'),
    path('post/<int:pk>/report', PostReportView.as_view(), name='report-post'),
    path('post/<int:pk>/hide', PostHideView.as_view(), name='hide-post'),
    path('post/<int:pk>/comments', GetCommentView.as_view(), name='get-comments'),
    path('post/<int:pk>/add-comment', AddCommentView.as_view(), name='add-comment'),

    path('user/<str:username>', ProfileView.as_view(), name='profile'),
    path('user/<str:username>/edit', ProfileEditView.as_view(), name='edit-profile'),
    path('user/<str:username>/delete', ProfileDeleteView.as_view(), name='delete-profile'),
    # path('user/<str:username>/star', ProfileStarView.as_view(), name='star-profile'),
    path("search", ProfilSearchView.as_view(), name="search"),

    # path('comment/<int:pk>/delete', GetCommentView.as_view(), name='delete-comment'),
    # path('comment/<int:pk>/like', PostLikeView.as_view(), name='like-comment'),
    # path('comment/<int:pk>/report', PostReportView.as_view(), name='report-comment'),
    # path('comment/<int:pk>/hide', PostHideView.as_view(), name='hide-comment'),

    path('moderation', ModerationView.as_view(), name='moderation'),
]
