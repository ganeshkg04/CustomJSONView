from django.contrib import admin
from core.CustomAdmin import CustomModelAdmin
from .models import SampleModel, MpttSampleModel
from mptt.admin import MPTTModelAdmin

admin.site.site_header = 'Lingua · Translation studio'
admin.site.site_title = 'Lingua'
admin.site.index_title = 'Your content workspace'


@admin.register(SampleModel)
class SampleModelAdmin(CustomModelAdmin):
    list_display = ('__str__', 'translation_codes')
    fieldsets = (
        ('Multilingual content', {
            'description': 'One record. Every language. The default language is required.',
            'fields': ('title', 'article'),
        }),
        ('Additional metadata', {'fields': ('author',), 'classes': ('collapse',)}),
    )

    @admin.display(description='Languages')
    def translation_codes(self, obj):
        return ', '.join(code.upper() for code, text in obj.title.items() if text) if isinstance(obj.title, dict) else '—'


# Retained for existing installations; unrelated to the translation editor.
admin.site.register(MpttSampleModel, MPTTModelAdmin)
