from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Setup groups (default_user, moderator, etc.)'

    def handle(self, *args, **options):
        user: Group = Group.objects.get_or_create(name="utilisateur")[0]
        moderator: Group = Group.objects.get_or_create(name="utilisateur")[0]

        user_permissions = ("create_posts",
                            "edit_own_posts",
                            "delete_own_posts",

                            "add_comments",
                            "delete_own_comments",

                            "report_posts",

                            "like_posts")

        for p in user_permissions:
            user.permissions.add(Permission.objects.get(codename=p))

        moderator_permissions = user_permissions + ()

        for p in moderator_permissions:
            moderator.permissions.add(Permission.objects.get(codename=p))

        self.stdout.write(self.style.SUCCESS('Successfully setup roles.'))
