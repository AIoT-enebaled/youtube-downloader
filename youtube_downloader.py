import os
from pytube import YouTube
import moviepy.editor as mp
import streamlit as st

def download_video(url, save_dir, progress_callback):
    yt = YouTube(url, on_progress_callback=progress_callback)

    # Download the highest resolution video without audio
    video_stream = yt.streams.filter(adaptive=True, file_extension='mp4').order_by('resolution').desc().first()
    video_path = video_stream.download(output_path=save_dir, filename='temp_video')

    # Download the highest quality audio stream
    audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()
    audio_path = audio_stream.download(output_path=save_dir, filename='temp_audio')

    # Combine video and audio using moviepy
    video_clip = mp.VideoFileClip(video_path)
    audio_clip = mp.AudioFileClip(audio_path)
    final_clip = video_clip.set_audio(audio_clip)

    # Save the final video
    final_video_path = os.path.join(save_dir, 'final_video.mp4')
    final_clip.write_videofile(final_video_path, codec='libx264', audio_codec='aac')

    # Clean up temporary files
    os.remove(video_path)
    os.remove(audio_path)

    return final_video_path

def main():
    st.title("YouTube Video Downloader")

    st.sidebar.header("Enter the YouTube video URL and select save directory")

    video_url = st.sidebar.text_input("YouTube Video URL")

    save_dir = st.sidebar.text_input("Enter or select a directory path")

    if st.sidebar.button("Select Directory"):
        save_dir = st.sidebar.file_uploader("Select Save Directory", type='directory')
        if save_dir:
            save_dir = save_dir.name

    if st.sidebar.button("Download Video"):
        if not video_url:
            st.error("Please enter a YouTube video URL.")
        elif not save_dir:
            st.error("Please select or enter a directory to save the video.")
        else:
            st.session_state.progress_bar = st.progress(0)
            with st.spinner("Downloading and processing..."):
                try:
                    final_video_path = download_video(video_url, save_dir, None)
                    st.success(f"Video downloaded successfully! Saved to: {final_video_path}")
                    st.video(final_video_path)
                except Exception as e:
                    st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()