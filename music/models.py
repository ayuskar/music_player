from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import os

def song_upload_path(instance, filename):
    return f'music/songs/{instance.artist}/{filename}'

def cover_upload_path(instance, filename):
    return f'music/covers/{instance.artist}/{filename}'

class Genre(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Artist(models.Model):
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    image = models.ImageField(upload_to='artists/', null=True, blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Album(models.Model):
    title = models.CharField(max_length=200)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='albums')
    cover_image = models.ImageField(upload_to='albums/', null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    genre = models.ManyToManyField(Genre, blank=True)
    
    class Meta:
        ordering = ['-release_date', 'title']
    
    def __str__(self):
        return f"{self.title} - {self.artist.name}"

class Song(models.Model):
    title = models.CharField(max_length=200)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='songs')
    album = models.ForeignKey(Album, on_delete=models.SET_NULL, null=True, blank=True, related_name='songs')
    genre = models.ManyToManyField(Genre, blank=True)
    audio_file = models.FileField(upload_to=song_upload_path)
    cover_image = models.ImageField(upload_to=cover_upload_path, null=True, blank=True)
    duration = models.CharField(max_length=10, blank=True)  # Store as "MM:SS"
    lyrics = models.TextField(blank=True)
    lyrics_source = models.CharField(max_length=20, choices=[
        ('manual', 'Manual'),
        ('generated', 'AI Generated'),
    ], default='manual')
    plays_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_songs')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - {self.artist.name}"
    
    def get_audio_url(self):
        return self.audio_file.url if self.audio_file else ''
    
    def increment_plays(self):
        self.plays_count += 1
        self.save()

class Playlist(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    songs = models.ManyToManyField(Song, through='PlaylistSong')
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"

class PlaylistSong(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'added_at']

class UserSongInteraction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    is_liked = models.BooleanField(default=False)
    played_at = models.DateTimeField(auto_now=True)
    play_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'song']

class RecentPlay(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recent_plays')
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    played_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-played_at']
        unique_together = ['user', 'song']