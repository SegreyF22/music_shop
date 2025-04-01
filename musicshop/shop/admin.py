from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import *


class MemberInline(admin.TabularInline):
    model = Artist.members.through


class ImageGalleryInline(GenericTabularInline):
    model = ImageGallery
    readonly_fields = ('image_url',)  # чтобы видеть не ссылку на изображение, а само изобр.

@admin.register(Album)
class AlbumInlines(admin.ModelAdmin):
    inlines = [ImageGalleryInline]

@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    inlines = [MemberInline, ImageGalleryInline]
    exclude = ('members',)


admin.site.register(Genre)
admin.site.register(Member)
admin.site.register(MediaType)
admin.site.register(ImageGallery)
admin.site.register(Cart)
admin.site.register(CartProduct)
admin.site.register(Order)
admin.site.register(Customer)
admin.site.register(Notification)
