from __future__ import annotations

import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet, Manager

from auth.models import CustomUser

log = logging.getLogger(__name__)


class Post(models.Model):
    NORMAl = 'N'
    AWAITING_VERIFICATION = 'A'
    HIDDEN = 'H'

    STATUS_CHOICES = (
        (NORMAl, 'Normal'),
        (AWAITING_VERIFICATION, 'En attente de vérification'),
        (HIDDEN, 'Masqué'),
    )

    VISIBLE_STATUSES = (NORMAl,)

    text = models.TextField("contenu du post", max_length=500)
    author: CustomUser = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                           related_name='posts', verbose_name='Auteur')
    status = models.CharField("état", max_length=1, choices=STATUS_CHOICES, default=NORMAl)
    is_anonymous = models.BooleanField("post anonyme", default=True)
    updated_at = models.DateTimeField("dernière modification", auto_now=True)
    created_at = models.DateTimeField("date de création", auto_now_add=True)

    likes: QuerySet[Like]
    reports: QuerySet[PostReport]
    comments: QuerySet[Comment]
    objects: Manager

    class Meta:
        verbose_name = "post"
        verbose_name_plural = "posts"

        permissions = (
            # user permission
            ("create_posts", "Peut créer des posts"),
            ('edit_own_posts', 'Peut modifier ses propres posts'),
            ('delete_own_posts', 'Peut supprimer ses propres posts'),

            # moderator permission
            ('hide_posts_from_other_users', "Peut masquer des posts (sans voir l'auteur)"),
            ('delete_posts_from_other_users', "Peut supprimer les posts des autres (sans voir l'auteur)"),

            # admin permission
            ("view_posts_details", "Peut voir les détails des posts (dont l'auteur)"),
        )

        default_permissions = ()

    def reset_report(self) -> None:
        """ Reset all reports for this post. """
        self.reports.all().delete()

    @property
    def nb_of_likes(self) -> int:
        """ Return the number of likes for this post. """
        return self.likes.count()

    @property
    def nb_of_comments(self) -> int:
        """ Return the number of comments for this post. """
        return self.comments.count()

    @property
    def nb_of_reports(self) -> int:
        """ Return the number of reports for this post. """
        return self.reports.count()

    # noinspection PyTypeChecker
    @property
    def short_text(self) -> str:
        """ Returns the first 40 characters of the post's text. """
        MAX_LENGTH = 37  # 40 characters - 3 dots
        if len(self.text) > MAX_LENGTH:
            return self.text[:MAX_LENGTH] + '...'
        else:
            return self.text

    def __str__(self) -> str:
        return f"{self.author.username} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"


class Comment(models.Model):
    post: Post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments", verbose_name="post")
    author: CustomUser = models.ForeignKey(CustomUser, on_delete=models.CASCADE,
                                           related_name="comments", verbose_name='auteur')
    text = models.TextField(max_length=300)
    is_anonymous = models.BooleanField("commentaire anonyme", default=True)
    created_at = models.DateTimeField("date de creation", auto_now_add=True)

    objects: Manager

    class Meta:
        verbose_name = "commentaire"
        verbose_name_plural = "commentaires"

        permissions = (
            # user permission
            ("add_comments", "Peut ajouter des commentaires"),
            ("delete_own_comments", "Peut supprimer ses commentaires"),

            # moderator permission
            ("delete_comments_from_other_users", "Peut supprimer les commentaires des autres (sans voir l'auteur)"),

            # admin permission
            ("view_comments_details", "Peut voir les détails des commentaires (dont l'auteur)"),
        )

        default_permissions = ()

    # noinspection PyTypeChecker
    @property
    def short_text(self) -> str:
        """ Returns the first 40 characters of the post's text. """
        MAX_LENGTH = 37  # 40 characters - 3 dots
        if len(self.text) > MAX_LENGTH:
            return self.text[:MAX_LENGTH] + '...'
        else:
            return self.text

    def __str__(self) -> str:
        return f"{self.author.username} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"


class PostReport(models.Model):
    # threshold beyond which the publication is hidden
    REPORTS_CRITICAL_THRESHOLD = 3

    post: Post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reports", verbose_name="post signalé")
    user: CustomUser = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                         related_name="reports", verbose_name="auteur du signalement")
    created_at = models.DateTimeField("date du signalement", auto_now_add=True)

    objects: Manager

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['post', 'user'], name='unique_report_post_user'),
        ]

        verbose_name = "signalement"
        verbose_name_plural = "signalements"

        permissions = (
            # user permission
            ("report_posts", "Peut signaler des posts"),
        )

        default_permissions = ()

    def validate_unique(self, exclude: iter = None) -> None:
        """ Check you can't report the same post twice """
        if PostReport.objects.filter(post=self.post, user=self.user).exists():
            raise ValidationError("The post has already been reported by this user.", code='unique_report_post_user')
        super().validate_unique(exclude)

    def clean(self) -> None:
        """ Check you can't report your own post """
        if self.post.author == self.user:
            raise ValidationError("The post author can't report his own post.", code='author_post')

    def save(self, **kwargs) -> None:
        """ Override save method to prevent more than 3 reports per post """
        super().save(**kwargs)

        self.post.status = Post.AWAITING_VERIFICATION

        if self.post.nb_of_reports >= self.REPORTS_CRITICAL_THRESHOLD:
            self.post.status = Post.HIDDEN
            log.info(
                    f"Post {self.post.id} has been hidden because it has been reported {self.post.nb_of_reports} times.")

        self.post.save()

    def __repr__(self) -> str:
        return f'{self.post} - {self.user.username}'


class Like(models.Model):
    post: Post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes", verbose_name="post aimé")
    user: CustomUser = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                         related_name="likes", verbose_name="utilisateur aimant")
    created_at = models.DateTimeField("date", auto_now_add=True)

    objects: Manager

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['post', 'user'], name='unique_like_post_user')
        ]

        verbose_name = "like"
        verbose_name_plural = "likes"

        permissions = (
            # user permission
            ("like_posts", "Peut aimer des posts"),
        )

        default_permissions = ()

    def validate_unique(self, exclude: iter = None) -> None:
        """ Check you can't like the same post twice """
        if Like.objects.filter(post=self.post, user=self.user).exists():
            raise ValidationError("Vous avez déjà liké ce post")
        super().validate_unique(exclude)

    def __str__(self) -> str:
        return f'{self.post} - {self.user.username}'
