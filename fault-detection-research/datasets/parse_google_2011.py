#!/usr/bin/env python3
"""
Parse Google Cluster Trace 2011 and transform to CloudSim-compatible format.

Implements the exact schema mappings from the official documentation:
https://github.com/google/cluster-data/blob/master/ClusterData2011_2.md
"""

import argparse
import gzip
import pandas as pd
import numpy as np
from pathlib import Path
import json
from tqdm import tqdm

# Official Google 2011 schemas (from format documentation)
MACHINE_EVENTS_SCHEMA = [
    'timestamp', 'machine_id', 'event_type', 'platform_id',
    'cpu_capacity', 'memory_capacity'
]

TASK_EVENTS_SCHEMA = [
    'timestamp', 'missing_info', 'job_id', 'task_index', 'machine_id',
    'event_type', 'user', 'scheduling_class', 'priority',
    'cpu_request', 'memory_request', 'disk_request', 'different_machine'
]

TASK_USAGE_SCHEMA = [
    'start_time', 'end_time', 'job_id', 'task_index', 'machine_id',
    'cpu_rate', 'canonical_memory_usage', 'assigned_memory',
    'unmapped_page_cache', 'total_page_cache', 'max_memory_usage',
    'disk_io_time', 'local_disk_space_usage', 'max_cpu_rate',
    'max_disk_io_time', 'cycles_per_instruction',
    'memory_accesses_per_instruction', 'sample_portion', 'aggregation_type',
    'sampled_cpu_usage'
]

# Event type mappings
MACHINE_EVENT_TYPES = {
    0: 'ADD',
    1: 'REMOVE',
    2: 'UPDATE'
}

TASK_EVENT_TYPES = {
    0: 'SUBMIT',
    1: 'SCHEDULE',
    2: 'EVICT',
    3: 'FAIL',
    4: 'FINISH',
    5: 'KILL',
    6: 'LOST',
    7: 'UPDATE_PENDING',
    8: 'UPDATE_RUNNING'
}


