from django.contrib import admin

from .models import PushSubscription


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("medecin", "user_agent", "date_creation")
    list_filter = ("medecin",)
