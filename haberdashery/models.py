from django.db import models
from django.utils.text import slugify

class Haberdashery(models.Model):
    workshop = models.OneToOneField(
        "workshop.Workshop", on_delete=models.CASCADE, related_name="haberdashery", unique=True)
    workers = models.ManyToManyField(
        "workshop.Worker",  blank=True, related_name="haberdashery")
    is_active = models.BooleanField(default=False)
    end_date = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Haberdashery'
        verbose_name_plural = 'Haberdasheries'

class TypeArticleInHaberdashery(models.Model):
    haberdashery = models.ForeignKey(
        Haberdashery, on_delete=models.CASCADE, related_name="type_articles")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, primary_key=True)
    description = models.TextField()
    is_delete = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['name']
        unique_together = ('name', 'haberdashery')
        verbose_name = 'Type d\'article dans le Haberdashery'
        verbose_name_plural = 'Types d\'articles dans le Haberdashery'
    
    def save(self, *args, **kwargs):
        # Création
        if not self.pk and not self.slug:
            self.slug = slugify(self.name)

        # Mise à jour
        elif self.pk:
            old_name = type(self).objects.only("name").get(pk=self.pk).name
            if self.name != old_name or not self.slug:
                self.slug = slugify(self.name)
        return super().save(*args, **kwargs)


class ArticleInHaberdashery(models.Model):
    type_article = models.ForeignKey(
        TypeArticleInHaberdashery, on_delete=models.CASCADE, related_name="articles")
    name = models.CharField(max_length=255)
    quantity = models.SmallIntegerField(default=0)
    is_delete = models.BooleanField(default=False)
    is_out = models.BooleanField(default=False)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Article dans le Haberdashery'
        verbose_name_plural = 'Articles dans le Haberdashery'
        ordering = ['-createdAt']
        unique_together = ("name", "type_article")
        
    def __str__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        if self.quantity < 0:
            self.quantity = 0
        return super().save(*args, **kwargs)


