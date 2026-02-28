// Music Player JavaScript

class MusicPlayer {
    constructor() {
        this.audio = new Audio();
        this.isPlaying = false;
        this.currentSong = null;
        this.playlist = [];
        this.currentIndex = 0;
        
        this.init();
    }
    
    init() {
        // Initialize event listeners
        this.audio.addEventListener('timeupdate', () => this.updateProgress());
        this.audio.addEventListener('ended', () => this.next());
        
        // Setup controls
        this.setupControls();
    }
    
    setupControls() {
        // Play/Pause button
        $('.play-pause').click(() => this.togglePlay());
        
        // Next button
        $('.next').click(() => this.next());
        
        // Previous button
        $('.prev').click(() => this.previous());
        
        // Volume control
        $('.volume-control').on('input', (e) => {
            this.audio.volume = e.target.value / 100;
        });
        
        // Progress bar
        $('.progress-bar').click((e) => {
            const percent = e.offsetX / e.target.offsetWidth;
            this.audio.currentTime = percent * this.audio.duration;
        });
    }
    
    loadSong(song) {
        this.currentSong = song;
        this.audio.src = song.audio_url;
        this.updateSongInfo();
    }
    
    play() {
        this.audio.play();
        this.isPlaying = true;
        $('.play-pause i').removeClass('fa-play').addClass('fa-pause');
    }
    
    pause() {
        this.audio.pause();
        this.isPlaying = false;
        $('.play-pause i').removeClass('fa-pause').addClass('fa-play');
    }
    
    togglePlay() {
        this.isPlaying ? this.pause() : this.play();
    }
    
    next() {
        if (this.currentIndex < this.playlist.length - 1) {
            this.currentIndex++;
            this.loadSong(this.playlist[this.currentIndex]);
            this.play();
        }
    }
    
    previous() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            this.loadSong(this.playlist[this.currentIndex]);
            this.play();
        }
    }
    
    updateProgress() {
        const percent = (this.audio.currentTime / this.audio.duration) * 100;
        $('.progress-fill').css('width', percent + '%');
        
        // Update time display
        const current = this.formatTime(this.audio.currentTime);
        const duration = this.formatTime(this.audio.duration);
        $('.current-time').text(current);
        $('.duration').text(duration);
    }
    
    formatTime(seconds) {
        if (isNaN(seconds)) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    updateSongInfo() {
        if (this.currentSong) {
            $('.now-playing-title').text(this.currentSong.title);
            $('.now-playing-artist').text(this.currentSong.artist);
            
            if (this.currentSong.cover) {
                $('.now-playing-cover').attr('src', this.currentSong.cover);
            }
        }
    }
    
    setPlaylist(songs, startIndex = 0) {
        this.playlist = songs;
        this.currentIndex = startIndex;
        this.loadSong(this.playlist[this.currentIndex]);
    }
}

// Like/Unlike functionality
function setupLikeButtons() {
    $('.like-button').click(function() {
        const button = $(this);
        const songId = button.data('song-id');
        const action = button.hasClass('liked') ? 'unlike' : 'like';
        
        $.ajax({
            url: '/like-song/',
            method: 'POST',
            data: JSON.stringify({
                song_id: songId,
                action: action
            }),
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            success: function(response) {
                if (response.success) {
                    button.toggleClass('liked');
                    button.find('.like-count').text(response.likes_count);
                    
                    if (action === 'like') {
                        button.find('i').removeClass('far').addClass('fas');
                    } else {
                        button.find('i').removeClass('fas').addClass('far');
                    }
                }
            }
        });
    });
}

// Add to playlist functionality
function setupPlaylistButtons() {
    $('.add-to-playlist').click(function() {
        const songId = $(this).data('song-id');
        $('#playlistModal').modal('show');
        $('#playlistModal .add-to-playlist-btn').data('song-id', songId);
    });
}

// Cookie helper function
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Initialize when document is ready
$(document).ready(function() {
    setupLikeButtons();
    setupPlaylistButtons();
});