from django.db import models
from django.utils.text import slugify
from django.urls import reverse


def create_slug(title, id):
    slug = str(slugify(title)) + '-' + str(id)
    return slug


class MainCategory(models.Model):
    title = models.CharField(max_length=30)
    slug = models.SlugField(unique=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.slug:
            self.slug = create_slug(self.title, self.id)
        super().save(*args, **kwargs)


class UnderCategory(models.Model):
    title = models.CharField(max_length=30)
    slug = models.SlugField(unique=True, blank=True)
    main_category = models.ManyToManyField(MainCategory, related_name='under_category')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('undercategory_books', kwargs={'under_category_slug': self.slug})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.slug:
            self.slug = create_slug(self.title, self.id)
        super().save(*args, **kwargs)


class Book(models.Model):
    title = models.CharField(max_length=40)
    image = models.ImageField(default='../media/default.png')
    slug = models.SlugField(unique=True, blank=True)
    info = models.TextField(max_length=300)
    price = models.DecimalField(max_digits=5, decimal_places=2, default=50.00)
    under_category = models.ManyToManyField(UnderCategory, related_name='book')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.slug:
            self.slug = create_slug(self.title, self.id)
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        return reverse('book_detail', kwargs={'book_slug': self.slug})

    def __str__(self):
        return self.title