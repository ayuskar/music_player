from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Genre, Artist, Album, Song, Playlist, PlaylistSong

class SongAdmin(admin.ModelAdmin):
    list_display = ['title', 'artist', 'album', 'plays_count', 'likes_count', 'uploaded_at']
    list_filter = ['artist', 'genre', 'uploaded_at']
    search_fields = ['title', 'artist__name']
    readonly_fields = ['plays_count', 'likes_count', 'uploaded_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'artist', 'album', 'genre')
        }),
        ('Media Files', {
            'fields': ('audio_file', 'cover_image')
        }),
        ('Lyrics', {
            'fields': ('lyrics', 'lyrics_source')
        }),
        ('Metadata', {
            'fields': ('duration', 'is_active')
        }),
        ('Statistics', {
            'fields': ('plays_count', 'likes_count')
        }),
    )

admin.site.register(Genre)
admin.site.register(Artist)
admin.site.register(Album)
admin.site.register(Song, SongAdmin)
admin.site.register(Playlist)