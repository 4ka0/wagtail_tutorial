from django.db import models

from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.snippets.models import register_snippet

from modelcluster.fields import ParentalKey


class HomePage(Page):
    name = models.CharField(blank=False, null=True, max_length=200)
    intro = RichTextField(
        blank=False, null=True, features=['h2', 'h3', 'bold', 'italic']
    )

    content_panels = Page.content_panels + [
        InlinePanel('gallery_images', label='Gallery images'),
        FieldPanel('name', classname="full"),
        FieldPanel('intro', classname="full"),
    ]


class HomePageGalleryImage(Orderable):
    page = ParentalKey(
        HomePage, on_delete=models.CASCADE, related_name='gallery_images'
    )

    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )

    panels = [
        ImageChooserPanel('image'),
    ]


@register_snippet
class Footer(models.Model):
    text = RichTextField(
        blank=False, null=True, features=['bold', 'italic', 'link']
    )
    max_count = 1

    panels = [
        FieldPanel('text'),
    ]

    def __str__(self):
        return self.text