class GoogleTraceParser:
    """Parser for Google Cluster Trace 2011."""

    def __init__(self, input_dir, output_dir):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            'machines': 0,
            'tasks': 0,
            'usage_records': 0,
            'machine_failures': 0,
            'task_failures': 0
        }

    def parse_machine_events(self):
        """Parse machine_events/*.csv.gz files."""
        print("\n[1/3] Parsing machine events...")

        machine_dir = self.input_dir / 'machine_events'
        if not machine_dir.exists():
            print(f"  ✗ Directory not found: {machine_dir}")
            return None

        all_machines = []
        gz_files = list(machine_dir.glob('*.csv.gz'))

        for gz_file in tqdm(gz_files, desc="  Processing files"):
            try:
                df = pd.read_csv(
                    gz_file,
                    names=MACHINE_EVENTS_SCHEMA,
                    compression='gzip'
                )
                all_machines.append(df)
            except Exception as e:
                print(f"  ✗ Error reading {gz_file.name}: {e}")

        if not all_machines:
            print("  ✗ No machine events found")
            return None

        df_machines = pd.concat(all_machines, ignore_index=True)
        df_machines['event_name'] = df_machines['event_type'].map(MACHINE_EVENT_TYPES)

        # Identify fault events
        df_machines['is_failure'] = df_machines['event_type'].isin([1])  # REMOVE

        self.stats['machines'] = df_machines['machine_id'].nunique()
        self.stats['machine_failures'] = df_machines['is_failure'].sum()

        print(f"  ✓ Parsed {len(df_machines):,} machine events")
        print(f"  ✓ Unique machines: {self.stats['machines']:,}")
        print(f"  ✓ Machine removals: {self.stats['machine_failures']:,}")

        # Save
        output_file = self.output_dir / 'machine_events.parquet'
        df_machines.to_parquet(output_file, index=False)
        print(f"  ✓ Saved: {output_file}")

        return df_machines

    def parse_task_events(self):
        """Parse task_events/*.csv.gz files."""
        print("\n[2/3] Parsing task events...")

        task_dir = self.input_dir / 'task_events'
        if not task_dir.exists():
            print(f"  ✗ Directory not found: {task_dir}")
            return None

        all_tasks = []
        gz_files = list(task_dir.glob('*.csv.gz'))[:10]  # Limit for demo

        for gz_file in tqdm(gz_files, desc="  Processing files"):
            try:
                df = pd.read_csv(
                    gz_file,
                    names=TASK_EVENTS_SCHEMA,
                    compression='gzip'
                )
                all_tasks.append(df)
            except Exception as e:
                print(f"  ✗ Error reading {gz_file.name}: {e}")

        if not all_tasks:
            print("  ✗ No task events found")
            return None

        df_tasks = pd.concat(all_tasks, ignore_index=True)
        df_tasks['event_name'] = df_tasks['event_type'].map(TASK_EVENT_TYPES)

        # Identify fault events
        fault_events = [2, 3, 5, 6]  # EVICT, FAIL, KILL, LOST
        df_tasks['is_failure'] = df_tasks['event_type'].isin(fault_events)

        self.stats['tasks'] = len(df_tasks[df_tasks['event_type'] == 0])  # SUBMITs
        self.stats['task_failures'] = df_tasks['is_failure'].sum()

        print(f"  ✓ Parsed {len(df_tasks):,} task events")
        print(f"  ✓ Task submissions: {self.stats['tasks']:,}")
        print(f"  ✓ Task failures: {self.stats['task_failures']:,}")

        # Save
        output_file = self.output_dir / 'task_events.parquet'
        df_tasks.to_parquet(output_file, index=False)
        print(f"  ✓ Saved: {output_file}")

        return df_tasks

    def parse_task_usage(self):
        """Parse task_usage/*.csv.gz files."""
        print("\n[3/3] Parsing task usage...")

        usage_dir = self.input_dir / 'task_usage'
        if not usage_dir.exists():
            print(f"  ✗ Directory not found: {usage_dir}")
            return None

        all_usage = []
        gz_files = list(usage_dir.glob('*.csv.gz'))[:10]  # Limit for demo

        for gz_file in tqdm(gz_files, desc="  Processing files"):
            try:
                df = pd.read_csv(
                    gz_file,
                    names=TASK_USAGE_SCHEMA,
                    compression='gzip'
                )
                all_usage.append(df)
            except Exception as e:
                print(f"  ✗ Error reading {gz_file.name}: {e}")

        if not all_usage:
            print("  ✗ No usage data found")
            return None

        df_usage = pd.concat(all_usage, ignore_index=True)

        self.stats['usage_records'] = len(df_usage)

        print(f"  ✓ Parsed {len(df_usage):,} usage records")

        # Save
        output_file = self.output_dir / 'task_usage.parquet'
        df_usage.to_parquet(output_file, index=False)
        print(f"  ✓ Saved: {output_file}")

        return df_usage

    def generate_cloudsim_entities(self, df_machines, df_tasks, df_usage):
        """Transform to CloudSim JSON format."""
        print("\n[4/4] Generating CloudSim entities...")

        entities = {
            'hosts': [],
            'vms': [],
            'cloudlets': []
        }

        # Generate Hosts from machines
        print("  Creating hosts...")
        if df_machines is not None:
            # Get latest capacity for each machine
            latest_machines = df_machines.sort_values('timestamp').groupby('machine_id').last()

            for machine_id, row in latest_machines.iterrows():
                if pd.notna(row['cpu_capacity']) and pd.notna(row['memory_capacity']):
                    num_pes = max(1, int(round(row['cpu_capacity'])))
                    ram_mb = int(row['memory_capacity'] * 100000)  # Normalize

                    entities['hosts'].append({
                        'id': int(machine_id),
                        'pesNumber': num_pes,
                        'mipsPerPe': 10000,
                        'ram': ram_mb,
                        'storage': 1000000,
                        'bw': 10000
                    })

        print(f"    ✓ Created {len(entities['hosts'])} hosts")

        # Generate VMs from task requests
        print("  Creating VMs...")
        if df_tasks is not None:
            # Get task submissions with resource requests
            submissions = df_tasks[df_tasks['event_type'] == 0].copy()  # SUBMIT

            for idx, row in submissions.head(1000).iterrows():  # Limit for demo
                if pd.notna(row['cpu_request']) and pd.notna(row['memory_request']):
                    vm_id = int(row['job_id'] * 1000000 + row['task_index'])
                    cpu_pes = max(1, int(round(row['cpu_request'] * 10)))
                    ram_mb = int(row['memory_request'] * 10000)

                    entities['vms'].append({
                        'id': vm_id,
                        'mips': 10000,
                        'pesNumber': cpu_pes,
                        'ram': max(512, ram_mb),
                        'bw': 1000,
                        'size': 10000
                    })

        print(f"    ✓ Created {len(entities['vms'])} VMs")

        # Generate Cloudlets from usage
        print("  Creating cloudlets...")
        if df_usage is not None:
            for idx, row in df_usage.head(1000).iterrows():  # Limit for demo
                if pd.notna(row['cpu_rate']) and pd.notna(row['start_time']):
                    cloudlet_id = int(row['job_id'] * 1000000 + row['task_index'])
                    duration = (row['end_time'] - row['start_time']) / 1e6  # microsec to sec
                    length = int(row['cpu_rate'] * duration * 10000)

                    entities['cloudlets'].append({
                        'id': cloudlet_id,
                        'length': max(1000, length),
                        'pesNumber': 1,
                        'submitTime': row['start_time'] / 1e6  # To seconds
                    })

        print(f"    ✓ Created {len(entities['cloudlets'])} cloudlets")

        # Save JSON
        json_file = self.output_dir / 'cloudsim_scenario.json'
        with open(json_file, 'w') as f:
            json.dump(entities, f, indent=2)

        print(f"  ✓ Saved: {json_file}")

        return entities

    def print_summary(self):
        """Print parsing summary."""
        print("\n" + "="*80)
        print("PARSING SUMMARY")
        print("="*80)
        print(f"  Unique machines:        {self.stats['machines']:,}")
        print(f"  Task submissions:       {self.stats['tasks']:,}")
        print(f"  Usage records:          {self.stats['usage_records']:,}")
        print(f"  Machine removals:       {self.stats['machine_failures']:,}")
        print(f"  Task failures:          {self.stats['task_failures']:,}")
        print(f"\n  Fault rate:             {100*self.stats['task_failures']/max(1,self.stats['tasks']):.2f}%")
        print("="*80)


def main():
    parser = argparse.ArgumentParser(
        description='Parse Google Cluster Trace 2011'
    )
    parser.add_argument('--input', required=True,
                       help='Input directory with downloaded data')
    parser.add_argument('--output', default='processed/google-2011',
                       help='Output directory for parsed data')

    args = parser.parse_args()

    print("="*80)
    print("GOOGLE CLUSTER TRACE 2011 PARSER")
    print("="*80)

    parser_obj = GoogleTraceParser(args.input, args.output)

    # Parse all files
    df_machines = parser_obj.parse_machine_events()
    df_tasks = parser_obj.parse_task_events()
    df_usage = parser_obj.parse_task_usage()

    # Generate CloudSim entities
    if any([df_machines is not None, df_tasks is not None, df_usage is not None]):
        parser_obj.generate_cloudsim_entities(df_machines, df_tasks, df_usage)

    # Print summary
    parser_obj.print_summary()

    print(f"\n✅ Parsing complete! Output: {args.output}")


if __name__ == '__main__':
    main()
