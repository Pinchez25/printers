from django import forms
from taggit.forms import TagWidget
from unfold.widgets import UnfoldAdminTextInputWidget
from unfold.fields import INPUT_CLASSES

from .models import CompanyConfig, PortfolioItem

class UnfoldTagWidget(TagWidget):
    """Custom tag widget that copies unfold's TextInput styling"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create a temporary UnfoldAdminTextInputWidget to get its classes
        temp_widget = UnfoldAdminTextInputWidget()
        unfold_classes = temp_widget.attrs.get('class', '')

        # Apply the same classes plus our placeholder
        self.attrs.update({
            'class': unfold_classes,
            'placeholder': 'Add tags separated by commas',
        })


class PortfolioItemForm(forms.ModelForm):
    class Meta:
        model = PortfolioItem
        fields = '__all__'
        widgets = {
            'tags': UnfoldTagWidget(),
        }

class CompanyConfigAdminForm(forms.ModelForm):
    class Meta:
        model = CompanyConfig
        fields = '__all__'
        widgets = {
            'email_password': forms.PasswordInput(render_value=True),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email_password'].widget.attrs.update({
            'class': ' '.join(INPUT_CLASSES),
        })