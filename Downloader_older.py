#!/usr/bin/env python3
import libtorrent as lt
import time
import sys
import os
import re
import datetime

# --- Configuration ---
# Set the path where you want to save the downloaded files.
# This will create a "downloads" directory in the same folder where the script is run.
SAVE_PATH = "downloads"

def sanitize_filename(filename):
    """Removes invalid characters from a string to be used as a filename."""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def format_size(size_bytes):
    """Converts bytes to a human-readable string (B, KB, MB, GB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    size_kb = size_bytes / 1024
    if size_kb < 1024:
        return f"{size_kb:.2f} KB"
    size_mb = size_kb / 1024
    if size_mb < 1024:
        return f"{size_mb:.2f} MB"
    size_gb = size_mb / 1024
    return f"{size_gb:.2f} GB"

def download_torrent(magnet_link, save_path):
    """
    Downloads selected files from a torrent from a magnet link with settings optimized for low RAM.
    """
    # Get the absolute path for the save directory
    save_path = os.path.abspath(save_path)
    if not os.path.exists(save_path):
        try:
            os.makedirs(save_path)
            print(f"Created save directory: {save_path}")
        except OSError as e:
            print(f"Error creating directory {save_path}: {e}")
            return

    # --- Session Settings for Low Memory ---
    settings = {
        'user_agent': 'libtorrent/2.0.5',
        'listen_interfaces': '0.0.0.0:6881',
        'announce_to_all_trackers': True,
        'announce_to_all_tiers': True,
        'connections_limit': 200,
        'connection_speed': 50,
        'cache_size': 2048,
        'max_queued_disk_bytes': 1 * 1024 * 1024,
        'send_buffer_watermark': 512 * 1024,
        'recv_socket_buffer_size': 1 * 1024 * 1024,
        'send_socket_buffer_size': 1 * 1024 * 1024,
        'choking_algorithm': lt.choking_algorithm_t.fixed_slots_choker,
        'seed_choking_algorithm': lt.seed_choking_algorithm_t.round_robin,
        'upload_rate_limit': 0,
        'download_rate_limit': 0,
        'unchoke_slots_limit': 20,
        'enable_dht': True,
        'enable_lsd': True,
        'enable_natpmp': True,
        'enable_upnp': True,
    }

    ses = lt.session(settings)

    # --- Phase 1: Add Torrent in Paused State to Get Metadata ---
    params = lt.parse_magnet_uri(magnet_link)
    params.save_path = save_path
    # Add the torrent paused, so we can select files before downloading
    params.flags |= lt.torrent_flags.paused
    handle = ses.add_torrent(params)

    print("Downloading metadata...")
    while not handle.has_metadata():
        time.sleep(1)
    print("Metadata received.")

    # --- Phase 2: Generate File List for User Selection ---
    ti = handle.get_torrent_info()
    torrent_name = ti.name()
    files = ti.files()
    
    # Create a safe filename for the list of files
    file_list_path = f"{sanitize_filename(torrent_name)}_files.txt"

    print(f"\nCreating file list at: {file_list_path}")
    with open(file_list_path, "w", encoding='utf-8') as f:
        for file_index, file_entry in enumerate(files):
            # Format the size and write it alongside the file path
            size_str = format_size(file_entry.size)
            f.write(f"[{size_str:>10}] {file_entry.path}\n")

    print("\n--- ACTION REQUIRED ---")
    print(f"1. Open the file: '{file_list_path}'")
    print("2. REMOVE the lines for any files you DO NOT want to download.")
    print("3. Save the file.")
    input("4. Press Enter here to continue the download...")

    # --- Phase 3: Set File Priorities Based on User's Selection ---
    try:
        with open(file_list_path, "r", encoding='utf-8') as f:
            # Create a set of desired files by parsing the file paths from the edited list
            desired_files = set()
            for line in f:
                line = line.strip()
                if line and '] ' in line:
                    # Extract the part after '] ' which is the file path
                    path = line.split('] ', 1)[1]
                    desired_files.add(path)
    except FileNotFoundError:
        print(f"Error: Could not find '{file_list_path}'. Aborting.")
        return
        
    priorities = []
    print("\nSetting file priorities...")
    for file_index, file_entry in enumerate(files):
        if file_entry.path in desired_files:
            priorities.append(1)  # Normal priority
            print(f"  [KEEP] {file_entry.path}")
        else:
            priorities.append(0)  # Do not download
            print(f"  [SKIP] {file_entry.path}")

    handle.prioritize_files(priorities)
    print("Priorities set. Starting download...")
    handle.resume()

    # --- Phase 4: Download Loop ---
    start_time = time.time()
    # The loop condition checks if the state is 'seeding', which happens after all wanted files are downloaded.
    while not handle.status().is_seeding:
        s = handle.status()
        state_str = [
            'queued', 'checking', 'downloading metadata',
            'downloading', 'finished', 'seeding', 'allocating'
        ]
        
        # --- FIXED PROGRESS CALCULATION ---
        # We now calculate progress based on the total data we *want* to download,
        # not the total size of the entire torrent.
        total_wanted = s.total_wanted
        total_wanted_done = s.total_wanted_done
        progress = (total_wanted_done / total_wanted) * 100 if total_wanted > 0 else 0
        
        download_speed = s.download_rate / 1000000
        upload_speed = s.upload_rate / 1000000
        peers = s.num_peers
        
        print(
            f"\r{torrent_name[:40]:<40} "
            f"[{'#' * int(progress / 5):<20}] {progress:.2f}% "
            f"| ? {download_speed:.2f} MB/s "
            f"| ? {upload_speed:.2f} MB/s "
            f"| Peers: {peers} "
            f"| State: {state_str[s.state]}",
            end=''
        )
        time.sleep(2)
    
    end_time = time.time()
    print(f"\n\nDownload of selected files from '{torrent_name}' complete.")
    
    # --- Phase 5: Display Summary ---
    total_downloaded_bytes = handle.status().total_wanted_done
    time_taken = end_time - start_time
    
    print("\n--- DOWNLOAD SUMMARY ---")
    print(f"Torrent: {torrent_name}")
    print("\nDownloaded Files:")
    for file_path in sorted(list(desired_files)):
        print(f"  - {file_path}")
    
    print(f"\nTotal Bandwidth Used: {format_size(total_downloaded_bytes)}")
    print(f"Time Taken: {datetime.timedelta(seconds=int(time_taken))}")
    print("------------------------\n")

    # --- Clean Up ---
    print("Removing torrent to stop seeding.")
    ses.remove_torrent(handle)
    
    try:
        os.remove(file_list_path)
        print(f"Removed temporary file list: '{file_list_path}'")
    except OSError as e:
        print(f"Error removing file list: {e}")

    time.sleep(2)
    print("Session closed. Exiting.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python optimized_downloader.py \"<magnet_link>\"")
        sys.exit(1)

    magnet_link_arg = sys.argv[1]
    
    if not magnet_link_arg.startswith("magnet:?xt=urn:btih:"):
        print("Error: Invalid magnet link provided.")
        sys.exit(1)
        
    download_torrent(magnet_link_arg, SAVE_PATH)
