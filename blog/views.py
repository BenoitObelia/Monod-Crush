from datetime import date, datetime
from typing import Any, Dict, Union

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View

from auth.models import CustomUser
from blog.models import Post, Comment, PostReport, Like


class ModerationView(LoginRequiredMixin, View):
    """ moderation panel with statistics """

    def get(self, request: Any) -> HttpResponse:
        if not request.user.is_superuser:
            raise PermissionDenied

        def cumulate_by_creation_date(data: QuerySet) -> Dict[Union[date, datetime], int]:
            """ cumulate objects by creation date """
            sorted(data, key=lambda x: x.created_at)
            result = {}
            c = 0
            for d in data:
                c += 1
                result[d.created_at] = c
            return result

        nb_posts = Post.objects.all().count()
        nb_users = CustomUser.objects.all().count()
        nb_comments = Comment.objects.all().count()
        nb_reports = PostReport.objects.all().count()
        nb_likes = Like.objects.all().count()

        cpost = cumulate_by_creation_date(Post.objects.all())

        context = {
            'nb_posts': nb_posts,
            'nb_users': nb_users,
            'nb_comments': nb_comments,
            'nb_reports': nb_reports,
            'nb_likes': nb_likes,
            'cpost': cpost,
        }

        return render(request, 'blog/pages/moderation.html', context)
