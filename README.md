
# Linux Disk Management CLI Tool

A powerful Python-based command-line interface (CLI) tool designed for Linux systems to perform a wide range of storage device operations. This includes common tasks like listing, copying, deleting, and formatting, as well as more advanced features like backing up/restoring disk images, creating bootable USBs, and basic disk benchmarking.

**⚠️ WARNING: This tool performs destructive operations. Use with extreme caution. Incorrect usage can lead to permanent data loss on your system.**

## Features

* **1. List Storage Devices:** View all block devices and their partitions (`lsblk`).
* **2. Copy Data:** Copy files or directories (`cp`).
* **3. Delete Data:** Delete specific files/directories (`rm`) or securely wipe an entire device (`dd`).
* **4. Format Entire Disk:** Format an entire physical disk (e.g., `/dev/sdb`) with FAT32, NTFS, or Ext4 filesystems (`mkfs`).
* **5. Manage Partitions:** Enter interactive `fdisk` or `parted` modes for advanced partitioning operations.
* **6. Check Disk Health:** Retrieve a full S.M.A.R.T. report for a selected disk (`smartctl`).
* **7. View Disk Usage:** Check filesystem disk space (`df`) and specific directory/file sizes (`du`).
* **8. Create Directory:** Create new directories (`mkdir`).
* **9. Mount/Unmount Device:** Mount or unmount partitions/devices to/from a specific mount point.
* ---
* **10. Backup Partition/Disk to Image:** Create a bit-for-bit image (`.img` file) of a selected partition or entire disk (`dd`).
* **11. Restore Image to Partition/Disk:** Write an existing `.img` file back onto a selected partition or entire disk. **This will overwrite all existing data on the destination.** (`dd`)
* **12. Create Bootable USB from ISO:** Write an ISO image file to a USB drive, making it bootable. **This will erase all data on the USB.** (`dd`)
* **13. Format Partition Only:** Format a specific partition (e.g., `/dev/sdb1`) with FAT32, NTFS, or Ext4 filesystems (`mkfs`).
* **14. View S.M.A.R.T. Errors Only:** Display only the error log from the S.M.A.R.T. data (`smartctl`).
* **15. Benchmark Disk Read/Write Speed:** Perform a simple sequential read and write speed test on a selected device (`dd`).

## Prerequisites

Before running this tool, ensure you have the following installed on your Linux system. Most standard utilities are pre-installed on modern Linux distributions.

* **Python 3**
* **Standard Linux utilities (usually pre-installed):**
    * `lsblk` (from `util-linux`)
    * `cp`, `rm`, `mkdir`, `df`, `du`, `dd` (from `coreutils`)
    * `umount`, `mount` (from `util-linux`)
    * `fdisk` (from `util-linux`)
    * `parted` (separate package, often pre-installed)
* **Filesystem utilities:**
    * For FAT32: `dosfstools` (e.g., `sudo apt install dosfstools` on Debian/Ubuntu)
    * For NTFS: `ntfs-3g` (e.g., `sudo apt install ntfs-3g` on Debian/Ubuntu)
    * For Ext4: `e2fsprogs` (e.g., `sudo apt install e2fsprogs` on Debian/Ubuntu)
* **S.M.A.R.T. tools (optional, for health check and errors):**
    * `smartmontools` (e.g., `sudo apt install smartmontools` on Debian/Ubuntu)

## Installation & Usage

1.  **Create the project directory and files:**
    On your Linux machine, create a folder named `LinuxDiskTool` (or any name you prefer) and then create the `disk_tool.py`, `README.md`, `LICENSE`, `.gitignore`, and `requirements.txt` files inside it with the content provided above.

    ```bash
    mkdir LinuxDiskTool
    cd LinuxDiskTool
    # Now create the files manually using your text editor or 'nano'
    # For example: nano disk_tool.py, paste content, save (Ctrl+O, Enter, Ctrl+X)
    ```

2.  **Make the script executable:**
    ```bash
    chmod +x disk_tool.py
    ```

3.  **Run the tool with `sudo`:**
    **It is CRUCIAL to run this tool with `sudo` for almost all operations, as they require root privileges to interact with disk devices.**

    ```bash
    sudo python3 disk_tool.py
    ```
    You will be prompted for your user password.

## How to Use

The tool will display a menu with numbered options. Enter the number corresponding to the operation you wish to perform and press Enter.

**Always read the on-screen prompts and warnings carefully, especially when performing destructive actions like formatting, deleting, or wiping data.** Double-check the device or partition path you enter to avoid accidental data loss on critical drives.

## Contributing

Contributions are welcome! If you have ideas for new features, bug fixes, or improvements, please feel free to:

1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add new feature X'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a Pull Request.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.  
