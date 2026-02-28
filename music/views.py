from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Song, Playlist, Artist, Album, Genre, UserSongInteraction, RecentPlay
from .utils import LyricsGenerator
import json

def home(request):
    """Home page with featured songs and recommendations"""
    
    # Get recent songs
    recent_songs = Song.objects.filter(is_active=True).order_by('-uploaded_at')[:10]
    
    # Get popular songs
    popular_songs = Song.objects.filter(is_active=True).order_by('-plays_count')[:10]
    
    # Get featured artists
    featured_artists = Artist.objects.all()[:6]
    
    # Get genres
    genres = Genre.objects.annotate(song_count=Count('song')).filter(song_count__gt=0)[:8]
    
    context = {
        'recent_songs': recent_songs,
        'popular_songs': popular_songs,
        'featured_artists': featured_artists,
        'genres': genres,
    }
    
    return render(request, 'music/home.html', context)

def song_detail(request, song_id):
    """Display song details with lyrics"""
    song = get_object_or_404(Song, id=song_id, is_active=True)
    
    # Log the play if user is logged in
    if request.user.is_authenticated:
        # Update or create interaction
        interaction, created = UserSongInteraction.objects.get_or_create(
            user=request.user,
            song=song,
            defaults={'play_count': 1}
        )
        if not created:
            interaction.play_count += 1
            interaction.save()
        
        # Add to recent plays
        RecentPlay.objects.update_or_create(
            user=request.user,
            song=song,
            defaults={'played_at': song.uploaded_at}
        )
    
    # Get similar songs
    similar_songs = Song.objects.filter(
        Q(artist=song.artist) | Q(genre__in=song.genre.all())
    ).exclude(id=song.id).distinct()[:5]
    
    context = {
        'song': song,
        'similar_songs': similar_songs,
    }
    return render(request, 'music/song_detail.html', context)

@login_required
def add_to_playlist(request, song_id):
    """Add a song to a playlist"""
    song = get_object_or_404(Song, id=song_id)
    
    if request.method == 'POST':
        playlist_id = request.POST.get('playlist_id')
        playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
        
        # Check if song is already in playlist
        if not playlist.songs.filter(id=song.id).exists():
            playlist.songs.add(song)
            messages.success(request, f'Song added to {playlist.name}')
        else:
            messages.info(request, 'Song already in playlist')
    
    return redirect('music:song_detail', song_id=song_id)

@login_required
def create_playlist(request):
    """Create a new playlist"""
    if request.method == 'POST':
        name = request.POST.get('name')
        is_public = request.POST.get('is_public') == 'on'
        
        playlist = Playlist.objects.create(
            name=name,
            user=request.user,
            is_public=is_public
        )
        messages.success(request, f'Playlist "{name}" created successfully!')
        return redirect('music:playlist_detail', playlist_id=playlist.id)
    
    return render(request, 'music/create_playlist.html')

@login_required
def playlist_detail(request, playlist_id):
    """View a playlist"""
    playlist = get_object_or_404(Playlist, id=playlist_id)
    
    # Check if user has permission to view
    if not playlist.is_public and playlist.user != request.user:
        messages.error(request, 'You do not have permission to view this playlist')
        return redirect('music:home')
    
    return render(request, 'music/playlist_detail.html', {'playlist': playlist})

def search(request):
    """Search for songs, artists, and albums"""
    query = request.GET.get('q', '')
    
    if query:
        songs = Song.objects.filter(
            Q(title__icontains=query) | 
            Q(artist__name__icontains=query) |
            Q(album__title__icontains=query),
            is_active=True
        ).distinct()
        
        artists = Artist.objects.filter(name__icontains=query)
        albums = Album.objects.filter(title__icontains=query)
        
        context = {
            'query': query,
            'songs': songs,
            'artists': artists,
            'albums': albums,
        }
    else:
        context = {
            'query': '',
            'songs': [],
            'artists': [],
            'albums': [],
        }
    
    return render(request, 'music/search.html', context)

