import io
from dataclasses import dataclass

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

from gallery.models import CompanyConfig, PortfolioItem


def _make_image_file(name: str = "test.png", size=(50, 50), colour=(255, 0, 0)):
    buffer = io.BytesIO()
    Image.new("RGB", size, colour).save(buffer, format="PNG")
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type="image/png")


@dataclass
class PortfolioItemFactory:
    title: str = "sample title"
    description: str = ""
    is_published: bool = True
    tags: list[str] | None = None

    def create(self) -> PortfolioItem:
        item = PortfolioItem.objects.create(
            title=self.title,
            description=self.description,
            is_published=self.is_published,
            image=_make_image_file(),
        )
        if self.tags:
            item.tags.add(*self.tags)
        return item


def ensure_company_config(email_configured: bool = True, always_save: bool = False) -> CompanyConfig:
    cfg = CompanyConfig.get_instance()
    cfg.always_save_contactus_queries = always_save
    if email_configured:
        cfg.email_username = "noreply@example.com"
        cfg.email_password = "secret"
        cfg.email_from_address = "from@example.com"
        cfg.email_to_address = "to@example.com"
        cfg.email_host = "smtp.example.com"
        cfg.email_port = 587
        cfg.email_use_tls = True
    else:
        cfg.email_username = ""
        cfg.email_password = ""
    cfg.save()
    return cfg
