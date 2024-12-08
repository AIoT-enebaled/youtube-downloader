import os
import re
import yt_dlp
import streamlit as st
from urllib.parse import urlparse, parse_qs
import time

def is_valid_youtube_url(url):
    """Validate YouTube URL and extract video ID."""
    try:
        # Check if URL is valid
        parsed_url = urlparse(url)
        if parsed_url.netloc not in ['www.youtube.com', 'youtube.com', 'youtu.be']:
            return None

        # Extract video ID based on URL format
        if parsed_url.netloc == 'youtu.be':
            return parsed_url.path[1:]
        
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query).get('v', [None])[0]
            
        return None
    except:
        return None

def format_size(bytes):
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} GB"

def sanitize_filename(title):
    """Create a safe filename from the video title."""
    # Remove invalid characters
    filename = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
    # Remove leading/trailing spaces
    filename = filename.strip()
    # Replace multiple spaces with single space
    filename = re.sub(r'\s+', ' ', filename)
    return filename or "video"  # Fallback to "video" if filename is empty

def get_video_info(url):
    """Get video information using yt-dlp."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            
            # Filter and organize formats
            for f in info['formats']:
                # Skip formats without video or audio
                if f.get('vcodec') == 'none' and f.get('acodec') == 'none':
                    continue
                    
                format_info = {
                    'format_id': f['format_id'],
                    'ext': f['ext'],
                    'filesize': format_size(f.get('filesize', 0)) if f.get('filesize') else 'N/A',
                    'format_note': f.get('format_note', ''),
                    'vcodec': 'none' if f.get('vcodec') == 'none' else f.get('vcodec', 'N/A'),
                    'acodec': 'none' if f.get('acodec') == 'none' else f.get('acodec', 'N/A'),
                    'resolution': f.get('resolution', 'N/A'),
                }
                
                # Create a descriptive format string
                if f['vcodec'] == 'none':
                    format_info['description'] = f"Audio only ({format_info['format_note']}) - {format_info['filesize']}"
                else:
                    format_info['description'] = f"Video ({format_info['resolution']}) - {format_info['filesize']}"
                
                formats.append(format_info)
            
            return {
                'title': info.get('title', 'Untitled'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail'),
                'formats': formats,
                'channel': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0)
            }
    except Exception as e:
        st.error(f"Error extracting video information: {str(e)}")
        return None

def download_video(url, save_dir, format_id, is_audio=False):
    """Download video with specified format."""
    try:
        ydl_opts = {
            'format': format_id,
            'outtmpl': os.path.join(save_dir, '%(title)s.%(ext)s'),
            'progress_hooks': [download_progress_hook],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        st.error(f"Error downloading video: {str(e)}")
        return False

def download_progress_hook(d):
    """Progress hook for downloads."""
    if d['status'] == 'downloading':
        try:
            total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                progress = (downloaded / total) * 100
                if 'progress_bar' in st.session_state:
                    st.session_state.progress_bar.progress(int(progress))
        except:
            pass

def main():
    st.set_page_config(page_title="YouTube Video Downloader", page_icon="🎥")
    
    # Custom CSS
    st.markdown("""
        <style>
        .stButton>button {
            width: 100%;
        }
        .streamlit-expanderHeader {
            background-color: #f0f2f6;
        }
        .stAlert > div {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🎥 YouTube Video Downloader")
    st.markdown("---")
    
    # Create downloads directory
    downloads_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(downloads_dir, exist_ok=True)
    
    # URL input
    video_url = st.text_input("🔗 Enter YouTube URL:", placeholder="https://www.youtube.com/watch?v=...")
    
    if video_url:
        try:
            # Extract video ID and validate URL
            video_id = is_valid_youtube_url(video_url)
            if not video_id:
                st.error("❌ Invalid YouTube URL. Please enter a valid YouTube video URL.")
                return

            # Get video information
            info = get_video_info(video_url)
            if not info:
                return
            
            # Show video information
            col1, col2 = st.columns([1, 2])
            with col1:
                if info.get('thumbnail'):
                    st.image(info['thumbnail'], use_container_width=True)
                else:
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                    st.image(thumbnail_url, use_container_width=True)
                    
            with col2:
                st.subheader(info['title'])
                st.write(f"👤 **Channel:** {info['channel']}")
                if info['view_count'] > 0:
                    st.write(f"👁️ **Views:** {info['view_count']:,}")
                if info['duration'] > 0:
                    duration_min = info['duration'] // 60
                    duration_sec = info['duration'] % 60
                    st.write(f"⏱️ **Length:** {duration_min}:{duration_sec:02d} minutes")
            
            st.markdown("---")
            
            # Create format selection options
            video_formats = [f for f in info['formats'] if f['vcodec'] != 'none']
            audio_formats = [f for f in info['formats'] if f['vcodec'] == 'none' and f['acodec'] != 'none']

            # Format selection
            format_type = st.radio("Select format type:", ["Video", "Audio only"])
            
            if format_type == "Video":
                format_options = {f['description']: f['format_id'] for f in video_formats}
            else:
                format_options = {f['description']: f['format_id'] for f in audio_formats}

            selected_format_desc = st.selectbox(
                "Select quality:",
                options=list(format_options.keys())
            )
            
            selected_format_id = format_options[selected_format_desc]

            # Download button and directory selection
            save_dir = st.text_input("Save directory (leave empty for current directory)", "")
            if not save_dir:
                save_dir = os.getcwd()

            if st.button("⬇️ Download Now", type="primary"):
                try:
                    st.session_state.progress_bar = st.progress(0)
                    with st.spinner("Downloading..."):
                        success = download_video(
                            video_url, 
                            save_dir, 
                            selected_format_id,
                            is_audio=(format_type == "Audio only")
                        )
                        
                    if success:
                        st.success("✅ Successfully downloaded!")
                    else:
                        st.error("❌ Download failed. Please try again.")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.info("💡 Tips:\n"
                           "- Make sure the video exists and is not private\n"
                           "- Check your internet connection\n"
                           "- Try refreshing the page")
                    
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.info("💡 Tips:\n"
                   "- Make sure the video exists and is not private\n"
                   "- Check your internet connection\n"
                   "- Try refreshing the page")
            
    st.markdown("---")
    st.markdown("### 📝 Instructions")
    st.markdown("""
    1. Paste a YouTube video URL in the input field above
    2. Select your preferred download type (Video or Audio)
    3. Choose the quality you want
    4. Click the Download button
    5. Find your downloaded file in the 'downloads' folder
    """)

if __name__ == "__main__":
    main()