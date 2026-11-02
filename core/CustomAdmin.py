"""Backwards-compatible admin base; the field now owns its editor."""
from django.contrib import admin


class CustomModelAdmin(admin.ModelAdmin):
    """Optional compatibility class. Plain ModelAdmin works as well."""
