# Video Compressor

A simple Python script to compress videos to a specified target size while maintaining reasonable quality.

## Requirements

- Python 3.x
- ffmpeg and ffprobe (must be installed on your system and available in your PATH)

## Installation

1. Clone this repository:

```
git clone https://github.com/yourusername/video-compressor.git
cd video-compressor
```

2. Install dependencies:

```
make install
```

## Usage

```
python video-compressor.py input_video output_video target_size_mb
```

### Parameters:

- `input_video`: Path to the input video file
- `output_video`: Path where the compressed video will be saved
- `target_size_mb`: Target size in megabytes (MB)

### Example:

```
python video-compressor.py input.mp4 output.mp4 100
```

This will compress `input.mp4` to approximately 100MB and save it as `output.mp4`.

## How it works

The script:

1. Calculates the target bitrate based on the video duration and desired file size
2. Reserves 128 kbps for audio quality
3. Uses the remaining bitrate for video
4. Uses H.264 (libx264) for video compression and AAC for audio compression

## Notes

- The actual file size may vary slightly from the target size
- Very low target sizes may result in poor video quality
- The compression process uses default preset settings for libx264
