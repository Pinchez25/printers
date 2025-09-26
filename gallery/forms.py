from django import forms
from taggit.forms import TagWidget
from unfold.widgets import UnfoldAdminTextInputWidget

from .models import PortfolioItem

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