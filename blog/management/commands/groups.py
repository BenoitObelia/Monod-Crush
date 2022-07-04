from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import models

from auth.models import CustomUser


class Command(BaseCommand):
    help = "set "

    def add_arguments(self, parser):
        parser.add_argument("action", type=str, help="action to perform", choices=["add", "remove", "set"])
        parser.add_argument("username",nargs=1, type=str, help="username")
        parser.add_argument("group", nargs="+", type=str, help="group name",
                            choices=list(Group.objects.all().values_list('name', flat=True)) + ['admin'])

    def handle(self, *args, **options):
        users = []
        for username in options['username']:
            try:
                user: CustomUser = CustomUser.objects.get(username=username)
                users.append(user)
            except models.ObjectDoesNotExist:
                self.stdout.write(self.style.ERROR(f"User with username '{username}' does not exist."))

        groups = []
        admin = False
        for group_name in options['group']:
            if group_name != 'admin':
                group: Group = Group.objects.get(name=group_name)
                groups.append(group)
            else:
                admin = True

        if options['action'] == 'add':
            for user in users:
                user.groups.add(*groups)
                if admin:
                    user.is_staff = True
                    user.is_superuser = True
                    user.save()
        elif options['action'] == 'remove':
            for user in users:
                user.groups.remove(*groups)
                if admin:
                    user.is_staff = False
                    user.is_superuser = False
                    user.save()
        elif options['action'] == 'set':
            for user in users:
                user.groups.set(groups)
                user.is_staff = False
                user.is_superuser = False
                user.save()
                if admin:
                    user.is_staff = True
                    user.is_superuser = True
                    user.save()

        self.stdout.write(self.style.SUCCESS('Successfully setup roles.'))
