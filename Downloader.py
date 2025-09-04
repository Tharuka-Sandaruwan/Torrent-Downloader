#!/usr/bin/env python3
import libtorrent as lt
import time
import sys
import os
import re
import datetime
import shutil

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

def get_available_disk_space(path):
    """Returns available disk space in bytes for the given path."""
    try:
        total, used, free = shutil.disk_usage(path)
        return free
    except Exception as e:
        print(f"Error checking disk space: {e}")
        return 0

def check_disk_space(required_bytes, save_path):
    """Checks if there's enough disk space available."""
    available_space = get_available_disk_space(save_path)
    if available_space < required_bytes:
        return False, available_space
    return True, available_space

def verify_downloaded_files(handle, save_path, desired_files):
    """
    Verifies the integrity of downloaded files using torrent piece hashes.
    Returns a dictionary with verification results.
    """
    print("\n🔍 Starting file verification...")
    
    # Force a hash check
    handle.force_recheck()
    
    # Wait for the recheck to complete
    print("Performing hash verification...")
    start_verify_time = time.time()
    
    while True:
        s = handle.status()
        if s.state == lt.torrent_status.checking_files:
            progress = s.progress * 100
            print(f"\rVerifying integrity... {progress:.1f}%", end='')
        elif s.state == lt.torrent_status.downloading or s.state == lt.torrent_status.finished or s.state == lt.torrent_status.seeding:
            break
        time.sleep(0.5)
    
    verify_time = time.time() - start_verify_time
    print(f"\n✅ Verification completed in {verify_time:.1f} seconds")
    
    # Get piece information
    ti = handle.get_torrent_info()
    piece_size = ti.piece_length()
    num_pieces = ti.num_pieces()
    
    # Check which pieces are complete
    pieces = handle.status().pieces
    total_pieces_needed = 0
    verified_pieces = 0
    
    # Map files to pieces to determine which pieces belong to our selected files
    file_pieces = {}
    for file_index, file_entry in enumerate(ti.files()):
        if file_entry.path in desired_files:
            file_offset = file_entry.offset
            file_size = file_entry.size
            
            start_piece = file_offset // piece_size
            end_piece = (file_offset + file_size - 1) // piece_size
            
            file_pieces[file_entry.path] = {
                'start_piece': start_piece,
                'end_piece': end_piece,
                'pieces_needed': end_piece - start_piece + 1,
                'size': file_size
            }
    
    verification_results = {
        'overall_status': True,
        'files': {},
        'summary': {
            'total_files': len(desired_files),
            'verified_files': 0,
            'corrupted_files': 0,
            'total_pieces_checked': 0,
            'corrupted_pieces': 0
        }
    }
    
    print("\n📋 File-by-file verification results:")
    
    for file_path, piece_info in file_pieces.items():
        file_verified = True
        corrupted_pieces_in_file = 0
        
        for piece_idx in range(piece_info['start_piece'], piece_info['end_piece'] + 1):
            verification_results['summary']['total_pieces_checked'] += 1
            if piece_idx < len(pieces) and not pieces[piece_idx]:
                file_verified = False
                corrupted_pieces_in_file += 1
                verification_results['summary']['corrupted_pieces'] += 1
        
        verification_results['files'][file_path] = {
            'verified': file_verified,
            'pieces_needed': piece_info['pieces_needed'],
            'corrupted_pieces': corrupted_pieces_in_file,
            'size': piece_info['size']
        }
        
        # Display result
        status_icon = "✅" if file_verified else "❌"
        size_str = format_size(piece_info['size'])
        
        if file_verified:
            print(f"  {status_icon} {file_path} ({size_str}) - INTACT")
            verification_results['summary']['verified_files'] += 1
        else:
            print(f"  {status_icon} {file_path} ({size_str}) - CORRUPTED ({corrupted_pieces_in_file} bad pieces)")
            verification_results['summary']['corrupted_files'] += 1
            verification_results['overall_status'] = False
    
    return verification_results

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
    total_selected_size = 0
    print("\nSetting file priorities...")
    for file_index, file_entry in enumerate(files):
        if file_entry.path in desired_files:
            priorities.append(1)  # Normal priority
            total_selected_size += file_entry.size
            print(f"  [KEEP] {file_entry.path}")
        else:
            priorities.append(0)  # Do not download
            print(f"  [SKIP] {file_entry.path}")

    # Check disk space before starting download
    print(f"\nChecking disk space...")
    print(f"Selected files total size: {format_size(total_selected_size)}")
    
    # Add 10% buffer for safety
    required_space = int(total_selected_size * 1.1)
    has_space, available_space = check_disk_space(required_space, save_path)
    
    print(f"Available disk space: {format_size(available_space)}")
    print(f"Required space (with 10% buffer): {format_size(required_space)}")
    
    if not has_space:
        print(f"\n❌ ERROR: Not enough disk space!")
        print(f"   Need: {format_size(required_space)}")
        print(f"   Available: {format_size(available_space)}")
        print(f"   Shortage: {format_size(required_space - available_space)}")
        print("   Please free up some disk space and try again.")
        return
    
    print("✅ Sufficient disk space available.")

    handle.prioritize_files(priorities)
    print("Priorities set. Starting download...")
    handle.resume()

    # --- Phase 4: Download Loop ---
    start_time = time.time()
    previous_progress = 0
    stalled_count = 0
    
    print("\nStarting download loop...")
    
    # Improved completion detection
    while True:
        s = handle.status()
        state_str = [
            'queued', 'checking', 'downloading metadata',
            'downloading', 'finished', 'seeding', 'allocating'
        ]
        
        # --- FIXED PROGRESS CALCULATION ---
        total_wanted = s.total_wanted
        total_wanted_done = s.total_wanted_done
        progress = (total_wanted_done / total_wanted) * 100 if total_wanted > 0 else 0
        
        download_speed = s.download_rate / 1000000
        upload_speed = s.upload_rate / 1000000
        peers = s.num_peers
        
        print(
            f"\r{torrent_name[:40]:<40} "
            f"[{'#' * int(progress / 5):<20}] {progress:.2f}% "
            f"| ↓ {download_speed:.2f} MB/s "
            f"| ↑ {upload_speed:.2f} MB/s "
            f"| Peers: {peers} "
            f"| State: {state_str[s.state]}",
            end=''
        )
        
        # Check if download is complete
        if progress >= 99.9 or s.is_seeding or s.state == lt.torrent_status.finished:
            print(f"\n✅ Download complete! Progress: {progress:.2f}%")
            break
        
        # Check if download is stalled (same progress for too long)
        if abs(progress - previous_progress) < 0.01:  # Less than 0.01% progress
            stalled_count += 1
            if stalled_count > 30:  # 30 iterations * 2 seconds = 1 minute stalled
                print(f"\n⚠️  Download appears stalled at {progress:.2f}%. Checking if complete...")
                if total_wanted_done >= total_wanted * 0.999:  # 99.9% threshold
                    print("✅ Download is actually complete (minor rounding difference).")
                    break
                else:
                    print("Download is genuinely stalled. Continuing to wait...")
                    stalled_count = 0  # Reset counter
        else:
            stalled_count = 0  # Reset if progress is being made
            
        previous_progress = progress
        time.sleep(2)
    
    end_time = time.time()
    final_status = handle.status()
    final_progress = (final_status.total_wanted_done / final_status.total_wanted) * 100 if final_status.total_wanted > 0 else 0
    
    print(f"\n\n🎉 Download of selected files from '{torrent_name}' completed!")
    print(f"Final progress: {final_progress:.2f}%")
    
    # --- Phase 5: File Verification ---
    verification_results = verify_downloaded_files(handle, save_path, desired_files)
    
    # --- Phase 6: Display Summary ---
    total_downloaded_bytes = handle.status().total_wanted_done
    time_taken = end_time - start_time
    
    print("\n--- DOWNLOAD SUMMARY ---")
    print(f"Torrent: {torrent_name}")
    print(f"Final Status: {'✅ ALL FILES VERIFIED' if verification_results['overall_status'] else '❌ SOME FILES CORRUPTED'}")
    
    print("\nDownloaded Files:")
    for file_path in sorted(list(desired_files)):
        file_result = verification_results['files'].get(file_path, {})
        status = "✅ Verified" if file_result.get('verified', False) else "❌ Corrupted"
        size_str = format_size(file_result.get('size', 0))
        print(f"  {status} - {file_path} ({size_str})")
    
    # Verification summary
    vs = verification_results['summary']
    print(f"\nVerification Summary:")
    print(f"  Files verified: {vs['verified_files']}/{vs['total_files']}")
    print(f"  Pieces checked: {vs['total_pieces_checked']}")
    if vs['corrupted_pieces'] > 0:
        print(f"  ⚠️  Corrupted pieces found: {vs['corrupted_pieces']}")
        print(f"  📝 Recommendation: Re-download corrupted files")
    
    print(f"\nTotal Downloaded: {format_size(total_downloaded_bytes)}")
    print(f"Time Taken: {datetime.timedelta(seconds=int(time_taken))}")
    if time_taken > 0:
        avg_speed = total_downloaded_bytes / time_taken / 1024 / 1024
        print(f"Average Speed: {avg_speed:.2f} MB/s")
    print("------------------------\n")

    # --- Clean Up ---
    print("\n🧹 Cleaning up...")
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
