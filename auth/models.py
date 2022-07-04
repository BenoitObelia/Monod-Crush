import logging
from datetime import date
from typing import Any

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager, Group, Permission
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models
from django.db.models.functions import Lower
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver

from .validators import username_validator, date_of_birth_validator, instagram_validator, twitter_validator


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """ Custom user model """

    username = models.CharField(
            "nom d'utilisateur",
            max_length=20,
            unique=True,
            help_text="Nom d'utilisateur composé de lettres, chiffres, -/_/. de 20 caractères maximum.",
            validators=[username_validator],
            error_messages={
                "unique": "Ce nom d'utilisateur est déjà utilisé.",
            },
    )

    date_of_birth = models.DateField("date de naissance", validators=[date_of_birth_validator])

    profile_pic = models.ImageField(
            "photo de profil",
            upload_to="profile_pics",
            blank=True,
            null=True,
    )

    first_name = models.CharField("prénom", max_length=150, blank=True)
    bio = models.TextField("biographie", max_length=500, blank=True)
    email = models.EmailField("adresse mail", blank=True,
                              help_text="L'adresse mail permet de récupérer son compte en cas de perte de mot de passe."
                                        " Elle n'est pas publiée sur votre profil.")

    study = models.CharField("études (classe)", max_length=100, blank=True)
    instagram = models.CharField("instagram", max_length=100, validators=[instagram_validator], blank=True)
    twitter = models.CharField("twitter", max_length=100, validators=[twitter_validator], blank=True)
    github = models.CharField("github", max_length=100, blank=True)
    website = models.URLField("site web", blank=True)

    is_staff = models.BooleanField(
            "membre du staff",
            default=False,
            help_text="Permet de définir si l'utilisateur peut se connecter à l'administration.",
    )

    is_active = models.BooleanField(
            "actif",
            default=True,
            help_text="Permet de définir si l'utilisateur peut se connecter."
                      " Désactivez-le pour pour bannir un utilisateur ou désactiver un compte sans le supprimer.",
    )
    date_joined = models.DateTimeField("date d'inscription", auto_now_add=True)

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["date_of_birth"]

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower("username"), name="unique_username"),
        ]

        verbose_name = "utilisateur"
        verbose_name_plural = "utilisateurs"

    def validate_unique(self, exclude: iter = None) -> None:
        """ Validate that the lower username is unique."""
        username_check = CustomUser.objects.filter(username__iexact=self.username)
        if username_check.exists() and username_check.first() != self:
            raise ValidationError("Ce nom d'utilisateur est déjà utilisé.", code="unique_username")
        super().validate_unique(exclude)

    def clean(self) -> None:
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def email_user(self, subject: Any, message: Any, from_email: Any = None, **kwargs: Any) -> int:
        """ Sends an email to this User."""
        return send_mail(subject, message, from_email, [self.email], **kwargs)

    @property
    def is_birthday(self) -> bool:
        """ Return True if the user is a birthday."""
        return self.date_of_birth.month == date.today().month and self.date_of_birth.day == date.today().day


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """ Add all new users to the "default_user" group """
    if created:
        default_user: Group = Group.objects.get_or_create(name='default_user')[0]

        instance.groups.add(default_user)

        # Create the default group once at the beginning of the project.

        permission = ("create_posts",
                      "edit_own_posts",
                      "delete_own_posts",

                      "add_comments",
                      "delete_own_comments",

                      "report_posts",

                      "like_posts")

        for p in permission:
            default_user.permissions.add(Permission.objects.get(codename=p))

        Group.objects.get_or_create(name='modérateur')
