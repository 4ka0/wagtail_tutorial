from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

# Orderable adds sort_order to the images model to keep track of image order
from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import (
    FieldPanel, InlinePanel, MultiFieldPanel
)
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


class BlogPageTag(TaggedItemBase):
    '''
    Model for tags that can be attached to a blog entry. Has to be defined
    prior to the BlogPage model.
    '''

    # ParentalKey is similar to ForeignKey in that it attaches this model to
    # a parent model, but it also explicitly defines this model as being
    # a child of BlogPage so that it is treated as a basic part of a page
    # when submitting for moderation and tracking version history.
    content_object = ParentalKey(
        'BlogPage', related_name='tagged_items', on_delete=models.CASCADE
    )


class BlogPage(Page):
    date = models.DateField('Post date')
    intro = models.CharField(max_length=250)
    body = RichTextField(blank=True)
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)

    def main_image(self):
        '''
        Returns the first image for a given blog page.
        '''
        gallery_item = self.gallery_images.first()
        if gallery_item:
            return gallery_item.image
        else:
            return None

    def get_tags(self):
        '''
        Returns all tags for given blog page.
        '''
        tags = self.tags.all()
        for tag in tags:
            tag.url = '/' + '/'.join(s.strip('/') for s in [
                self.get_parent().url,
                'tags',
                tag.slug
            ])
        return tags

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body'),
    ]

    # Content panels are panels that can be edited by the user on the editing
    # interface for BlogPage.
    content_panels = Page.content_panels + [
        MultiFieldPanel([  # Used to group multiple fields into single panel
            FieldPanel('date'),
            FieldPanel('tags'),
        ], heading='Blog information'),
        FieldPanel('intro'),
        FieldPanel('body'),
        InlinePanel('gallery_images', label='Gallery images'),
    ]


class BlogPageGalleryImage(Orderable):
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


class BlogTagIndexPage(Page):

    def get_all_tags(self):
        tags = []
        blogpages = BlogPage.objects.live()
        for page in blogpages:
            tags += page.get_tags()
        tags = sorted(set(tags))

    def get_context(self, request):
        tag = request.GET.get('tag')
        if tag:
            # Filter blog posts by tag and add to context
            blogpages = BlogPage.objects.filter(tags__name=tag)
            context = super().get_context(request)
            context['blogpages'] = blogpages
            return context
        else:
            # Add all available tags to context
            blogpages = BlogPage.objects.all()
            context = super().get_context(request)
            context['tags'] = self.get_all_tags()
            return context
