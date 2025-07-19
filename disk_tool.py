import subprocess
import os
import sys
import time

# --- Helper Functions for CLI Operations ---

def run_command(command, sudo_required=True, capture_output=True, text=True, check=True):
    """
    Executes a shell command.
    """
    if sudo_required and os.geteuid() != 0:
        print("Error: This operation requires root privileges. Please run the script with 'sudo'.")
        sys.exit(1)

    try:
        cmd_with_sudo = command[:] # Make a copy
        if sudo_required and cmd_with_sudo[0] != 'sudo': # Add sudo if not already there
            cmd_with_sudo.insert(0, 'sudo')

        # For dd with status=progress, we don't want to capture output directly for real-time updates
        if 'status=progress' in ' '.join(cmd_with_sudo):
            result = subprocess.run(cmd_with_sudo, capture_output=False, check=check)
        else:
            result = subprocess.run(cmd_with_sudo, capture_output=capture_output, text=text, check=check)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return None
    except FileNotFoundError:
        print(f"Error: Command '{command[0]}' not found. Make sure it's installed on your system.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def list_storage_devices():
    """
    Lists available storage devices and their partitions using lsblk.
    """
    print("\n--- Available Storage Devices & Partitions ---")
    print("Please carefully identify your target device (e.g., /dev/sdb, /dev/nvme0n1)")
    print("---------------------------------------------")
    result = run_command(['lsblk', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT'], sudo_required=False)
    if result:
        print(result.stdout)
    print("---------------------------------------------\n")

def get_device_path_from_user(prompt_type="device"):
    """
    Prompts the user to enter a device or partition path and performs basic validation.
    Returns the path or None if the user types 'back'.
    """
    while True:
        device_path = input(f"Enter the FULL {prompt_type} path (e.g., /dev/sdb, /dev/sdb1, /dev/nvme0n1) or type 'back' to return: ").strip().lower()
        if device_path == 'back':
            print("Returning to main menu.")
            return None
        elif not device_path.startswith('/dev/'):
            print("Invalid path format. It should start with '/dev/'.")
        elif not os.path.exists(device_path):
            print(f"Path '{device_path}' does not seem to exist. Please check 'lsblk' output.")
        else:
            confirmation = input(f"You selected '{device_path}'. Is this correct? (yes/no): ").lower()
            if confirmation == 'yes':
                return device_path
            else:
                print("Device selection cancelled. Please try again or type 'back' to return.")

def get_source_destination_paths(action="copy"):
    """
    Prompts user for source and destination paths.
    Returns (source, destination) or (None, None) if the user types 'back'.
    """
    source = None
    destination = None

    while True:
        source_input = input(f"Enter SOURCE path (file or directory to {action}) or type 'back' to return: ").strip().lower()
        if source_input == 'back':
            print("Returning to main menu.")
            return None, None
        if not os.path.exists(source_input):
            print(f"Source path '{source_input}' does not exist. Please check.")
            continue
        source = source_input
        break

    while True:
        destination_input = input(f"Enter DESTINATION path (where to {action}) or type 'back' to return: ").strip().lower()
        if destination_input == 'back':
            print("Returning to main menu.")
            return None, None
        # Basic check for destination parent directory existence
        if not os.path.exists(os.path.dirname(destination_input) or '.'):
             print(f"Destination parent directory does not exist for '{destination_input}'.")
             continue
        destination = destination_input
        break
    return source, destination

def confirm_action(action_description):
    """
    Asks for explicit confirmation for destructive actions.
    Returns True if confirmed, False if cancelled or 'back'.
    """
    print(f"\n!!! DANGER: You are about to {action_description}. This action is IRREVERSIBLE. !!!")
    confirmation = input("Type 'CONFIRM' (in uppercase) to proceed, or 'back' to return, or anything else to cancel: ").strip().lower()
    if confirmation == "confirm":
        return True
    elif confirmation == "back":
        print("Returning to main menu.")
        return False # Treat 'back' as a cancellation for confirmation purposes
    else:
        print("Action cancelled.")
        return False

# --- Main Operations ---

def copy_data():
    """Copies files/directories."""
    print("\n--- Copy Data ---")
    source, destination = get_source_destination_paths("copy")
    if source is None: # User typed 'back'
        return
    
    print(f"Copying '{source}' to '{destination}'...")
    if not confirm_action(f"copy '{source}' to '{destination}'"):
        return

    # -a for archive mode (preserves permissions, timestamps, etc.)
    # -v for verbose output
    result = run_command(['cp', '-av', source, destination], sudo_required=True)
    if result:
        print("Data copied successfully.")
    else:
        print("Data copy failed.")

def delete_data():
    """Deletes files/directories/full device data."""
    print("\n--- Delete Data ---")
    print("1. Delete specific files/directories")
    print("2. Securely wipe entire device (DANGEROUS & SLOW!)")
    print("Type 'back' to return to main menu.")
    
    delete_choice = input("Enter your choice (1 or 2): ").strip().lower()

    if delete_choice == 'back':
        print("Returning to main menu.")
        return
    elif delete_choice == '1':
        path_to_delete = input("Enter the path of the file or directory to delete or type 'back' to return: ").strip().lower()
        if path_to_delete == 'back':
            print("Returning to main menu.")
            return
        
        if confirm_action(f"delete '{path_to_delete}'"):
            print(f"Deleting '{path_to_delete}'...")
            # -r for recursive (directories), -f for force (no prompt)
            result = run_command(['rm', '-rf', path_to_delete], sudo_required=True)
            if result:
                print("Data deleted successfully.")
            else:
                print("Data deletion failed.")
        else:
            print("Deletion cancelled.")
    elif delete_choice == '2':
        list_storage_devices()
        device_to_wipe = get_device_path_from_user("device")
        if device_to_wipe is None:
            return
            
        if confirm_action(f"PERMANENTLY WIPE ALL DATA from '{device_to_wipe}' (zeros out the entire disk)"):
            print(f"Wiping all data from '{device_to_wipe}'. This will take a long time for large drives...")
            # dd if=/dev/zero of=/dev/sdb bs=4M status=progress
            result = run_command(['dd', 'if=/dev/zero', f'of={device_to_wipe}', 'bs=4M', 'status=progress'], sudo_required=True, capture_output=False, check=False)
            if result and result.returncode == 0:
                print(f"Successfully wiped '{device_to_wipe}'.")
            else:
                print(f"Failed to wipe '{device_to_wipe}'.")
        else:
            print("Device wipe cancelled.")
    else:
        print("Invalid choice. Returning to main menu.")

def format_disk():
    """Formats a selected entire disk with a chosen filesystem."""
    print("\n--- Format Entire Disk ---")
    list_storage_devices()
    device_to_format = get_device_path_from_user("device")
    if device_to_format is None:
        return

    print("Available Filesystem Types:")
    print("1. FAT32 (Compatible with Windows, macOS, Linux)")
    print("2. NTFS (Primarily Windows, good Linux support)")
    print("3. Ext4 (Linux Native)")
    print("Type 'back' to return to main menu.")

    fs_choice = input("Enter your desired filesystem type (1, 2, or 3): ").strip().lower()

    if fs_choice == 'back':
        print("Returning to main menu.")
        return

    filesystem_map = {
        '1': {'type': 'fat32', 'command': 'mkfs.fat -F 32'},
        '2': {'type': 'ntfs', 'command': 'mkfs.ntfs -f'}, # -f for force
        '3': {'type': 'ext4', 'command': 'mkfs.ext4 -F'}  # -F for force
    }

    if fs_choice in filesystem_map:
        fs_info = filesystem_map[fs_choice]
        fs_type = fs_info['type']
        mkfs_command = fs_info['command'].split() # Split to list for subprocess

        if confirm_action(f"format '{device_to_format}' (entire disk) with '{fs_type}'"):
            # First, try to unmount the device and its common partitions
            print(f"Attempting to unmount {device_to_format} and its partitions...")
            run_command(['umount', f"{device_to_format}1"], sudo_required=True, check=False)
            run_command(['umount', f"{device_to_format}2"], sudo_required=True, check=False)
            run_command(['umount', device_to_format], sudo_required=True, check=False)
            print("Unmount attempts finished. Proceeding with format...")

            full_format_command = mkfs_command + [device_to_format]
            result = run_command(full_format_command, sudo_required=True, capture_output=True)

            if result and result.returncode == 0:
                print(f"'{device_to_format}' successfully formatted to {fs_type}.")
            else:
                print(f"Formatting failed for '{device_to_format}'.")
        # else: confirm_action already printed cancellation message
    else:
        print("Invalid filesystem choice. Returning to main menu.")


def manage_partitions():
    """
    Provides options to create/delete partitions using fdisk/parted.
    Note: This is an advanced operation and requires careful handling.
    """
    print("\n--- Partition Management (Advanced) ---")
    print("Warning: Incorrect partition management can render your device unusable.")
    list_storage_devices()
    device_for_partition = get_device_path_from_user("device")
    if device_for_partition is None:
        return

    print("1. Start 'fdisk' interactive mode (for MBR/GPT, common for USBs)")
    print("2. Start 'parted' interactive mode (more powerful, supports GPT better)")
    print("3. List partitions (fdisk -l)")
    print("Type 'back' to return to main menu.")

    partition_choice = input("Enter your choice (1, 2, or 3): ").strip().lower()

    if partition_choice == 'back':
        print("Returning to main menu.")
        return
    elif partition_choice == '1':
        if confirm_action(f"enter 'fdisk' interactive mode for {device_for_partition}"):
            print(f"Starting 'fdisk {device_for_partition}'. Type 'm' for help inside fdisk.")
            run_command(['fdisk', device_for_partition], sudo_required=True, capture_output=False) # Direct interactive mode
            print("Exited fdisk.")
        # else: confirm_action already printed cancellation message
    elif partition_choice == '2':
        if confirm_action(f"enter 'parted' interactive mode for {device_for_partition}"):
            print(f"Starting 'parted {device_for_partition}'. Type 'help' for help inside parted.")
            run_command(['parted', device_for_partition], sudo_required=True, capture_output=False) # Direct interactive mode
            print("Exited parted.")
        # else: confirm_action already printed cancellation message
    elif partition_choice == '3':
        print(f"Listing partitions for {device_for_partition}:")
        run_command(['fdisk', '-l', device_for_partition], sudo_required=False)
    else:
        print("Invalid choice. Returning to main menu.")


def check_disk_health():
    """
    Checks disk health using smartctl (if installed).
    """
    print("\n--- Check Disk Health (S.M.A.R.T.) ---")
    list_storage_devices()
    device_to_check = get_device_path_from_user("device")
    if device_to_check is None:
        return

    print(f"Checking S.M.A.R.T. health for {device_to_check}...")
    # smartctl needs to be installed (e.g., sudo apt install smartmontools)
    result = run_command(['smartctl', '-H', device_to_check], sudo_required=True)
    if result:
        print(result.stdout)
        # Full SMART report
        full_report = input("Do you want a full S.M.A.R.T. report? (yes/no): ").lower()
        if full_report == 'yes':
            run_command(['smartctl', '-a', device_to_check], sudo_required=True, capture_output=False)
    else:
        print("Could not retrieve S.M.A.R.T. data. 'smartctl' might not be installed or supported for this device.")


def view_disk_usage():
    """
    Views disk usage using 'df -h' and 'du -sh'.
    """
    print("\n--- View Disk Usage ---")
    print("1. View filesystem disk space (df -h)")
    print("2. View directory/file size (du -sh)")
    print("Type 'back' to return to main menu.")

    usage_choice = input("Enter your choice (1 or 2): ").strip().lower()

    if usage_choice == 'back':
        print("Returning to main menu.")
        return
    elif usage_choice == '1':
        print("Filesystem Disk Space:")
        run_command(['df', '-h'], sudo_required=False)
    elif usage_choice == '2':
        path_for_du = input("Enter the path (directory or file) to check size for or type 'back' to return: ").strip().lower()
        if path_for_du == 'back':
            print("Returning to main menu.")
            return
        if os.path.exists(path_for_du):
            print(f"Size of '{path_for_du}':")
            run_command(['du', '-sh', path_for_du], sudo_required=False)
        else:
            print(f"Path '{path_for_du}' does not exist.")
    else:
        print("Invalid choice. Returning to main menu.")

def create_directory():
    """
    Creates a new directory.
    """
    print("\n--- Create Directory ---")
    dir_path = input("Enter the full path for the new directory or type 'back' to return: ").strip().lower()
    if dir_path == 'back':
        print("Returning to main menu.")
        return
    if os.path.exists(dir_path):
        print(f"Directory '{dir_path}' already exists.")
        return

    if confirm_action(f"create directory '{dir_path}'"):
        result = run_command(['mkdir', '-p', dir_path], sudo_required=True)
        if result:
            print(f"Directory '{dir_path}' created successfully.")
        else:
            print(f"Failed to create directory '{dir_path}'.")
    # else: confirm_action already printed cancellation message

def mount_unmount_device():
    """
    Mounts or unmounts a device/partition.
    """
    print("\n--- Mount/Unmount Device ---")
    print("1. Mount a partition")
    print("2. Unmount a partition/device")
    print("Type 'back' to return to main menu.")

    choice = input("Enter your choice (1 or 2): ").strip().lower()

    if choice == 'back':
        print("Returning to main menu.")
        return
    elif choice == '1':
        list_storage_devices()
        partition_path = get_device_path_from_user("partition")
        if partition_path is None:
            return

        mount_point = input("Enter the mount point directory (e.g., /mnt/myusb, will be created if needed) or type 'back' to return: ").strip().lower()
        if mount_point == 'back':
            print("Returning to main menu.")
            return

        if not os.path.exists(mount_point):
            print(f"Mount point '{mount_point}' does not exist. Creating it...")
            if not confirm_action(f"create mount point directory '{mount_point}'"):
                return # If creation is cancelled, also cancel mount
            run_command(['mkdir', '-p', mount_point], sudo_required=True)

        if confirm_action(f"mount '{partition_path}' to '{mount_point}'"):
            result = run_command(['mount', partition_path, mount_point], sudo_required=True)
            if result:
                print(f"Successfully mounted '{partition_path}' to '{mount_point}'.")
            else:
                print("Mount failed.")
        # else: confirm_action already printed cancellation message
    elif choice == '2':
        path_to_unmount = input("Enter the device/partition path OR mount point to unmount or type 'back' to return: ").strip().lower()
        if path_to_unmount == 'back':
            print("Returning to main menu.")
            return
        
        if confirm_action(f"unmount '{path_to_unmount}'"):
            result = run_command(['umount', path_to_unmount], sudo_required=True)
            if result:
                print(f"Successfully unmounted '{path_to_unmount}'.")
            else:
                print("Unmount failed.")
        # else: confirm_action already printed cancellation message
    else:
        print("Invalid choice. Returning to main menu.")

# --- New Features ---

def backup_disk_to_image():
    """
    Backs up a partition or entire disk to an image file using dd.
    """
    print("\n--- Backup Partition/Disk to Image ---")
    list_storage_devices()
    source_path = get_device_path_from_user("device/partition to backup")
    if source_path is None:
        return

    destination_image_path = input("Enter the FULL path for the output image file (e.g., /home/user/my_backup.img) or type 'back' to return: ").strip().lower()
    if destination_image_path == 'back':
        print("Returning to main menu.")
        return

    if not os.path.isdir(os.path.dirname(destination_image_path) or '.'):
        print("Error: Destination directory does not exist.")
        return

    if confirm_action(f"backup '{source_path}' to '{destination_image_path}'"):
        # Unmount the source if it's mounted
        print(f"Attempting to unmount {source_path} before backup...")
        run_command(['umount', source_path], sudo_required=True, check=False)
        
        print(f"Creating image from '{source_path}' to '{destination_image_path}'. This may take time...")
        # dd if=/dev/sdb of=/path/to/backup.img bs=4M status=progress
        result = run_command(['dd', f'if={source_path}', f'of={destination_image_path}', 'bs=4M', 'status=progress'], sudo_required=True, capture_output=False, check=False)
        if result and result.returncode == 0:
            print(f"Backup of '{source_path}' to '{destination_image_path}' completed successfully.")
        else:
            print(f"Backup failed for '{source_path}'.")
    # else: confirm_action already printed cancellation message

def restore_image_to_disk():
    """
    Restores an image file to a partition or entire disk using dd.
    """
    print("\n--- Restore Image to Partition/Disk ---")
    image_path = input("Enter the FULL path to the image file to restore (e.g., /home/user/my_backup.img) or type 'back' to return: ").strip().lower()
    if image_path == 'back':
        print("Returning to main menu.")
        return
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found.")
        return

    list_storage_devices()
    destination_path = get_device_path_from_user("destination device/partition")
    if destination_path is None:
        return

    if confirm_action(f"RESTORE IMAGE '{image_path}' to '{destination_path}'. ALL DATA on {destination_path} WILL BE OVERWRITTEN!"):
        # Unmount the destination if it's mounted
        print(f"Attempting to unmount {destination_path} before restore...")
        run_command(['umount', destination_path], sudo_required=True, check=False)

        print(f"Restoring image '{image_path}' to '{destination_path}'. This may take time...")
        # dd if=/path/to/backup.img of=/dev/sdb bs=4M status=progress
        result = run_command(['dd', f'if={image_path}', f'of={destination_path}', 'bs=4M', 'status=progress'], sudo_required=True, capture_output=False, check=False)
        if result and result.returncode == 0:
            print(f"Restore of '{image_path}' to '{destination_path}' completed successfully.")
        else:
            print(f"Restore failed for '{destination_path}'.")
    # else: confirm_action already printed cancellation message

def create_bootable_usb():
    """
    Creates a bootable USB from an ISO file using dd.
    """
    print("\n--- Create Bootable USB from ISO ---")
    iso_path = input("Enter the FULL path to the ISO file (e.g., /home/user/ubuntu.iso) or type 'back' to return: ").strip().lower()
    if iso_path == 'back':
        print("Returning to main menu.")
        return
    if not os.path.exists(iso_path) or not iso_path.lower().endswith('.iso'):
        print(f"Error: ISO file '{iso_path}' not found or is not an ISO file.")
        return

    list_storage_devices()
    usb_device = get_device_path_from_user("USB device (e.g., /dev/sdb)")
    if usb_device is None:
        return

    if confirm_action(f"CREATE BOOTABLE USB from '{iso_path}' to '{usb_device}'. ALL DATA on {usb_device} WILL BE OVERWRITTEN!"):
        # Unmount the USB device if it's mounted
        print(f"Attempting to unmount {usb_device} before writing ISO...")
        run_command(['umount', usb_device], sudo_required=True, check=False)

        print(f"Writing ISO '{iso_path}' to '{usb_device}'. This may take time...")
        # dd if=/path/to/image.iso of=/dev/sdb bs=4M status=progress
        result = run_command(['dd', f'if={iso_path}', f'of={usb_device}', 'bs=4M', 'status=progress', 'oflag=sync'], sudo_required=True, capture_output=False, check=False)
        if result and result.returncode == 0:
            print(f"Bootable USB '{usb_device}' created successfully from '{iso_path}'.")
            print("Note: You may need to sync the changes (sudo sync) or remove and re-insert the USB for it to be recognized.")
        else:
            print(f"Failed to create bootable USB on '{usb_device}'.")
    # else: confirm_action already printed cancellation message

def format_partition():
    """Formats a selected partition with a chosen filesystem."""
    print("\n--- Format Partition ---")
    list_storage_devices()
    partition_to_format = get_device_path_from_user("partition")
    if partition_to_format is None:
        return

    # Basic check to ensure it's likely a partition (e.g., /dev/sdb1, not /dev/sdb)
    if not (partition_to_format.startswith('/dev/sd') and any(char.isdigit() for char in partition_to_format.split('/')[-1])) and \
       not (partition_to_format.startswith('/dev/nvme') and 'p' in partition_to_format.split('/')[-1]):
        print("Warning: The selected path does not look like a partition (e.g., /dev/sdb1). Proceeding anyway, but be careful!")
        if not confirm_action(f"format what appears to be a FULL DISK, not a partition: {partition_to_format}"):
            print("Operation cancelled.")
            return

    print("Available Filesystem Types:")
    print("1. FAT32 (Compatible with Windows, macOS, Linux)")
    print("2. NTFS (Primarily Windows, good Linux support)")
    print("3. Ext4 (Linux Native)")
    print("Type 'back' to return to main menu.")

    fs_choice = input("Enter your desired filesystem type (1, 2, or 3): ").strip().lower()

    if fs_choice == 'back':
        print("Returning to main menu.")
        return

    filesystem_map = {
        '1': {'type': 'fat32', 'command': 'mkfs.fat -F 32'},
        '2': {'type': 'ntfs', 'command': 'mkfs.ntfs -f'}, # -f for force
        '3': {'type': 'ext4', 'command': 'mkfs.ext4 -F'}  # -F for force
    }

    if fs_choice in filesystem_map:
        fs_info = filesystem_map[fs_choice]
        fs_type = fs_info['type']
        mkfs_command = fs_info['command'].split()

        if confirm_action(f"format '{partition_to_format}' (partition) with '{fs_type}'"):
            print(f"Attempting to unmount {partition_to_format} before format...")
            run_command(['umount', partition_to_format], sudo_required=True, check=False)
            print("Unmount attempt finished. Proceeding with format...")

            full_format_command = mkfs_command + [partition_to_format]
            result = run_command(full_format_command, sudo_required=True, capture_output=True)

            if result and result.returncode == 0:
                print(f"'{partition_to_format}' successfully formatted to {fs_type}.")
            else:
                print(f"Formatting failed for '{partition_to_format}'.")
        # else: confirm_action already printed cancellation message
    else:
        print("Invalid filesystem choice. Returning to main menu.")

def view_smart_errors():
    """
    Views S.M.A.R.T. errors for a selected disk.
    """
    print("\n--- View S.M.A.R.T. Errors ---")
    list_storage_devices()
    device_to_check = get_device_path_from_user("device")
    if device_to_check is None:
        return

    print(f"Checking S.M.A.R.T. error log for {device_to_check}...")
    # smartctl -l error /dev/sdb
    result = run_command(['smartctl', '-l', 'error', device_to_check], sudo_required=True)
    if result:
        print(result.stdout)
    else:
        print("Could not retrieve S.M.A.R.T. error log. 'smartctl' might not be installed or supported for this device.")

def benchmark_disk_speed():
    """
    Performs basic read/write benchmarking using dd.
    """
    print("\n--- Disk Benchmarking (Read/Write Speed) ---")
    list_storage_devices()
    device_to_benchmark = get_device_path_from_user("device")
    if device_to_benchmark is None:
        return

    temp_test_file = "/tmp/disk_test_file.bin" # Temporary file for write test
    block_size = "1M"
    count = 1024 # 1GB test file (1024 * 1MB)

    print(f"\nBenchmarking '{device_to_benchmark}' with a {count * 1}MB test size...")
    print("Type 'back' at any prompt to return to main menu.")


    # --- Write Speed Test ---
    if not confirm_action(f"start Write Speed Test to '{temp_test_file}' (temporary file on your system disk)"):
        return
    
    print("\n--- Starting Write Speed Test ---")
    print(f"Writing {count * 1}MB to {temp_test_file} on {device_to_benchmark}...")
    start_time_write = time.time()
    # dd if=/dev/zero of=/tmp/disk_test_file.bin bs=1M count=1024 conv=fdatasync status=progress
    write_result = run_command(['dd', 'if=/dev/zero', f'of={temp_test_file}', f'bs={block_size}', f'count={count}', 'conv=fdatasync', 'status=progress'], sudo_required=False, capture_output=False, check=False)
    end_time_write = time.time()
    write_duration = end_time_write - start_time_write

    if write_result and write_result.returncode == 0:
        file_size_bytes = count * 1024 * 1024 # Calculate actual bytes written
        write_speed_mbps = (file_size_bytes / (1024 * 1024)) / write_duration
        print(f"Write test completed in {write_duration:.2f} seconds.")
        print(f"Average Write Speed: {write_speed_mbps:.2f} MB/s")
    else:
        print("Write test failed.")
    
    # Clean up the temporary file
    if os.path.exists(temp_test_file):
        run_command(['rm', '-f', temp_test_file], sudo_required=False)
        print(f"Removed temporary file: {temp_test_file}")


    # --- Read Speed Test ---
    if not confirm_action(f"start Read Speed Test from '{device_to_benchmark}'"):
        return
        
    print("\n--- Starting Read Speed Test ---")
    print(f"Reading {count * 1}MB from {device_to_benchmark}...")
    start_time_read = time.time()
    # dd if=/dev/sdb of=/dev/null bs=1M count=1024 status=progress
    read_result = run_command(['dd', f'if={device_to_benchmark}', 'of=/dev/null', f'bs={block_size}', f'count={count}', 'status=progress'], sudo_required=True, capture_output=False, check=False)
    end_time_read = time.time()
    read_duration = end_time_read - start_time_read

    if read_result and read_result.returncode == 0:
        file_size_bytes = count * 1024 * 1024 # Calculate actual bytes read
        read_speed_mbps = (file_size_bytes / (1024 * 1024)) / read_duration
        print(f"Read test completed in {read_duration:.2f} seconds.")
        print(f"Average Read Speed: {read_speed_mbps:.2f} MB/s")
    else:
        print("Read test failed.")
        print("Note: Read test might fail if the device is not readable or already mounted.")

    print("\nBenchmarking complete.")

def show_developer_info():
    """Displays information about the developer."""
    print("\n--- Developer Information ---")
    print("Tool Name: Storage Device Management Tool (Linux CLI)")
    print("Version: 1.0")
    print("Developed by: [Sowmitro Halder Badhon (Darklord690)]") 
    print("Contact: [sowmitro2235@gmail.com]")    
    print("https://wa.me/+8801921964044")
    print("Denote $10 Buy a coffee  Bkash/Nagod  01921964044 ")
    print("Purpose: A command-line utility for managing storage devices on Linux systems.")
    print("Disclaimer: Use with caution. Incorrect operations can lead to data loss.")
    print("-----------------------------\n")

# --- Main Menu ---

def main_menu():
    """Displays the main menu and handles user input."""
    while True:
        print("\n--- Storage Device Management Tool (Linux CLI) ---")
        print("1. List Storage Devices (lsblk)")
        print("2. Copy Data (cp)")
        print("3. Delete Data (rm / dd)")
        print("4. Format Entire Disk (mkfs)")
        print("5. Manage Partitions (fdisk/parted - Advanced!)")
        print("6. Check Disk Health (S.M.A.R.T. Full Report)")
        print("7. View Disk Usage (df/du)")
        print("8. Create Directory (mkdir)")
        print("9. Mount/Unmount Device")
        print("-------------------------------------------------")
        print("--- Advanced Features ---")
        print("10. Backup Partition/Disk to Image (dd)")
        print("11. Restore Image to Partition/Disk (dd)")
        print("12. Create Bootable USB from ISO (dd)")
        print("13. Format Partition Only (mkfs)")
        print("14. View S.M.A.R.T. Errors Only")
        print("15. Benchmark Disk Read/Write Speed (dd)")
        print("-------------------------------------------------")
        print("00. Developer Info") # New option
        print("0. Exit")
        print("-------------------------------------------------")

        choice = input("Enter your choice (0-15, 00 for info): ").strip()

        if choice == '1':
            list_storage_devices()
        elif choice == '2':
            copy_data()
        elif choice == '3':
            delete_data()
        elif choice == '4':
            format_disk()
        elif choice == '5':
            manage_partitions()
        elif choice == '6':
            check_disk_health()
        elif choice == '7':
            view_disk_usage()
        elif choice == '8':
            create_directory()
        elif choice == '9':
            mount_unmount_device()
        elif choice == '10':
            backup_disk_to_image()
        elif choice == '11':
            restore_image_to_disk()
        elif choice == '12':
            create_bootable_usb()
        elif choice == '13':
            format_partition()
        elif choice == '14':
            view_smart_errors()
        elif choice == '15':
            benchmark_disk_speed()
        elif choice == '00': # Handle the new '00' choice
            show_developer_info()
        elif choice == '0':
            print("Exiting tool. Goodbye!")
            sys.exit(0)
        else:
            print("Name:Sowmitro Halder Badhon ")
            print("https://wa.me/+8801921964044")
            print("Denote $10 Buy a coffee  Bkash/Nagod  01921964044 ")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Warning: Most operations require root privileges.")
        print("It is highly recommended to run this script with 'sudo':")
        print("  sudo python3 disk_tool.py")
        print("Continuing without sudo might limit functionality.")
        input("Press Enter to continue or Ctrl+C to exit and restart with sudo...")
    main_menu()
