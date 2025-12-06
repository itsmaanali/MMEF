#!/usr/bin/env python3
"""
Download Google Cluster Trace 2011 (ClusterData2011_2) dataset.
Official repository: https://github.com/google/cluster-data
Documentation: https://github.com/google/cluster-data/blob/master/ClusterData2011_2.md

This downloads from Google Cloud Storage bucket: gs://clusterdata-2011-2
- Trace covers 29 days (May 1-29, 2011)
- Cluster size: ~12,500 machines
- Total size: ~41GB compressed
- License: Creative Commons CC-BY 4.0

Usage:
    python download_google_2011.py --sample    # 1-day sample (~500MB)
    python download_google_2011.py --full      # Complete 29-day dataset (~41GB)
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Official Google Cloud Storage URLs
GSUTIL_BASE = "gs://clusterdata-2011-2"

# Files we need for fault detection
FILES_TO_DOWNLOAD = {
    'sample': {
        'machine_events': ['machine_events/part-00000-of-00001.csv.gz'],
        'task_events': [
            'task_events/part-00000-of-00500.csv.gz',
            'task_events/part-00001-of-00500.csv.gz'
        ],
        'task_usage': [
            'task_usage/part-00000-of-00500.csv.gz',
            'task_usage/part-00001-of-00500.csv.gz'
        ]
    },
    'full': {
        'machine_events': 'machine_events/',
        'task_events': 'task_events/',
        'task_usage': 'task_usage/'
    }
}


def check_gsutil():
    """Check if gsutil is installed."""
    try:
        subprocess.run(['gsutil', 'version'],
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def download_file(gs_path, local_path):
    """Download a single file from Google Cloud Storage."""
    print(f"  Downloading: {gs_path}")

    local_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = ['gsutil', '-m', 'cp', gs_path, str(local_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  ✗ Failed: {result.stderr}")
        return False

    print(f"  ✓ Downloaded: {local_path.name}")
    return True


def download_directory(gs_dir, local_dir):
    """Download entire directory from Google Cloud Storage."""
    print(f"  Downloading directory: {gs_dir}")

    local_dir.mkdir(parents=True, exist_ok=True)

    cmd = ['gsutil', '-m', 'cp', '-r', gs_dir + '*', str(local_dir)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  ✗ Failed: {result.stderr}")
        return False

    print(f"  ✓ Downloaded to: {local_dir}")
    return True


def download_sample(output_dir):
    """Download sample dataset (1 day, ~500MB)."""
    print("\n[1/3] Downloading sample Google Cluster Trace 2011...")
    print("      This will download ~500MB of data\n")

    output_path = Path(output_dir) / 'google-2011-sample'

    files = FILES_TO_DOWNLOAD['sample']
    success_count = 0
    total_count = sum(len(v) for v in files.values())

    for category, file_list in files.items():
        print(f"\n  [{category}]")
        category_dir = output_path / category

        for file_name in file_list:
            gs_path = f"{GSUTIL_BASE}/{file_name}"
            local_path = category_dir / Path(file_name).name

            if download_file(gs_path, local_path):
                success_count += 1

    print(f"\n  Downloaded {success_count}/{total_count} files")
    print(f"  ✓ Sample dataset ready at: {output_path}")

    return output_path


def download_full(output_dir):
    """Download full dataset (29 days, ~41GB)."""
    print("\n[1/3] Downloading FULL Google Cluster Trace 2011...")
    print("      WARNING: This will download ~41GB of data!")
    print("      This may take 30-90 minutes depending on connection.\n")

    response = input("Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("  Cancelled.")
        return None

    output_path = Path(output_dir) / 'google-2011-full'

    dirs = FILES_TO_DOWNLOAD['full']

    for category, gs_subdir in dirs.items():
        print(f"\n  [{category}]")
        gs_path = f"{GSUTIL_BASE}/{gs_subdir}"
        local_dir = output_path / category

        download_directory(gs_path, local_dir)

    print(f"\n  ✓ Full dataset ready at: {output_path}")
    return output_path


def create_readme(output_path):
    """Create README in downloaded dataset directory."""
    readme_content = """# Google Cluster Trace 2011

Downloaded from: gs://clusterdata-2011-2

## Files

### machine_events/
Machine lifecycle events (ADD, REMOVE, UPDATE)
Schema: timestamp, machine_id, event_type, platform_id, cpu_capacity, memory_capacity

### task_events/
Task submission, scheduling, and completion events
Schema: timestamp, job_id, task_index, machine_id, event_type, priority,
        cpu_request, memory_request, disk_request

### task_usage/
Resource utilization over time
Schema: start_time, end_time, job_id, task_index, machine_id,
        cpu_rate, canonical_memory_usage, assigned_memory,
        disk_io_time, local_disk_space_usage, max_cpu_rate,
        cycles_per_instruction, memory_accesses_per_instruction

## Event Type Codes

Machine Events:
- 0: ADD
- 1: REMOVE
- 2: UPDATE

Task Events:
- 0: SUBMIT
- 1: SCHEDULE
- 2: EVICT
- 3: FAIL
- 4: FINISH
- 5: KILL
- 6: LOST
- 7: UPDATE_PENDING
- 8: UPDATE_RUNNING

## Reference
https://github.com/google/cluster-data/blob/master/ClusterData2011_2.md
"""

    readme_path = output_path / 'README.txt'
    readme_path.write_text(readme_content)
    print(f"\n  ✓ Created: {readme_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Download Google Cluster Trace 2011 dataset'
    )
    parser.add_argument('--sample', action='store_true',
                       help='Download 1-day sample (~500MB)')
    parser.add_argument('--full', action='store_true',
                       help='Download full 29-day dataset (~40GB)')
    parser.add_argument('--output', type=str, default='.',
                       help='Output directory (default: current directory)')

    args = parser.parse_args()

    if not args.sample and not args.full:
        parser.print_help()
        print("\nError: Specify --sample or --full")
        sys.exit(1)

    print("="*80)
    print("GOOGLE CLUSTER TRACE 2011 DOWNLOADER")
    print("="*80)

    # Check for gsutil
    if not check_gsutil():
        print("\n✗ ERROR: gsutil not found!")
        print("\nInstall Google Cloud SDK:")
        print("  macOS:   brew install google-cloud-sdk")
        print("  Linux:   curl https://sdk.cloud.google.com | bash")
        print("  Windows: https://cloud.google.com/sdk/docs/install")
        sys.exit(1)

    print("\n✓ gsutil found")

    # Download
    if args.sample:
        output_path = download_sample(args.output)
    else:
        output_path = download_full(args.output)

    if output_path:
        create_readme(output_path)

        print("\n" + "="*80)
        print("✅ DOWNLOAD COMPLETE!")
        print("="*80)
        print(f"\nDataset location: {output_path.absolute()}")
        print("\nNext steps:")
        print(f"  1. Parse the data:")
        print(f"     python parse_google_2011.py --input {output_path}")
        print(f"  2. Generate features:")
        print(f"     python generate_features.py --dataset google-2011")


if __name__ == '__main__':
    main()
