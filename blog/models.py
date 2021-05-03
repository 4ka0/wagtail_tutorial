from django.db import models

from modelcluster.fields import ParentalKey

# Orderable adds sort_order to the images model to keep track of image order
from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index


class BlogIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname='full')
    ]

    def get_context(self, request):
        '''
        Overrides the default get_context() such that the context dictionary
        includes published posts in reverse chronological order.
        '''
        context = super().get_context(request)
        blogpages = self.get_children().live().order_by('-first_published_at')
        context['blogpages'] = blogpages
        return context


class BlogPage(Page):
    date = models.DateField('Post date')
    intro = models.CharField(max_length=250)
    body = RichTextField(blank=True)

    def main_image(self):
        gallery_item = self.gallery_images.first()
        if gallery_item:
            return gallery_item.image
        else:
            return None

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    # Content panels are panels that can be edited by the user on the editing
    # interface for BlogPage.
    content_panels = Page.content_panels + [
        FieldPanel('date'),
        FieldPanel('intro'),
        FieldPanel('body', classname='full'),
        InlinePanel('gallery_images', label='Gallery images'),
    ]


class BlogPageGalleryImage(Orderable):
    # ParentalKey is similar to ForeignKey in that it attaches this model to
    # a parent model, but it also explicitly defines this model as being
    # a child of BlogPage so that it is treated as a basic part of a page
    # when submitting for moderation and tracking version history.
    page = ParentalKey(
        BlogPage, on_delete=models.CASCADE, related_name='gallery_images'
    )

    # image is a ForeignKey to Wagtail’s built-in Image model, where the
    # images themselves are stored. This comes with a dedicated panel type,
    # ImageChooserPanel, which provides a pop-up interface for choosing an
    # existing image or uploading a new one. This way, we allow an image to
    # exist in multiple galleries - effectively, we’ve created a many-to-many
    # relationship between pages and images.
    # Specifying on_delete=models.CASCADE on the foreign key means that if the
    # image is deleted from the system, the gallery entry is deleted as well.
    image = models.ForeignKey(
        'wagtailimages.Image', on_delete=models.CASCADE, related_name='+'
    )

    caption = models.CharField(blank=True, max_length=250)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('caption'),
    ]
