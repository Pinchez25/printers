from django import forms
from django.test import SimpleTestCase

from gallery.forms import CompanyConfigAdminForm, PortfolioItemForm, UnfoldTagWidget


class FormTests(SimpleTestCase):
    def test_portfolio_item_form_uses_unfold_tag_widget(self):
        form = PortfolioItemForm()
        self.assertIsInstance(form.fields["tags"].widget, UnfoldTagWidget)

    def test_company_config_admin_form_password_widget_has_render_value(self):
        form = CompanyConfigAdminForm()
        self.assertIsInstance(form.fields["email_password"].widget, forms.PasswordInput)
        self.assertTrue(form.fields["email_password"].widget.render_value)
