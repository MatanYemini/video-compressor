import subprocess
import sys
import os
import argparse

# Flask imports (only loaded when UI is used)
flask_available = False
try:
    from flask import Flask, render_template_string, request, jsonify
    flask_available = True
except ImportError:
    pass

def extract_audio(input_path, output_path, audio_bitrate=192):
    """
    Extract audio from a video file.
    
    Args:
        input_path (str): Path to the input video file
        output_path (str): Path where the extracted audio will be saved
        audio_bitrate (int): Audio bitrate in kbps
    
    Returns:
        bool: True if extraction was successful, False otherwise
    """
    # Check if input file exists
    if not os.path.isfile(input_path):
        print(f"Error: Input file '{input_path}' does not exist.")
        return False
    
    # If output path doesn't have an extension, add .mp3
    if not os.path.splitext(output_path)[1]:
        output_path = f"{output_path}.mp3"
    
    print(f"Extracting audio from {input_path} to {output_path}")
    print(f"Audio bitrate: {audio_bitrate} kbps")
    
    try:
        result = subprocess.run([
            "ffmpeg", "-i", input_path,
            "-vn",  # No video
            "-c:a", "libmp3lame",  # Use MP3 codec
            "-b:a", f"{audio_bitrate}k",
            "-y",  # Overwrite output file if it exists
            output_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error during audio extraction: {result.stderr}")
            return False
            
        # Verify the output file was created
        if not os.path.isfile(output_path):
            print("Error: Output file was not created.")
            return False
            
        actual_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"Audio extraction complete!")
        print(f"Output audio size: {actual_size:.2f} MB")
        return True
            
    except Exception as e:
        print(f"Error during audio extraction: {str(e)}")
        return False

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

def main():
    parser = argparse.ArgumentParser(description="Compress video or extract audio from a video file")
    parser.add_argument("input_video", help="Path to the input video file")
    parser.add_argument("output_path", help="Path for the output file")
    
    # Create a mutually exclusive group for compression vs audio extraction
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-s", "--size", type=float, help="Target size in megabytes (for video compression)")
    group.add_argument("-a", "--audio-only", action="store_true", help="Extract audio only (no video)")
    
    # Additional audio options
    parser.add_argument("--audio-bitrate", type=int, default=192, help="Audio bitrate in kbps (default: 192)")
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.isfile(args.input_video):
        print(f"Error: Input file '{args.input_video}' does not exist.")
        sys.exit(1)
    
    if args.audio_only:
        success = extract_audio(args.input_video, args.output_path, args.audio_bitrate)
    else:
        if args.size <= 0:
            print("Error: Target size must be a positive number.")
            sys.exit(1)
        success = compress_video(args.input_video, args.output_path, args.size)
    
    if not success:
        sys.exit(1)

# HTML template for the web UI
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video to MP3 Converter</title>
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a2e;
            color: #eee;
            min-height: 100vh;
        }
        h1 {
            color: #00d9ff;
            text-align: center;
            margin-bottom: 30px;
        }
        .container {
            background: #16213e;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }
        .section {
            margin-bottom: 25px;
        }
        .section-title {
            font-size: 1.1em;
            font-weight: 600;
            color: #00d9ff;
            margin-bottom: 12px;
        }
        .file-browser {
            background: #0f0f23;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 15px;
            max-height: 300px;
            overflow-y: auto;
        }
        .path-bar {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 15px;
            padding: 10px;
            background: #0f0f23;
            border-radius: 6px;
        }
        .path-bar input {
            flex: 1;
            padding: 8px 12px;
            border: 1px solid #333;
            border-radius: 4px;
            background: #1a1a2e;
            color: #eee;
            font-size: 14px;
        }
        .path-bar button {
            padding: 8px 16px;
            background: #00d9ff;
            border: none;
            border-radius: 4px;
            color: #1a1a2e;
            cursor: pointer;
            font-weight: 600;
        }
        .path-bar button:hover {
            background: #00b8d9;
        }
        .file-item {
            display: flex;
            align-items: center;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .file-item:hover {
            background: #1a1a2e;
        }
        .file-item.directory {
            color: #ffd700;
        }
        .file-item.selected {
            background: #0a4d68;
        }
        .file-item input[type="checkbox"] {
            margin-right: 10px;
        }
        .file-icon {
            margin-right: 10px;
            font-size: 1.2em;
        }
        .selected-files {
            background: #0f0f23;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 15px;
            min-height: 80px;
        }
        .selected-file {
            display: inline-flex;
            align-items: center;
            background: #0a4d68;
            padding: 6px 12px;
            border-radius: 20px;
            margin: 4px;
            font-size: 0.9em;
        }
        .selected-file .remove {
            margin-left: 8px;
            cursor: pointer;
            color: #ff6b6b;
            font-weight: bold;
        }
        .output-info {
            background: #0f0f23;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 15px;
            color: #888;
        }
        .output-info strong {
            color: #00d9ff;
        }
        .convert-btn {
            width: 100%;
            padding: 15px;
            font-size: 1.1em;
            font-weight: 600;
            background: linear-gradient(135deg, #00d9ff, #0077b6);
            border: none;
            border-radius: 8px;
            color: white;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .convert-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0, 217, 255, 0.4);
        }
        .convert-btn:disabled {
            background: #444;
            cursor: not-allowed;
        }
        .progress-container {
            margin-top: 20px;
            display: none;
        }
        .progress-container.active {
            display: block;
        }
        .progress-item {
            background: #0f0f23;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 10px;
        }
        .progress-item .filename {
            font-weight: 600;
            margin-bottom: 8px;
        }
        .progress-bar {
            height: 6px;
            background: #333;
            border-radius: 3px;
            overflow: hidden;
        }
        .progress-bar .fill {
            height: 100%;
            background: #00d9ff;
            transition: width 0.3s;
        }
        .progress-item.success .fill {
            background: #00ff88;
        }
        .progress-item.error .fill {
            background: #ff6b6b;
        }
        .status-text {
            font-size: 0.85em;
            color: #888;
            margin-top: 6px;
        }
        .results {
            margin-top: 20px;
            padding: 15px;
            background: #0f0f23;
            border-radius: 8px;
            display: none;
        }
        .results.active {
            display: block;
        }
        .results h3 {
            color: #00ff88;
            margin-top: 0;
        }
        .empty-state {
            text-align: center;
            color: #666;
            padding: 20px;
        }
        .browse-system-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 12px 20px;
            background: linear-gradient(135deg, #6c5ce7, #a855f7);
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            margin-bottom: 15px;
        }
        .browse-system-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(168, 85, 247, 0.4);
        }
        .browse-divider {
            display: flex;
            align-items: center;
            margin: 20px 0;
            color: #666;
        }
        .browse-divider::before,
        .browse-divider::after {
            content: '';
            flex: 1;
            border-bottom: 1px solid #333;
        }
        .browse-divider span {
            padding: 0 15px;
            font-size: 0.9em;
        }
        #systemFileInput {
            display: none;
        }
    </style>