@login_required
@require_POST
def like_song(request):
    """AJAX view to like/unlike a song"""
    try:
        data = json.loads(request.body)
        song_id = data.get('song_id')
        action = data.get('action')  # 'like' or 'unlike'
        
        song = get_object_or_404(Song, id=song_id)
        interaction, created = UserSongInteraction.objects.get_or_create(
            user=request.user,
            song=song
        )
        
        if action == 'like':
            interaction.is_liked = True
            song.likes_count += 1
        elif action == 'unlike':
            interaction.is_liked = False
            song.likes_count -= 1
        
        interaction.save()
        song.save()
        
        return JsonResponse({
            'success': True,
            'likes_count': song.likes_count,
            'is_liked': interaction.is_liked
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Admin Views for Song Management

@staff_member_required
def add_song(request):
    """Admin view to add a new song"""
    if request.method == 'POST':
        title = request.POST.get('title')
        artist_id = request.POST.get('artist')
        album_id = request.POST.get('album')
        audio_file = request.FILES.get('audio_file')
        cover_image = request.FILES.get('cover_image')
        lyrics = request.POST.get('lyrics')
        generate_lyrics = request.POST.get('generate_lyrics') == 'on'
        
        # Create or get artist
        artist, _ = Artist.objects.get_or_create(name=artist_id)
        
        # Create or get album
        album = None
        if album_id:
            album, _ = Album.objects.get_or_create(title=album_id, artist=artist)
        
        # Create song
        song = Song.objects.create(
            title=title,
            artist=artist,
            album=album,
            audio_file=audio_file,
            cover_image=cover_image,
            uploaded_by=request.user
        )
        
        # Handle lyrics
        if generate_lyrics:
            generator = LyricsGenerator()
            generated_lyrics = generator.generate_lyrics(title, artist.name)
            song.lyrics = generated_lyrics
            song.lyrics_source = 'generated'
        else:
            song.lyrics = lyrics
            song.lyrics_source = 'manual'
        
        # Set duration (you might want to extract from audio file)
        song.duration = "03:30"  # Placeholder
        
        # Add genres
        genre_ids = request.POST.getlist('genres')
        song.genre.set(genre_ids)
        
        song.save()
        
        messages.success(request, f'Song "{title}" added successfully!')
        return redirect('music:song_detail', song_id=song.id)
    
    artists = Artist.objects.all()
    albums = Album.objects.all()
    genres = Genre.objects.all()
    
    context = {
        'artists': artists,
        'albums': albums,
        'genres': genres,
    }
    return render(request, 'music/add_song.html', context)

@staff_member_required
def manage_songs(request):
    """Admin view to manage songs"""
    songs = Song.objects.all().order_by('-uploaded_at')
    return render(request, 'music/manage_songs.html', {'songs': songs})

def genre_view(request, genre_id):
    """View songs by genre"""
    genre = get_object_or_404(Genre, id=genre_id)
    songs = Song.objects.filter(genre=genre, is_active=True)
    
    context = {
        'genre': genre,
        'songs': songs,
    }
    return render(request, 'music/genre.html', context)

def artist_view(request, artist_id):
    """View artist details and their songs"""
    artist = get_object_or_404(Artist, id=artist_id)
    songs = Song.objects.filter(artist=artist, is_active=True)
    albums = Album.objects.filter(artist=artist)
    
    context = {
        'artist': artist,
        'songs': songs,
        'albums': albums,
    }
    return render(request, 'music/artist.html', context)
@login_required
def delete_playlist(request, playlist_id):
    """Delete a playlist"""
    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    
    if request.method == 'POST':
        playlist.delete()
        messages.success(request, f'Playlist "{playlist.name}" deleted successfully.')
    
    return redirect('accounts:profile')

@login_required
@require_POST
def remove_from_playlist(request, playlist_id):
    """Remove a song from playlist"""
    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    song_id = request.POST.get('song_id')
    
    if song_id:
        playlist.songs.remove(song_id)
        messages.success(request, 'Song removed from playlist.')
    
    return redirect('music:playlist_detail', playlist_id=playlist_id)

@staff_member_required
def delete_song(request, song_id):
    """Delete a song (admin only)"""
    song = get_object_or_404(Song, id=song_id)
    
    if request.method == 'POST':
        song.delete()
        messages.success(request, f'Song "{song.title}" deleted successfully.')
    
    return redirect('music:manage_songs')

@staff_member_required
def edit_song(request, song_id):
    """Edit a song (admin only)"""
    song = get_object_or_404(Song, id=song_id)
    
    if request.method == 'POST':
        # Handle edit form submission
        song.title = request.POST.get('title')
        # ... update other fields
        song.save()
        messages.success(request, 'Song updated successfully.')
        return redirect('music:song_detail', song_id=song.id)
    
    artists = Artist.objects.all()
    albums = Album.objects.all()
    genres = Genre.objects.all()
    
    context = {
        'song': song,
        'artists': artists,
        'albums': albums,
        'genres': genres,
    }
    return render(request, 'music/edit_song.html', context)