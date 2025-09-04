# 🌊 Torrent Downloader

A smart, resource-efficient torrent downloader optimized for both powerful servers and small VPS instances. Features intelligent file selection, disk space checking, integrity verification, and automatic optimization based on your system resources.

## ✨ Features

- 🎯 **Selective Download**: Choose specific files from torrents
- 💾 **Smart Disk Space Check**: Prevents downloads if insufficient storage
- 🔍 **Integrity Verification**: Automatic file corruption detection
- ⚡ **Auto-Optimization**: Adapts to your server's CPU and RAM
- 🖥️ **Small Server Ready**: Works great on VPS with limited resources
- 🛑 **Proper Completion**: Stops downloading exactly when files are complete
- 📊 **Detailed Progress**: Real-time download statistics and progress bars

## 🔧 Installation

### Prerequisites

**Python 3.6 or higher** is required.

### Install Dependencies

Choose one of these installation methods:

#### Option 1: Full Installation (Recommended)
```bash
pip install libtorrent-python psutil
```

#### Option 2: Minimal Installation
```bash
pip install libtorrent-python
```
> **Note**: Without `psutil`, the auto-optimization feature won't work, but the downloader will still function normally.

### Download the Script

1. Download `Downloader.py` to your desired folder
2. Make it executable (Linux/Mac):
   ```bash
   chmod +x Downloader.py
   ```

## 🚀 Quick Start

### Basic Usage

```bash
python Downloader.py "magnet:?xt=urn:btih:YOUR_MAGNET_LINK_HERE"
```

### Step-by-Step Process

1. **Run the command** with your magnet link
2. **Wait for metadata** to be downloaded
3. **Edit the file list** that gets created
4. **Press Enter** to start downloading
5. **Wait for completion** and verification

## 📖 Detailed Usage Guide

### Step 1: Get a Magnet Link

A magnet link looks like this:
```
magnet:?xt=urn:btih:1234567890abcdef1234567890abcdef12345678&dn=Example+File&tr=udp://tracker.example.com:1337
```

You can find magnet links on torrent sites, forums, or file sharing platforms.

### Step 2: Start the Download

Open your terminal/command prompt and run:

```bash
# Windows
python Downloader.py "magnet:?xt=urn:btih:YOUR_MAGNET_LINK"

# Linux/Mac
python3 Downloader.py "magnet:?xt=urn:btih:YOUR_MAGNET_LINK"
```

**Important**: Always put the magnet link in quotes!

### Step 3: File Selection

The downloader will:
1. Connect to peers and download metadata
2. Create a file called `[TorrentName]_files.txt`
3. Show you this message:

```
--- ACTION REQUIRED ---
1. Open the file: 'Movie_Collection_files.txt'
2. REMOVE the lines for any files you DO NOT want to download.
3. Save the file.
4. Press Enter here to continue the download...
```

### Step 4: Edit the File List

Open the created `.txt` file in any text editor. You'll see something like:

```
[  1.2 GB] Movie1.mkv
[ 45.2 KB] Movie1.srt
[800.0 MB] Movie2.mp4
[ 12.3 KB] Movie2.srt
[  2.1 GB] Movie3.avi
```

**To select files**: Keep the lines for files you want
**To skip files**: Delete the entire line for files you don't want

Example - if you only want Movie1:
```
[  1.2 GB] Movie1.mkv
[ 45.2 KB] Movie1.srt
```

Save the file and go back to the terminal.

### Step 5: Start Download

Press `Enter` in the terminal. The downloader will:

1. ✅ Check if you have enough disk space
2. 🚀 Start downloading selected files
3. 📊 Show real-time progress
4. 🔍 Verify file integrity when complete

## 📊 Understanding the Progress Display

During download, you'll see something like:

```
Movie Collection                     [########            ] 45.67% | ↓ 2.34 MB/s | ↑ 0.12 MB/s | Peers: 15 | State: downloading
```

- **Progress bar**: Visual representation of completion
- **Percentage**: Exact completion percentage
- **↓ Speed**: Download speed in MB/s
- **↑ Speed**: Upload speed in MB/s
- **Peers**: Number of connected peers
- **State**: Current download state

## ⚙️ Configuration

### Small Server Mode

The downloader automatically detects your system resources:

