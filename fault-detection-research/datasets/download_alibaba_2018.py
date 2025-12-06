#!/usr/bin/env python3
"""
Download Alibaba Cluster Trace 2018 (cluster-trace-v2018) dataset.
Official repository: https://github.com/alibaba/clusterdata
Documentation: https://github.com/alibaba/clusterdata/blob/master/cluster-trace-v2018/trace_2018.md

Dataset characteristics:
- 4,000 machines over 8 days
- Total size: ~48GB compressed, ~280GB uncompressed
- Real production cluster data from Alibaba
- Includes: machine events, container workloads, batch jobs

Note: Requires completing a short survey to get download links.
Survey: http://alibabadeveloper.mikecrm.com/BdJtacN
Contact: alibaba-clusterdata@list.alibaba-inc.com
"""

import argparse
from pathlib import Path

DOWNLOAD_INSTRUCTIONS = """
================================================================================
ALIBABA CLUSTER TRACE 2018 - DOWNLOAD INSTRUCTIONS
================================================================================

The Alibaba dataset requires registration before download.

Step 1: Visit the official repository
    https://github.com/alibaba/clusterdata

Step 2: Complete the survey
    Survey link: http://alibabadeveloper.mikecrm.com/BdJtacN
    Alternative: Email alibaba-clusterdata@list.alibaba-inc.com

Step 3: Download using provided script (fetchData.sh) or manual download:
    - machine_meta.tar.gz (~50MB)
    - machine_usage.tar.gz (largest - contains time-series metrics)
    - container_meta.tar.gz
    - container_usage.tar.gz
    - batch_instance.tar.gz (~20GB)
    - batch_task.tar.gz (~10GB - includes DAG task dependencies)

Total dataset: ~48GB compressed, ~280GB uncompressed

Step 4: Download the files to: {output_dir}

Step 5: Extract them:
    cd {output_dir}
    tar -xzf machine_meta.tar.gz
    tar -xzf machine_usage.tar.gz
    tar -xzf batch_instance.tar.gz
    tar -xzf batch_task.tar.gz

Required files for fault detection:
    ✓ machine_usage/ - Essential (CPU, memory, disk, network, CPI, MPKI)
    ✓ machine_meta/  - Essential (machine specs, failure domains, events)
    ✓ container_usage/ - Recommended (container-level metrics)
    ✓ batch_instance/ - Recommended (batch workload instances)
    - batch_task/     - Optional (task DAG dependencies)
    - container_meta/ - Optional (container lifecycle events)

For initial testing, you can download just:
    - machine_meta.tar.gz
    - First 1-2 files from machine_usage/ (sample)

================================================================================
"""


def main():
    parser = argparse.ArgumentParser(
        description='Alibaba Cluster Trace 2018 download helper'
    )
    parser.add_argument('--output', type=str, default='datasets/alibaba-2018',
                       help='Output directory for downloaded files')
    parser.add_argument('--check', action='store_true',
                       help='Check if files are downloaded')

    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.check:
        print("\nChecking for Alibaba dataset files...")
        print(f"Location: {output_dir.absolute()}\n")

        files_to_check = [
            'machine_meta',
            'machine_usage',
            'batch_instance',
            'batch_task'
        ]

        found = []
        missing = []

        for file_name in files_to_check:
            dir_path = output_dir / file_name
            if dir_path.exists() and any(dir_path.iterdir()):
                found.append(file_name)
                print(f"  ✓ Found: {file_name}/")
            else:
                missing.append(file_name)
                print(f"  ✗ Missing: {file_name}/")

        if len(found) >= 2:
            print(f"\n✅ Found {len(found)} dataset(s). Ready to parse!")
            print("\nNext step:")
            print(f"  python parse_alibaba_2018.py --input {output_dir}")
        else:
            print(f"\n⚠ Missing required datasets.")
            print(DOWNLOAD_INSTRUCTIONS.format(output_dir=output_dir.absolute()))

    else:
        print(DOWNLOAD_INSTRUCTIONS.format(output_dir=output_dir.absolute()))

        # Create README
        readme_path = output_dir / 'DOWNLOAD_INSTRUCTIONS.txt'
        readme_path.write_text(DOWNLOAD_INSTRUCTIONS.format(
            output_dir=output_dir.absolute()
        ))
        print(f"\n✓ Instructions saved to: {readme_path}")


if __name__ == '__main__':
    main()
