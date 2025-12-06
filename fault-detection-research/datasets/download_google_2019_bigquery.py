#!/usr/bin/env python3
"""
Download Google Cluster Trace 2019 (ClusterData2019) via BigQuery.
Official repository: https://github.com/google/cluster-data
Documentation: https://github.com/google/cluster-data/blob/master/ClusterData2019.md

Google ClusterData 2019 characteristics:
- 8 different Borg cells from May 2019
- ~2.4 TiB compressed
- Hosted exclusively on Google BigQuery
- Includes CPU usage histograms, alloc sets, job-parent relationships

Requirements:
- Google Cloud account with BigQuery API enabled
- google-cloud-bigquery Python package
- Appropriate permissions and billing setup

Usage:
    python download_google_2019_bigquery.py --cell a --days 1 --sample
    python download_google_2019_bigquery.py --cell a --days 7 --full
"""

import argparse
import sys
from pathlib import Path

try:
    from google.cloud import bigquery
    from google.oauth2 import service_account
except ImportError:
    print("ERROR: google-cloud-bigquery not installed!")
    print("\nInstall with:")
    print("  pip install google-cloud-bigquery google-auth")
    sys.exit(1)

# BigQuery dataset information
# Source: https://github.com/google/cluster-data/blob/master/ClusterData2019.md
PROJECT_ID = "google.com:clusterdata-v3"
DATASET_ID = "clusterdata_2019_{cell}"  # cell = a, b, c, d, e, f, g, h

# Available tables in ClusterData 2019
TABLES = {
    'instance_events': 'Instance lifecycle events (submit, schedule, evict, etc.)',
    'instance_usage': 'Instance resource usage with CPU histograms',
    'collection_events': 'Collection (job/alloc_set) lifecycle events',
    'machine_events': 'Machine lifecycle events',
    'machine_attributes': 'Machine attribute changes over time'
}

# Recommended queries for fault detection
FAULT_DETECTION_QUERIES = {
    'instance_failures': """
        SELECT
            time,
            collection_id,
            instance_index,
            machine_id,
            type,
            priority,
            scheduling_class
        FROM `{project}.{dataset}.instance_events`
        WHERE type IN (3, 4, 5)  -- EVICT=3, FAIL=4, FINISH=5
            AND time >= {start_time}
            AND time < {end_time}
        ORDER BY time
        LIMIT {limit}
    """,

    'machine_removals': """
        SELECT
            time,
            machine_id,
            type,
            capacity.cpus as cpu_capacity,
            capacity.memory as mem_capacity
        FROM `{project}.{dataset}.machine_events`
        WHERE type = 1  -- REMOVE
            AND time >= {start_time}
            AND time < {end_time}
        ORDER BY time
        LIMIT {limit}
    """,

    'instance_usage': """
        SELECT
            start_time,
            end_time,
            collection_id,
            instance_index,
            machine_id,
            average_usage.cpus as cpu_avg,
            average_usage.memory as mem_avg,
            maximum_usage.cpus as cpu_max,
            maximum_usage.memory as mem_max,
            sample_rate
        FROM `{project}.{dataset}.instance_usage`
        WHERE start_time >= {start_time}
            AND start_time < {end_time}
        ORDER BY start_time
        LIMIT {limit}
    """
}


