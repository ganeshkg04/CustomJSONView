"""The original module path is retained for existing database migrations."""
from django.db import models
from .translation_forms import TranslationFormField


class JsonFieldWithTranslation(models.JSONField):
    """Store language-code/text pairs, with a labelled input per language."""

    def formfield(self, **kwargs):
        return super().formfield(**{'form_class': TranslationFormField, **kwargs})

    def save_form_data(self, instance, data):
        # Changing the configured languages must not silently erase old translations.
        existing = getattr(instance, self.name, None)
        merged = dict(existing) if isinstance(existing, dict) else {}
        merged.update(data or {})
        super().save_form_data(instance, merged)
