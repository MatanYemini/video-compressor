# Video Compressor

A simple Python script to compress videos to a specified target size while maintaining reasonable quality. It can also extract audio from video files.

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

## Usages

### Video Compression

To compress a video to a specific size:

```
python video-compressor.py -s TARGET_SIZE_MB INPUT_VIDEO OUTPUT_VIDEO
```

Example:

```
python video-compressor.py -s 99 input.mp4 output.mp4
```

This will compress `input.mp4` to approximately 99MB and save it as `output.mp4`.

### Audio Extraction

To extract only the audio from a video:

```
python video-compressor.py -a INPUT_VIDEO OUTPUT_AUDIO
```

Example:

```
python video-compressor.py -a input.mp4 output.mp3
```

This will extract the audio from `input.mp4` and save it as `output.mp3`.

### Additional Options

To customize audio bitrate when extracting audio:

```
python video-compressor.py -a --audio-bitrate 320 input.mp4 output.mp3
```

To get full help:

```
python video-compressor.py -h
```

## How it works

### Video Compression

The script:

1. Calculates the target bitrate based on the video duration and desired file size
2. Reserves 128 kbps for audio quality
3. Uses the remaining bitrate for video
4. Uses H.264 (libx264) for video compression and AAC for audio compression

### Audio Extraction

When extracting audio:

1. Strips out the video track
2. Uses MP3 encoding (libmp3lame)
3. Default audio bitrate is 192 kbps (customizable)

## Notes

- The actual file size may vary slightly from the target size
- Very low target sizes may result in poor video quality
- The compression process uses default preset settings for libx264