class GoogleBigQueryDownloader:
    def __init__(self, cell: str, credentials_path: str = None):
        """Initialize BigQuery client."""
        self.cell = cell
        self.project_id = PROJECT_ID
        self.dataset_id = DATASET_ID.format(cell=cell)

        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
            self.client = bigquery.Client(
                credentials=credentials,
                project=credentials.project_id
            )
        else:
            # Use default credentials
            self.client = bigquery.Client()

        print(f"✓ Connected to BigQuery")
        print(f"  Project: {self.project_id}")
        print(f"  Dataset: {self.dataset_id}")

    def query_instance_events(self, start_time: int, end_time: int, limit: int = 100000):
        """Query instance lifecycle events."""
        print(f"\nQuerying instance_events...")

        query = FAULT_DETECTION_QUERIES['instance_failures'].format(
            project=self.project_id,
            dataset=self.dataset_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

        query_job = self.client.query(query)
        results = query_job.result()

        rows = list(results)
        print(f"  ✓ Retrieved {len(rows)} events")
        return rows

    def query_machine_events(self, start_time: int, end_time: int, limit: int = 100000):
        """Query machine lifecycle events."""
        print(f"\nQuerying machine_events...")

        query = FAULT_DETECTION_QUERIES['machine_removals'].format(
            project=self.project_id,
            dataset=self.dataset_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

        query_job = self.client.query(query)
        results = query_job.result()

        rows = list(results)
        print(f"  ✓ Retrieved {len(rows)} events")
        return rows

    def query_instance_usage(self, start_time: int, end_time: int, limit: int = 100000):
        """Query instance resource usage."""
        print(f"\nQuerying instance_usage...")

        query = FAULT_DETECTION_QUERIES['instance_usage'].format(
            project=self.project_id,
            dataset=self.dataset_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

        query_job = self.client.query(query)
        results = query_job.result()

        rows = list(results)
        print(f"  ✓ Retrieved {len(rows)} usage records")
        return rows

    def export_to_csv(self, rows, output_file: Path, headers: list):
        """Export query results to CSV."""
        import csv

        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for row in rows:
                writer.writerow([row[h] if h in row else '' for h in headers])

        print(f"  ✓ Saved to: {output_file}")

    def download_sample(self, output_dir: Path, days: int = 1):
        """Download sample data for fault detection."""
        print(f"\nDownloading {days}-day sample from cell {self.cell}...")

        # Time range (ClusterData 2019 uses microseconds since epoch)
        # May 2019: start from May 1, 2019 00:00:00 UTC
        start_time = 1556668800000000  # May 1, 2019 00:00:00 UTC in microseconds
        end_time = start_time + (days * 24 * 3600 * 1000000)  # Add days in microseconds

        output_dir.mkdir(parents=True, exist_ok=True)

        # Query instance failures
        instance_events = self.query_instance_events(start_time, end_time, limit=50000)
        self.export_to_csv(
            instance_events,
            output_dir / 'instance_failures.csv',
            ['time', 'collection_id', 'instance_index', 'machine_id', 'type', 'priority', 'scheduling_class']
        )

        # Query machine removals
        machine_events = self.query_machine_events(start_time, end_time, limit=10000)
        self.export_to_csv(
            machine_events,
            output_dir / 'machine_removals.csv',
            ['time', 'machine_id', 'type', 'cpu_capacity', 'mem_capacity']
        )

        # Query instance usage
        instance_usage = self.query_instance_usage(start_time, end_time, limit=100000)
        self.export_to_csv(
            instance_usage,
            output_dir / 'instance_usage.csv',
            ['start_time', 'end_time', 'collection_id', 'instance_index', 'machine_id',
             'cpu_avg', 'mem_avg', 'cpu_max', 'mem_max', 'sample_rate']
        )

        print(f"\n✅ Sample data downloaded to: {output_dir.absolute()}")


def print_setup_instructions():
    """Print setup instructions for BigQuery access."""
    print("""
================================================================================
GOOGLE CLUSTER DATA 2019 - BIGQUERY SETUP
================================================================================

ClusterData 2019 is hosted exclusively on Google BigQuery.

Prerequisites:
1. Google Cloud account
2. Enable BigQuery API
3. Set up authentication

Setup Steps:

1. Create Google Cloud Project (if you don't have one)
   https://console.cloud.google.com/projectcreate

2. Enable BigQuery API
   https://console.cloud.google.com/apis/library/bigquery.googleapis.com

3. Install Google Cloud SDK (for authentication)
   macOS:   brew install google-cloud-sdk
   Linux:   curl https://sdk.cloud.google.com | bash
   Windows: https://cloud.google.com/sdk/docs/install

4. Authenticate
   gcloud auth application-default login

5. Install Python package
   pip install google-cloud-bigquery google-auth

6. Run this script
   python download_google_2019_bigquery.py --cell a --days 1 --sample

Available Cells: a, b, c, d, e, f, g, h (8 different Borg cells)

Billing Notes:
- BigQuery charges for data scanned (~$5 per TB)
- Sample queries cost pennies to dollars
- Use --sample mode to minimize costs
- Consider using BigQuery free tier (1 TB/month free)

Documentation:
https://github.com/google/cluster-data/blob/master/ClusterData2019.md

================================================================================
""")


def main():
    parser = argparse.ArgumentParser(
        description='Download Google Cluster Trace 2019 from BigQuery'
    )
    parser.add_argument('--cell', type=str, choices=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'],
                       help='Borg cell identifier (a-h)')
    parser.add_argument('--days', type=int, default=1,
                       help='Number of days to download (default: 1)')
    parser.add_argument('--sample', action='store_true',
                       help='Download sample data (50K events)')
    parser.add_argument('--credentials', type=str,
                       help='Path to service account JSON credentials (optional)')
    parser.add_argument('--output', type=str, default='google-2019',
                       help='Output directory')
    parser.add_argument('--setup', action='store_true',
                       help='Show setup instructions')

    args = parser.parse_args()

    if args.setup or not args.cell:
        print_setup_instructions()
        if not args.cell:
            sys.exit(0)

    print("="*80)
    print("GOOGLE CLUSTER DATA 2019 (BIGQUERY)")
    print("="*80)

    try:
        downloader = GoogleBigQueryDownloader(
            cell=args.cell,
            credentials_path=args.credentials
        )

        output_dir = Path(args.output) / f'cell-{args.cell}'
        downloader.download_sample(output_dir, days=args.days)

        print("\nNext steps:")
        print(f"  1. Parse the downloaded data")
        print(f"  2. Generate ML features")
        print(f"  3. Train fault detection models")

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("\nRun with --setup flag for instructions:")
        print("  python download_google_2019_bigquery.py --setup")
        sys.exit(1)


if __name__ == '__main__':
    main()
