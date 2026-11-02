"""Language-aware JSON forms built on Django's public form APIs."""
from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def translation_languages():
    languages = tuple(settings.LANGUAGES)
    codes = [code for code, _ in languages]
    if not languages or len(codes) != len(set(codes)) or any(not code for code in codes):
        raise ImproperlyConfigured('LANGUAGES must contain unique, non-empty language codes.')
    if settings.DEFAULT_LANGUAGE_CODE not in codes:
        raise ImproperlyConfigured('DEFAULT_LANGUAGE_CODE must be listed in LANGUAGES.')
    return languages


class TranslationWidget(forms.MultiWidget):
    template_name = 'translationapp/widgets/translations.html'

    def __init__(self, languages, attrs=None):
        self.languages = languages
        widgets = {
            code: forms.Textarea(attrs={
                'rows': 3, 'lang': code, 'dir': 'auto',
                'class': 'translation-input',
            }) for code, _ in languages
        }
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if not isinstance(value, dict):
            return [''] * len(self.languages)
        return [value.get(code, '') for code, _ in self.languages]

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        for subwidget, (code, label) in zip(context['widget']['subwidgets'], self.languages):
            if context['widget']['attrs'].get('id'):
                subwidget['attrs']['id'] = f"{context['widget']['attrs']['id']}_{code}"
            subwidget['language_code'] = code
            subwidget['language_label'] = label
            subwidget['is_default'] = code == settings.DEFAULT_LANGUAGE_CODE
        return context

    class Media:
        css = {'all': ('translationapp/editor.css',)}


class TranslationFormField(forms.MultiValueField):
    def __init__(self, *, encoder=None, decoder=None, **kwargs):
        languages = translation_languages()
        self.codes = [code for code, _ in languages]
        required = kwargs.get('required', True)
        fields = [
            forms.CharField(
                required=required and code == settings.DEFAULT_LANGUAGE_CODE,
                error_messages={'incomplete': f'Enter a translation for {label} ({code}).'},
            ) for code, label in languages
        ]
        kwargs.setdefault('widget', TranslationWidget(languages))
        super().__init__(fields=fields, require_all_fields=False, **kwargs)

    def compress(self, data_list):
        return dict(zip(self.codes, data_list or [''] * len(self.codes)))