</head>
<body>
    <h1>Video to MP3 Converter</h1>

    <div class="container">
        <div class="section">
            <div class="section-title">Select Files</div>
            <input type="file" id="systemFileInput" accept=".mov,.MOV" multiple />
            <button class="browse-system-btn" onclick="document.getElementById('systemFileInput').click()">
                <span>📂</span> Browse with System Picker
            </button>
            <div class="browse-divider"><span>or browse folders below</span></div>
            <div class="path-bar">
                <input type="text" id="currentPath" value="{{ default_path }}" />
                <button onclick="navigateTo()">Go</button>
                <button onclick="navigateUp()">Up</button>
            </div>
            <div class="file-browser" id="fileBrowser">
                <div class="empty-state">Loading...</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Selected Files (<span id="selectedCount">0</span>)</div>
            <div class="selected-files" id="selectedFiles">
                <div class="empty-state">No files selected. Browse and select .mov files above.</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Output Location</div>
            <div class="output-info">
                <strong>Output folder:</strong> {{ output_path }}<br>
                <small>MP3 files will be saved with the same name as the source video.</small>
            </div>
        </div>

        <button class="convert-btn" id="convertBtn" onclick="startConversion()" disabled>
            Convert Selected Files to MP3
        </button>

        <div class="progress-container" id="progressContainer"></div>

        <div class="results" id="results">
            <h3>Conversion Complete!</h3>
            <div id="resultsContent"></div>
        </div>
    </div>

    <script>
        let selectedFiles = new Set();
        const outputPath = '{{ output_path }}';

        async function loadDirectory(path) {
            try {
                const response = await fetch('/api/browse?path=' + encodeURIComponent(path));
                const data = await response.json();

                if (data.error) {
                    alert('Error: ' + data.error);
                    return;
                }

                document.getElementById('currentPath').value = data.current_path;
                renderFiles(data.items);
            } catch (e) {
                alert('Failed to load directory: ' + e.message);
            }
        }

        function renderFiles(items) {
            const browser = document.getElementById('fileBrowser');

            if (items.length === 0) {
                browser.innerHTML = '<div class="empty-state">No .mov files or folders found</div>';
                return;
            }

            browser.innerHTML = items.map(item => {
                if (item.type === 'directory') {
                    return `
                        <div class="file-item directory" ondblclick="navigateToDir('${escapeHtml(item.path)}')">
                            <span class="file-icon">📁</span>
                            <span>${escapeHtml(item.name)}</span>
                        </div>
                    `;
                } else {
                    const isSelected = selectedFiles.has(item.path);
                    return `
                        <div class="file-item ${isSelected ? 'selected' : ''}" onclick="toggleFile('${escapeHtml(item.path)}', '${escapeHtml(item.name)}')">
                            <input type="checkbox" ${isSelected ? 'checked' : ''} onclick="event.stopPropagation(); toggleFile('${escapeHtml(item.path)}', '${escapeHtml(item.name)}')">
                            <span class="file-icon">🎬</span>
                            <span>${escapeHtml(item.name)}</span>
                        </div>
                    `;
                }
            }).join('');
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML.replace(/'/g, "\\'");
        }

        function toggleFile(path, name) {
            if (selectedFiles.has(path)) {
                selectedFiles.delete(path);
            } else {
                selectedFiles.add(path);
            }
            updateSelectedDisplay();
            loadDirectory(document.getElementById('currentPath').value);
        }

        function removeFile(path) {
            selectedFiles.delete(path);
            updateSelectedDisplay();
            loadDirectory(document.getElementById('currentPath').value);
        }

        function updateSelectedDisplay() {
            const container = document.getElementById('selectedFiles');
            const count = document.getElementById('selectedCount');
            const btn = document.getElementById('convertBtn');

            count.textContent = selectedFiles.size;
            btn.disabled = selectedFiles.size === 0;

            if (selectedFiles.size === 0) {
                container.innerHTML = '<div class="empty-state">No files selected. Browse and select .mov files above.</div>';
                return;
            }

            container.innerHTML = Array.from(selectedFiles).map(path => {
                const name = path.split('/').pop();
                return `
                    <span class="selected-file">
                        ${escapeHtml(name)}
                        <span class="remove" onclick="removeFile('${escapeHtml(path)}')">&times;</span>
                    </span>
                `;
            }).join('');
        }

        function navigateTo() {
            const path = document.getElementById('currentPath').value;
            loadDirectory(path);
        }

        function navigateUp() {
            const path = document.getElementById('currentPath').value;
            const parent = path.split('/').slice(0, -1).join('/') || '/';
            loadDirectory(parent);
        }

        function navigateToDir(path) {
            loadDirectory(path);
        }

        async function startConversion() {
            if (selectedFiles.size === 0) return;

            const btn = document.getElementById('convertBtn');
            const progressContainer = document.getElementById('progressContainer');
            const results = document.getElementById('results');

            btn.disabled = true;
            btn.textContent = 'Converting...';
            progressContainer.classList.add('active');
            results.classList.remove('active');

            // Create progress items
            progressContainer.innerHTML = Array.from(selectedFiles).map(path => {
                const name = path.split('/').pop();
                return `
                    <div class="progress-item" id="progress-${btoa(path)}">
                        <div class="filename">${escapeHtml(name)}</div>
                        <div class="progress-bar"><div class="fill" style="width: 0%"></div></div>
                        <div class="status-text">Waiting...</div>
                    </div>
                `;
            }).join('');

            const completedFiles = [];
            const failedFiles = [];

            for (const filePath of selectedFiles) {
                const progressId = 'progress-' + btoa(filePath);
                const progressItem = document.getElementById(progressId);
                const fill = progressItem.querySelector('.fill');
                const status = progressItem.querySelector('.status-text');

                fill.style.width = '50%';
                status.textContent = 'Converting...';

                try {
                    const response = await fetch('/api/convert', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ input_path: filePath })
                    });

                    const data = await response.json();

                    if (data.success) {
                        fill.style.width = '100%';
                        progressItem.classList.add('success');
                        status.textContent = 'Complete! Saved to: ' + data.output_path;
                        completedFiles.push({ input: filePath, output: data.output_path });
                    } else {
                        fill.style.width = '100%';
                        progressItem.classList.add('error');
                        status.textContent = 'Error: ' + data.error;
                        failedFiles.push({ input: filePath, error: data.error });
                    }
                } catch (e) {
                    fill.style.width = '100%';
                    progressItem.classList.add('error');
                    status.textContent = 'Error: ' + e.message;
                    failedFiles.push({ input: filePath, error: e.message });
                }
            }

            // Show results
            results.classList.add('active');
            let resultsHtml = '';
            if (completedFiles.length > 0) {
                resultsHtml += `<p style="color: #00ff88;">✓ ${completedFiles.length} file(s) converted successfully</p>`;
            }
            if (failedFiles.length > 0) {
                resultsHtml += `<p style="color: #ff6b6b;">✗ ${failedFiles.length} file(s) failed</p>`;
            }
            document.getElementById('resultsContent').innerHTML = resultsHtml;

            btn.disabled = false;
            btn.textContent = 'Convert Selected Files to MP3';

            // Clear selection
            selectedFiles.clear();
            updateSelectedDisplay();
            loadDirectory(document.getElementById('currentPath').value);
        }

        // Handle system file picker
        document.getElementById('systemFileInput').addEventListener('change', async function(e) {
            const files = e.target.files;
            if (files.length === 0) return;

            // Upload files to server and get their paths
            for (const file of files) {
                const formData = new FormData();
                formData.append('file', file);

                try {
                    const response = await fetch('/api/upload', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await response.json();

                    if (data.success) {
                        selectedFiles.add(data.path);
                    } else {
                        alert('Failed to add file: ' + data.error);
                    }
                } catch (err) {
                    alert('Failed to upload file: ' + err.message);
                }
            }

            updateSelectedDisplay();
            // Clear the input so the same file can be selected again
            e.target.value = '';
        });

        // Initial load
        loadDirectory('{{ default_path }}');
    </script>
</body>
</html>
'''

def run_ui(port=8081, browse_path=None, output_path=None):
    """Run the web UI for audio extraction."""
    if not flask_available:
        print("Error: Flask is not installed. Install it with: pip install flask")
        sys.exit(1)

    # Default paths
    if browse_path is None:
        browse_path = "/Users/matan/Movies"
    if output_path is None:
        output_path = "/Users/matan/Movies"

    # Ensure output directory exists
    os.makedirs(output_path, exist_ok=True)

    app = Flask(__name__)

    @app.route('/')
    def index():
        return render_template_string(HTML_TEMPLATE,
                                      default_path=browse_path,
                                      output_path=output_path)

    @app.route('/api/browse')
    def browse():
        path = request.args.get('path', browse_path)
        path = os.path.expanduser(path)

        if not os.path.isdir(path):
            return jsonify({'error': 'Directory not found', 'current_path': path, 'items': []})

        items = []
        try:
            for entry in sorted(os.listdir(path)):
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    items.append({
                        'name': entry,
                        'path': full_path,
                        'type': 'directory'
                    })
                elif entry.lower().endswith('.mov'):
                    items.append({
                        'name': entry,
                        'path': full_path,
                        'type': 'file'
                    })
        except PermissionError:
            return jsonify({'error': 'Permission denied', 'current_path': path, 'items': []})

        # Sort: directories first, then files
        items.sort(key=lambda x: (x['type'] != 'directory', x['name'].lower()))

        return jsonify({
            'current_path': path,
            'items': items
        })

    @app.route('/api/convert', methods=['POST'])
    def convert():
        data = request.json
        input_path = data.get('input_path')

        if not input_path:
            return jsonify({'success': False, 'error': 'No input path provided'})

        if not os.path.isfile(input_path):
            return jsonify({'success': False, 'error': 'File not found'})

        # Generate output filename
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_file = os.path.join(output_path, f"{base_name}.mp3")

        # Run extraction
        success = extract_audio(input_path, output_file)

        if success:
            return jsonify({
                'success': True,
                'output_path': output_file
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Conversion failed. Check console for details.'
            })

    @app.route('/api/upload', methods=['POST'])
    def upload():
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})

        # Save uploaded file to a temp location in the output directory
        filename = file.filename
        # Sanitize filename
        safe_filename = "".join(c for c in filename if c.isalnum() or c in '._- ')
        upload_dir = os.path.join(output_path, '.uploads')
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, safe_filename)

        try:
            file.save(file_path)
            return jsonify({
                'success': True,
                'path': file_path,
                'filename': safe_filename
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })

    print("\n" + "="*50)
    print("Video to MP3 Converter UI")
    print("="*50)
    print(f"Browse folder: {browse_path}")
    print(f"Output folder: {output_path}")
    print("="*50)
    print(f"\nStarting server at http://localhost:{port}")
    print("Press Ctrl+C to stop\n")

    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # If no arguments provided, show help
        print("Video Compressor Tool\n")
        print("For video compression:")
        print("  python video-compressor.py -s SIZE input.mp4 output.mp4")
        print("  Example: python video-compressor.py -s 99 input.mp4 output.mp4")
        print("\nFor audio extraction:")
        print("  python video-compressor.py -a input.mp4 output.mp3")
        print("  Example: python video-compressor.py -a input.mp4 output.mp3")
        print("\nFor web UI (batch audio extraction):")
        print("  python video-compressor.py --ui")
        print("  python video-compressor.py --ui --port 8081")
        print("\nFor more options, use: python video-compressor.py -h")
        sys.exit(0)

    # Check for UI mode
    if '--ui' in sys.argv:
        port = 8081
        if '--port' in sys.argv:
            port_idx = sys.argv.index('--port')
            if port_idx + 1 < len(sys.argv):
                try:
                    port = int(sys.argv[port_idx + 1])
                except ValueError:
                    print("Error: Invalid port number")
                    sys.exit(1)
        run_ui(port=port)
    else:
        main()