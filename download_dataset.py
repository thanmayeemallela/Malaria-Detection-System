"""
Download and extract the official NIH / NLM Malaria Cell Images Dataset.
Source: National Library of Medicine (Lister Hill National Center for Biomedical Communications)
URL: https://data.lhncbc.nlm.nih.gov/public/Malaria/cell_images.zip
"""

import os
import sys
import zipfile
import shutil
from pathlib import Path
import urllib.request

DATASET_DIR = Path('dataset')
DEST_DIR = DATASET_DIR / 'cell_images'
SAMPLE_DIR = Path('sample_images')
ZIP_URL = 'https://data.lhncbc.nlm.nih.gov/public/Malaria/cell_images.zip'
ZIP_PATH = DATASET_DIR / 'cell_images.zip'


def reporthook(block_num, block_size, total_size):
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(100.0, downloaded * 100 / total_size)
        mb_down = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        sys.stdout.write(f"\rDownloading NIH Malaria dataset: {mb_down:.1f} MB / {mb_total:.1f} MB ({percent:.1f}%)")
        sys.stdout.flush()


def download_and_extract():
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    parasitized_dir = DEST_DIR / 'Parasitized'
    uninfected_dir = DEST_DIR / 'Uninfected'

    if parasitized_dir.exists() and uninfected_dir.exists():
        p_count = len(list(parasitized_dir.glob('*.png')))
        u_count = len(list(uninfected_dir.glob('*.png')))
        if p_count > 100 and u_count > 100:
            print(f"Dataset already exists: {p_count} Parasitized, {u_count} Uninfected images.")
            copy_samples(parasitized_dir, uninfected_dir)
            return

    print(f"Connecting to NIH repository: {ZIP_URL}")
    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib.request.Request(ZIP_URL, headers=headers)

    with urllib.request.urlopen(req) as response, open(ZIP_PATH, 'wb') as out_file:
        total_size = int(response.getheader('Content-Length', 0))
        block_size = 1024 * 1024  # 1MB buffer
        downloaded = 0
        while True:
            chunk = response.read(block_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            if total_size > 0:
                pct = (downloaded / total_size) * 100
                sys.stdout.write(f"\rDownloading: {downloaded / (1024*1024):.1f}/{total_size / (1024*1024):.1f} MB ({pct:.1f}%)")
                sys.stdout.flush()

    print("\nDownload complete. Extracting dataset zip archive...")
    with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
        zf.extractall(DATASET_DIR)

    # Check structure
    inner_dir = DATASET_DIR / 'cell_images'
    if not inner_dir.exists():
        # Look for nested folder
        for item in DATASET_DIR.iterdir():
            if item.is_dir() and (item / 'Parasitized').exists():
                shutil.move(str(item), str(DEST_DIR))
                break

    # Clean up zip file to save disk space
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
        print("Removed temporary zip file to save disk space.")

    parasitized_dir = DEST_DIR / 'Parasitized'
    uninfected_dir = DEST_DIR / 'Uninfected'
    p_count = len(list(parasitized_dir.glob('*.png'))) if parasitized_dir.exists() else 0
    u_count = len(list(uninfected_dir.glob('*.png'))) if uninfected_dir.exists() else 0

    print(f"Dataset extracted successfully to {DEST_DIR}!")
    print(f"Total: {p_count} Parasitized images, {u_count} Uninfected images.")

    copy_samples(parasitized_dir, uninfected_dir)


def copy_samples(parasitized_dir, uninfected_dir):
    """Copies a few real NIH sample images to sample_images/ for quick testing."""
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    p_files = sorted(list(parasitized_dir.glob('*.png')))[:5]
    u_files = sorted(list(uninfected_dir.glob('*.png')))[:5]

    for idx, f in enumerate(p_files, 1):
        target = SAMPLE_DIR / f"real_nih_parasitized_{idx}.png"
        shutil.copy(f, target)

    for idx, f in enumerate(u_files, 1):
        target = SAMPLE_DIR / f"real_nih_uninfected_{idx}.png"
        shutil.copy(f, target)

    print(f"Copied {len(p_files)} Parasitized and {len(u_files)} Uninfected real NIH sample images to {SAMPLE_DIR}/.")


if __name__ == '__main__':
    download_and_extract()
