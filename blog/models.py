from django import forms
from django.db import models
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

from wagtail.core import blocks
from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import (
    FieldPanel, MultiFieldPanel, StreamFieldPanel
)
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index
from wagtail.snippets.models import register_snippet
from wagtail.core.fields import StreamField
from wagtail.images.blocks import ImageChooserBlock

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase


class BlogIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname='full')
    ]

    def get_all_tags():
        '''
        Returns a list of all tags associated with all live blog posts.
        '''
        tags = []
        blog_pages = BlogPage.objects.live()
        for page in blog_pages:
            tags += page.get_post_tags()
        tags = sorted(set(tags))
        return tags

    def get_context(self, request):
        '''
        Overrides the default get_context() so that:
        - the context includes published posts in reverse chronological order,
        - the context includes a list of all current tags, and
        - the results are paginated
        '''
        context = super().get_context(request)

        all_posts = self.get_children().live().order_by('-first_published_at')

        context['tags'] = BlogIndexPage.get_all_tags()

        paginator = Paginator(all_posts, 5)
        page = request.GET.get('page')
        try:
            # If the page exists and the page=x is an int
            posts = paginator.page(page)
        except PageNotAnInteger:
            # If page=x is not an int; show the first page
            posts = paginator.page(1)
        except EmptyPage:
            # If page=x is out of range: return the last page
            posts = paginator.page(paginator.num_pages)
        context['posts'] = posts

        return context


class BlogPageTag(TaggedItemBase):
    '''
    Model for tags that can be attached to blog posts.
    '''

    # This class has to be defined prior to the BlogPage model.
    # ParentalKey is similar to ForeignKey in that it attaches this model to
    # a parent model, but it also explicitly defines this model as being
    # a child of BlogPage so that it is treated as a basic part of a page
    # when submitting for moderation and tracking version history.
    content_object = ParentalKey(
        'BlogPage', related_name='tagged_items', on_delete=models.CASCADE
    )


class BlogPage(Page):
    date = models.DateField('Post date')
    body = StreamField([
        ('heading', blocks.CharBlock(form_classname='full title')),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
    ])
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    categories = ParentalManyToManyField('blog.BlogCategory', blank=True)

    # Set as a searchable field
    search_fields = Page.search_fields + [
        index.SearchField('body'),
    ]

    # Content panels are panels that can be edited by the user on the editing
    # interface for BlogPage.
    content_panels = Page.content_panels + [
        MultiFieldPanel([  # Used to group multiple fields into single panel
            FieldPanel('date'),
            FieldPanel('tags'),
            FieldPanel('categories', widget=forms.CheckboxSelectMultiple),
        ], heading='Blog information'),
        StreamFieldPanel('body'),
    ]

    def get_first_image(self):
        '''
        Returns the first image from the body StreamField.
        Used for the blog post index page.
        '''
        for block in self.body:
            if block.block_type == 'image':
                return block.value

    def get_post_tags(self):
        '''
        Returns all tags that are related to the blog post in question as a
        list that can be accessed in the template.
        Additionally, a URL is added so that the relevant post can be accessed
        with the tag in question.
        (Taken from the Wagtail bakery demo:)
        https://github.com/wagtail/bakerydemo/blob/4469a5a182f3c34db520979bd257a9a5cc4620fa/bakerydemo/blog/models.py#L110
        '''
        tags = self.tags.all()
        for tag in tags:
            tag.url = '/' + '/'.join(s.strip('/') for s in [
                self.get_parent().url,
                'tags',
                tag.slug
            ])
        return tags


class BlogPageGalleryImage(Orderable):

    # Sub-classing Orderable makes it possible to keep track of the image order

    page = ParentalKey(
        BlogPage, on_delete=models.CASCADE, related_name='gallery_images'
    )

    # 'image' is a ForeignKey to Wagtail???s built-in Image model, where the
    # images themselves are stored. This comes with a dedicated panel type,
    # ImageChooserPanel, which provides a pop-up interface for choosing an
    # existing image or uploading a new one. This way, we allow an image to
    # exist in multiple galleries - effectively, we???ve created a many-to-many
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
    '''
    Overrides the default get_context() so that:
    - the context includes only posts associated with a given tag, and
    - the context includes a list of all current tags.
    '''

    def get_context(self, request):
        context = super().get_context(request)

        tag = request.GET.get('tag')
        posts = BlogPage.objects.live().filter(tags__name=tag) \
            .order_by('-first_published_at')
        context['posts'] = posts

        tags = BlogIndexPage.get_all_tags()
        context['tags'] = tags

        return context


@register_snippet
class BlogCategory(models.Model):
    name = models.CharField(max_length=255)
    icon = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    panels = [
        FieldPanel('name'),
        ImageChooserPanel('icon'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'blog categories'