- **Auto-enabled if**: RAM < 2GB or CPU < 2 cores
- **Manual control**: Edit `SMALL_SERVER_MODE = True` in the script
- **Benefits**: Uses 75% less memory and CPU

### Download Location

By default, files download to a `downloads` folder. To change this:

1. Edit the script
2. Find: `SAVE_PATH = "downloads"`
3. Change to: `SAVE_PATH = "/your/preferred/path"`

## 🛠️ Troubleshooting

### Common Issues

**"Invalid magnet link provided"**
- Make sure the magnet link starts with `magnet:?xt=urn:btih:`
- Put the entire link in quotes
- Check for copy-paste errors

**"Not enough storage"**
- Free up disk space
- The downloader needs 10% extra space as a buffer
- Check the reported sizes in the error message

**Download stuck at 99%**
- This is normal - the downloader will detect completion automatically
- Wait a few more seconds, it should complete soon

**No peers found**
- The torrent might be dead (no seeders)
- Try a different torrent
- Check your internet connection

**ImportError: No module named 'libtorrent'**
- Install the required dependency: `pip install libtorrent-python`

### Getting Help

If you encounter other issues:
1. Check that Python 3.6+ is installed
2. Verify all dependencies are installed
3. Make sure the magnet link is valid
4. Try with a different, known-working torrent

## 📁 File Structure

After running the downloader, you'll see:

```
your-folder/
├── Downloader.py           # The main script
├── downloads/              # Downloaded files go here
│   ├── Movie1.mkv
│   └── Movie1.srt
└── TorrentName_files.txt   # Temporary file list (auto-deleted)
```

## 🔍 Verification Results

After download completion, you'll see verification results:

```
📋 File-by-file verification results:
  ✅ Movie1.mkv (1.2 GB) - INTACT
  ✅ Movie1.srt (45.2 KB) - INTACT

--- DOWNLOAD SUMMARY ---
Final Status: ✅ ALL FILES VERIFIED
Files verified: 2/2
Total Downloaded: 1.2 GB
Time Taken: 0:15:30
Average Speed: 1.34 MB/s
```

- ✅ **INTACT**: File is perfect, no corruption
- ❌ **CORRUPTED**: File has issues, needs re-download

## 🖥️ System Requirements

### Minimum Requirements
- **OS**: Windows, Linux, macOS
- **Python**: 3.6 or higher
- **RAM**: 256MB (with small server optimizations)
- **CPU**: Any (single core supported)
- **Disk**: Space for downloads + 10% buffer

### Recommended Requirements
- **RAM**: 1GB or more
- **CPU**: Dual-core or better
- **Network**: Stable internet connection

## 🚀 Advanced Usage

### Running on a VPS/Server

```bash
# Run in background (Linux/Mac)
nohup python3 Downloader.py "magnet_link_here" &

# Check if still running
ps aux | grep Downloader.py
```

### Automating File Selection

For automated deployments, you can pre-create the file list:

1. Run the downloader once to generate the file list
2. Edit and save your preferred selection
3. Copy this file for future use with the same torrent

## 📝 Examples

### Example 1: Download a Single Movie
```bash
python Downloader.py "magnet:?xt=urn:btih:abcd1234..."
# Edit the file list to keep only the movie file
# Press Enter to start
```

### Example 2: Download Selected Episodes
```bash
python Downloader.py "magnet:?xt=urn:btih:efgh5678..."
# Keep only episodes 1, 5, and 10 from the file list
# Delete all other lines
# Press Enter to start
```

### Example 3: Download Everything
```bash
python Downloader.py "magnet:?xt=urn:btih:ijkl9012..."
# Don't edit the file list - keep all files
# Press Enter to download everything
```

## ⚠️ Important Notes

- **Legal Use Only**: Only download content you have the right to download
- **Disk Space**: Always ensure you have enough free space
- **Network**: Torrent downloading uses your internet bandwidth
- **Patience**: Large files take time - let the process complete
- **Verification**: Always check the verification results after download

## 🔄 Updates

To update the downloader:
1. Download the latest `Downloader.py`
2. Replace your old file
3. Keep your configuration changes if any

---

**Happy downloading! 🎉**

For issues or questions, check the troubleshooting section above or review the error messages - they usually provide clear guidance on what needs to be fixed.
