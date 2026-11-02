from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.test import TestCase, SimpleTestCase, override_settings
from django.urls import reverse

from core.CustomFields import JsonFieldWithTranslation
from core.translation_forms import TranslationFormField, TranslationWidget
from .forms import SampleModelForm
from .models import SampleModel


class TranslationFieldTests(SimpleTestCase):
    def test_compress_languages_and_unicode(self):
        self.assertEqual(TranslationFormField().clean(['Hello', 'Bonjour', 'مرحبا']),
                         {'en': 'Hello', 'fr': 'Bonjour', 'ar': 'مرحبا'})

    def test_default_language_is_required(self):
        with self.assertRaises(ValidationError):
            TranslationFormField().clean(['', 'Bonjour', ''])

    def test_other_languages_are_optional(self):
        self.assertEqual(TranslationFormField().clean(['Hello', '', '']),
                         {'en': 'Hello', 'fr': '', 'ar': ''})

    def test_blank_model_field_is_optional(self):
        field = JsonFieldWithTranslation(blank=True).formfield()
        self.assertEqual(field.clean(['', '', '']), {'en': '', 'fr': '', 'ar': ''})

    def test_optional_clear_removes_configured_text_but_preserves_other_languages(self):
        field = JsonFieldWithTranslation(blank=True)
        field.set_attributes_from_name('content')
        class Record:
            content = {'en': 'Old', 'fr': 'Ancien', 'de': 'Behalten'}
        instance = Record()
        field.save_form_data(instance, field.formfield().clean(['', '', '']))
        self.assertEqual(instance.content, {'en': '', 'fr': '', 'ar': '', 'de': 'Behalten'})

    def test_widget_handles_missing_and_non_object_values(self):
        widget = TranslationWidget((('en', 'English'), ('fr', 'French')))
        for value in (None, [], 'legacy text', 3):
            self.assertEqual(widget.decompress(value), ['', ''])
        self.assertEqual(widget.decompress({'en': 'Hello'}), ['Hello', ''])

    def test_render_labels_stable_names_and_escaping(self):
        html = str(SampleModelForm(initial={'title': {'en': '<script>alert(1)</script>'}})['title'])
        self.assertIn('name="title_en"', html)
        self.assertIn('for="id_title_en"', html)
        self.assertIn('English', html)
        self.assertIn('dir="auto"', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>', html)

    @override_settings(LANGUAGES=[('pt-br', 'Brazilian Portuguese'), ('en_us', 'English')],
                       DEFAULT_LANGUAGE_CODE='pt-br')
    def test_locale_codes_are_not_parsed_from_field_names(self):
        self.assertEqual(TranslationFormField().clean(['Olá', 'Hello']),
                         {'pt-br': 'Olá', 'en_us': 'Hello'})

    @override_settings(LANGUAGES=[('en', 'English'), ('en', 'Duplicate')])
    def test_duplicate_language_configuration_fails(self):
        with self.assertRaises(ImproperlyConfigured):
            TranslationFormField()

    @override_settings(DEFAULT_LANGUAGE_CODE='missing')
    def test_unknown_default_language_fails(self):
        with self.assertRaises(ImproperlyConfigured):
            TranslationFormField()


class TranslationAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create(username='editor', is_staff=True, is_superuser=True)
        cls.user.set_unusable_password()
        cls.user.save()
        cls.first = SampleModel.objects.create(title={'en': 'First', 'de': 'Erste'}, article={'en': 'Body'})
        cls.second = SampleModel.objects.create(title={'en': 'Second'}, article={'en': 'Other'})

    def setUp(self):
        self.client.force_login(self.user)

    def test_plain_model_form_roundtrip_and_unknown_language_preservation(self):
        form = SampleModelForm(data={'title_en': 'Updated', 'title_fr': 'Nouveau',
                                   'article_en': 'Body', 'author': '{"name":"Ada"}'}, instance=self.first)
        self.assertTrue(form.is_valid(), form.errors)
        obj = form.save()
        obj.refresh_from_db()
        self.assertEqual(obj.title, {'en': 'Updated', 'fr': 'Nouveau', 'ar': '', 'de': 'Erste'})
        self.assertEqual(obj.author, {'name': 'Ada'})

    def test_instance_initial_values_are_isolated(self):
        first = SampleModelForm(instance=self.first)
        second = SampleModelForm(instance=self.second)
        self.assertEqual(first['title'].value()['en'], 'First')
        self.assertEqual(second['title'].value()['en'], 'Second')
        self.assertEqual(set(first.fields), set(second.fields))
        self.assertIsNot(first.fields['title'], second.fields['title'])

    def test_standard_jsonfield_keeps_json_editor(self):
        self.assertIsInstance(SampleModelForm().fields['author'], forms.JSONField)

    def test_admin_add_uses_explicit_fieldsets(self):
        response = self.client.get(reverse('admin:translationapp_samplemodel_add'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="title_en"')
        self.assertContains(response, 'name="article_ar"')
        self.assertContains(response, 'Lingua')

    def test_admin_post_saves_json_without_save_model_hacks(self):
        response = self.client.post(reverse('admin:translationapp_samplemodel_add'), {
            'title_en': 'Hello', 'title_fr': 'Bonjour', 'title_ar': 'مرحبا',
            'article_en': 'An article', 'author': '{}', '_save': 'Save',
        })
        self.assertEqual(response.status_code, 302)
        obj = SampleModel.objects.latest('pk')
        self.assertEqual(obj.title['ar'], 'مرحبا')
        self.assertEqual(obj.article['en'], 'An article')

    def test_admin_validation_retains_input(self):
        response = self.client.post(reverse('admin:translationapp_samplemodel_add'), {
            'title_fr': 'Bonjour', 'article_en': 'Body', 'author': '{}',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bonjour')
        self.assertIn('title', response.context['adminform'].form.errors)

    def test_plain_model_admin_works(self):
        model_admin = admin.ModelAdmin(SampleModel, admin.site)
        from django.test import RequestFactory
        request = RequestFactory().get('/')
        request.user = self.user
        form_class = model_admin.get_form(request)
        self.assertIsInstance(form_class().fields['title'], TranslationFormField)
