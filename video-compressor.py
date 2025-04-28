import subprocess
import sys
import os

def compress_video(input_path, output_path, target_size_mb):
    """
    Compress a video file to a target size while maintaining reasonable quality.
    
    Args:
        input_path (str): Path to the input video file
        output_path (str): Path where the compressed video will be saved
        target_size_mb (float): Target size in megabytes (MB)
    
    Returns:
        bool: True if compression was successful, False otherwise
    """
    # Check if input file exists
    if not os.path.isfile(input_path):
        print(f"Error: Input file '{input_path}' does not exist.")
        return False
        
    # Calculate the target size in bits
    target_size_bits = target_size_mb * 8 * 1024 * 1024  # MB to bits

    # Get video duration using ffprobe
    print(f"Analyzing video: {input_path}")
    probe = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_path
        ],
        capture_output=True,
        text=True
    )
    if probe.returncode != 0:
        print("Error: Failed to probe video duration. Make sure ffprobe is installed.")
        return False
        
    duration = float(probe.stdout.strip())
    
    # Format duration for display
    mins = int(duration / 60)
    secs = int(duration % 60)
    print(f"Video duration: {mins} minutes {secs} seconds")

    # Target total bitrate (video + audio)
    total_bitrate = target_size_bits / duration  # bits per second

    # Reserve a good bitrate for audio to keep it high quality
    audio_bitrate = 128 * 1024  # 128 kbps

    # Calculate video bitrate
    video_bitrate = total_bitrate - audio_bitrate

    if video_bitrate <= 0:
        print("Error: Target size too small for this video. Try a higher target size or a shorter video.")
        return False

    # Calculate estimated compression ratio
    print(f"Original file size: {os.path.getsize(input_path) / (1024 * 1024):.2f} MB")
    print(f"Target file size: {target_size_mb} MB")
    print(f"Compression settings:")
    print(f"  - Video bitrate: {video_bitrate/1000:.2f} kbps")
    print(f"  - Audio bitrate: {audio_bitrate/1000} kbps")
    print(f"Compressing video. This may take a while...")

    # Run ffmpeg to compress
    try:
        result = subprocess.run([
            "ffmpeg", "-i", input_path,
            "-c:v", "libx264", "-b:v", f"{int(video_bitrate/1000)}k",
            "-c:a", "aac", "-b:a", f"{int(audio_bitrate/1000)}k",
            "-movflags", "+faststart",
            "-y",  # Overwrite output file if it exists
            output_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error during compression: {result.stderr}")
            return False
            
        # Verify the output file was created
        if not os.path.isfile(output_path):
            print("Error: Output file was not created.")
            return False
            
        actual_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"Compression complete!")
        print(f"Actual output size: {actual_size:.2f} MB")
        return True
            
    except Exception as e:
        print(f"Error during compression: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: python {sys.argv[0]} input_video output_video target_size_mb")
        print("Example: python video-compressor.py input.mp4 output.mp4 100")
        sys.exit(1)

    input_video = sys.argv[1]
    output_video = sys.argv[2]
    
    try:
        target_size_mb = float(sys.argv[3])
        if target_size_mb <= 0:
            print("Error: Target size must be a positive number.")
            sys.exit(1)
    except ValueError:
        print("Error: Target size must be a valid number.")
        sys.exit(1)

    success = compress_video(input_video, output_video, target_size_mb)
    if not success:
        sys.exit(1)