from django.urls import path

from about.views import ContactView, WhoAreWeView

app_name = 'about'

urlpatterns = [
    path("contact", ContactView.as_view(), name="contact"),
    path("who-are-we", WhoAreWeView.as_view(), name="who-are-we"),
]
