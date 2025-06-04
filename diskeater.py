#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DiskEater - Optimized file encryption tool
This script allows encrypting and decrypting files in a specified folder using parallel processing.

Author: Br3noAraujo
License: MIT

DISCLAIMERS:
1. This tool is for educational purposes only
2. Use at your own risk
3. Always keep backups of your important files
4. The author is not responsible for any data loss
5. Do not use this tool on critical system files
6. Keep your encryption keys safe
7. This tool is not intended for malicious purposes
"""

import os
import logging
import argparse
import hashlib
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from cryptography.fernet import Fernet
import multiprocessing
import mmap
import threading
from queue import Queue
import time
from colorama import init, Fore, Style

# Initialize colorama
init()

# Logging configuration with colors
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors"""
    def format(self, record):
        if record.levelno == logging.INFO:
            record.msg = f"{Fore.GREEN}{record.msg}{Style.RESET_ALL}"
        elif record.levelno == logging.WARNING:
            record.msg = f"{Fore.YELLOW}{record.msg}{Style.RESET_ALL}"
        elif record.levelno == logging.ERROR:
            record.msg = f"{Fore.RED}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

# Configure logging with colors
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# File handler (without colors)
file_handler = logging.FileHandler('diskeater.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Console handler (with colors)
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

def get_gradient_text(text, start_color, end_color):
    """Generate gradient text effect"""
    gradient = []
    for i, char in enumerate(text):
        # Calculate color transition
        r = int(start_color[0] + (end_color[0] - start_color[0]) * i / len(text))
        g = int(start_color[1] + (end_color[1] - start_color[1]) * i / len(text))
        b = int(start_color[2] + (end_color[2] - start_color[2]) * i / len(text))
        gradient.append(f"\033[38;2;{r};{g};{b}m{char}")
    return ''.join(gradient) + Style.RESET_ALL

# Define gradient colors (light green to emerald)
start_color = (144, 238, 144)  # Light green
end_color = (0, 168, 107)  # Emerald green

banner = get_gradient_text('''
                           (o)(o)
                           /  °° \\
                          /       |
                         /   \\^^^^|  I'm DiskEater
           ________     /    /\\__/
   _      /        \\   /    /
  / \\    /  ____    \\_/    /
 //\\ \\  /  /    \\         /
 V  \\ \\/  /      \\       /
     \\___/        \\_____/                   By Br3noAraujo
''', start_color, end_color)

class DiskEater:
    def __init__(self, target_dir: str):
        """Initialize DiskEater with optimized settings."""
        self.target_dir = Path(target_dir)
        self.key_file = Path('key')
        self.mystery_key_file = Path('.mystery_key')
        self.fernet = self._initialize_encryption()
        # Use all available cores for maximum performance
        self.max_workers = multiprocessing.cpu_count()
        # Optimized I/O buffer size (4MB)
        self.buffer_size = 4 * 1024 * 1024
        # Queue for file processing
        self.file_queue = Queue()
        # Lock for I/O operations
        self.io_lock = threading.Lock()

    def _generate_mystery_key(self) -> str:
        """Generate a mystery key based on system data."""
        system_info = [
            os.getenv('USER', ''),
            os.getenv('HOME', ''),
            str(os.getpid()),
            str(multiprocessing.cpu_count())
        ]
        mystery = ''.join(system_info)
        return hashlib.sha256(mystery.encode()).hexdigest()[:32]

    def _initialize_encryption(self) -> Fernet:
        """Initialize encryption with existing or new key."""
        try:
            if self.key_file.exists():
                with open(self.key_file, 'rb') as f:
                    key = f.read()
            else:
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                
                # Generate and save mystery key only on first run
                mystery_key = self._generate_mystery_key()
                with open(self.mystery_key_file, 'w') as f:
                    f.write(mystery_key)
                
            return Fernet(key)
        except Exception as e:
            logging.error(f"Error initializing encryption: {e}")
            raise

    def _verify_mystery_key(self, provided_key: str) -> bool:
        """Verify if the provided mystery key is valid."""
        try:
            if not self.mystery_key_file.exists():
                logging.error("Mystery key file not found")
                return False

            with open(self.mystery_key_file, 'r') as f:
                stored_key = f.read().strip()

            return provided_key == stored_key
        except Exception as e:
            logging.error(f"Error verifying mystery key: {e}")
            return False

    def _process_chunk(self, chunk: bytes, decrypt: bool) -> bytes:
        """Process a data chunk."""
        return self.fernet.decrypt(chunk) if decrypt else self.fernet.encrypt(chunk)

    def _process_file(self, file_path: Path, decrypt: bool = False) -> bool:
        """Process a single file using memory mapping for optimization."""
        try:
            if decrypt:
                if not file_path.name.startswith('(encrypted)'):
                    return False
            else:
                if file_path.name.startswith('(encrypted)'):
                    return False

            # Use memory mapping for better performance
            with open(file_path, 'rb') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                    # Process file in chunks
                    chunks = []
                    for i in range(0, mm.size(), self.buffer_size):
                        chunk = mm[i:min(i + self.buffer_size, mm.size())]
                        processed_chunk = self._process_chunk(chunk, decrypt)
                        chunks.append(processed_chunk)

            # Write processed file
            new_file = file_path.parent / (f'(encrypted){file_path.name}' if not decrypt else file_path.name.replace('(encrypted)', ''))
            
            with self.io_lock:
                with open(new_file, 'wb') as f:
                    for chunk in chunks:
                        f.write(chunk)
                os.remove(file_path)

            logging.info(f"File {'decrypted' if decrypt else 'encrypted'}: {file_path.name}")
            return True

        except Exception as e:
            logging.error(f"Error processing {file_path}: {e}")
            return False

    def _worker(self, decrypt: bool):
        """Worker for parallel processing."""
        while True:
            try:
                file_path = self.file_queue.get_nowait()
                self._process_file(file_path, decrypt)
                self.file_queue.task_done()
            except Queue.Empty:
                break
            except Exception as e:
                logging.error(f"Worker error: {e}")
                self.file_queue.task_done()

    def process_directory(self, decrypt: bool = False, mystery_key: str = None) -> None:
        """Process all files in parallel using multiple processes."""
        if not self.target_dir.exists():
            logging.error(f"Target folder '{self.target_dir}' not found. Creating folder...")
            self.target_dir.mkdir(exist_ok=True)
            return

        if decrypt and not self._verify_mystery_key(mystery_key):
            logging.error("Invalid mystery key!")
            return

        files = [f for f in self.target_dir.iterdir() if f.is_file()]
        total_files = len(files)
        
        if total_files == 0:
            logging.info("No files found to process")
            return

        # Add files to queue
        for file in files:
            self.file_queue.put(file)

        operation = "Decryption" if decrypt else "Encryption"
        start_time = time.time()
        logging.info(f"{Fore.GREEN}Starting {operation} of {total_files} files with {self.max_workers} workers{Style.RESET_ALL}")

        # Create and start workers
        workers = []
        for _ in range(self.max_workers):
            worker = threading.Thread(target=self._worker, args=(decrypt,))
            worker.start()
            workers.append(worker)

        # Wait for completion
        self.file_queue.join()
        for worker in workers:
            worker.join()

        end_time = time.time()
        duration = end_time - start_time
        logging.info(f"{Fore.GREEN}{operation} completed in {duration:.2f} seconds{Style.RESET_ALL}")

def show_simple_usage():
    """Show simple usage instructions"""
    print(banner)
    print(f"""
{Fore.GREEN}Usage:{Style.RESET_ALL}
  python diskeater.py <target_folder> [options]

{Fore.GREEN}Basic Examples:{Style.RESET_ALL}
  # Encrypt files in a folder
  python diskeater.py ./my_files

  # Decrypt files
  python diskeater.py ./my_files --decrypt --key "your_mystery_key"

{Fore.GREEN}For more information:{Style.RESET_ALL}
  python diskeater.py -h
""")

def main():
    print(banner)
    
    parser = argparse.ArgumentParser(
        description=f'''
{Fore.GREEN}DiskEater - A powerful and optimized file encryption tool{Style.RESET_ALL}

This tool provides fast and secure file encryption/decryption capabilities:
- Parallel processing using all available CPU cores
- Memory-mapped file operations for better performance
- Secure encryption using Fernet (symmetric encryption)
- Mystery key system for additional security
- Progress tracking and detailed logging

Log File: 'diskeater.log'
Key Files: 'key' and '.mystery_key'
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
{Fore.GREEN}EXAMPLES:{Style.RESET_ALL}
  # Encrypt all files in a directory
  python diskeater.py ./my_files

  # Decrypt files using the mystery key
  python diskeater.py ./my_files --decrypt --key "your_mystery_key"

{Fore.YELLOW}IMPORTANT NOTES:{Style.RESET_ALL}
- Always keep backups of your important files
- Store your mystery key in a safe place
- The tool will create the target directory if it doesn't exist
- All operations are logged in 'diskeater.log'
- Files are processed in parallel for maximum speed
- Original files are removed after processing

{Fore.RED}WARNING: This tool is for educational purposes only.
Use at your own risk.{Style.RESET_ALL}
        '''
    )
    parser.add_argument('target_dir', type=str,
                       help='Target directory containing files to process')
    parser.add_argument('--decrypt', action='store_true', 
                       help='Decrypt files instead of encrypting them')
    parser.add_argument('--key', type=str, 
                       help='Mystery key required for decryption')
    args = parser.parse_args()

    try:
        disk_eater = DiskEater(args.target_dir)
        disk_eater.process_directory(decrypt=args.decrypt, mystery_key=args.key)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        return 1
    return 0

if __name__ == '__main__':
    if len(os.sys.argv) == 1:
        show_simple_usage()
    else:
        exit(main()) 