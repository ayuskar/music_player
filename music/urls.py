from django.urls import path
from . import views

app_name = 'music'

urlpatterns = [
    path('', views.home, name='home'),
    path('song/<int:song_id>/', views.song_detail, name='song_detail'),
    path('song/<int:song_id>/add-to-playlist/', views.add_to_playlist, name='add_to_playlist'),
    path('playlist/create/', views.create_playlist, name='create_playlist'),
    path('playlist/<int:playlist_id>/', views.playlist_detail, name='playlist_detail'),
    path('search/', views.search, name='search'),
    path('like-song/', views.like_song, name='like_song'),
    path('genre/<int:genre_id>/', views.genre_view, name='genre'),
    path('artist/<int:artist_id>/', views.artist_view, name='artist'),
    
    # Admin URLs
    path('admin/add-song/', views.add_song, name='add_song'),
    path('admin/manage-songs/', views.manage_songs, name='manage_songs'),
]