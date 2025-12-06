#!/usr/bin/env python3
"""
Parse Alibaba Cluster Trace 2018 dataset into structured format.
Official repository: https://github.com/alibaba/clusterdata
Schema documentation: https://github.com/alibaba/clusterdata/blob/master/cluster-trace-v2018/schema.txt

Processes:
1. machine_meta.csv - Machine metadata and lifecycle events
2. machine_usage.csv - Machine resource utilization time-series
3. container_meta.csv - Container metadata and lifecycle events
4. container_usage.csv - Container resource utilization time-series
5. batch_instance.csv - Batch workload instance information
6. batch_task.csv - Batch workload task information with DAG dependencies

Outputs:
- Parsed CSV files with standardized schemas
- CloudSim JSON entities (Hosts, VMs, Cloudlets)
- Fault event timeline for ML labeling
"""

import argparse
import csv
import gzip
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List
import sys

# Official Alibaba 2018 Schemas from GitHub repository
# Source: https://github.com/alibaba/clusterdata/blob/master/cluster-trace-v2018/schema.txt

MACHINE_META_SCHEMA = [
    'machine_id',           # string: unique machine identifier
    'time_stamp',           # bigint: timestamp in seconds
    'failure_domain_1',     # bigint: container failure domain level 1
    'failure_domain_2',     # string: container failure domain level 2
    'cpu_num',              # bigint: number of CPUs
    'mem_size',             # bigint: normalized memory [0, 100]
    'status'                # string: machine status
]

MACHINE_USAGE_SCHEMA = [
    'machine_id',           # string: unique machine identifier
    'time_stamp',           # double: timestamp in seconds
    'cpu_util_percent',     # bigint: CPU utilization [0, 100]
    'mem_util_percent',     # bigint: memory utilization [0, 100]
    'mem_gps',              # double: normalized memory bandwidth [0, 100]
    'mkpi',                 # bigint: misses per thousand instructions
    'net_in',               # double: normalized incoming network [0, 100]
    'net_out',              # double: normalized outgoing network [0, 100]
    'disk_io_percent'       # double: disk I/O percentage [0, 100], -1/101 = invalid
]

CONTAINER_META_SCHEMA = [
    'container_id',         # string: unique container identifier
    'machine_id',           # string: host machine identifier
    'time_stamp',           # bigint: timestamp in seconds
    'app_du',               # string: application deploy unit group
    'status',               # string: container status
    'cpu_request',          # bigint: CPU request (100 = 1 core)
    'cpu_limit',            # bigint: CPU limit (100 = 1 core)
    'mem_size'              # double: normalized memory [0, 100]
]

CONTAINER_USAGE_SCHEMA = [
    'container_id',         # string: unique container identifier
    'machine_id',           # string: host machine identifier
    'time_stamp',           # double: timestamp in seconds
    'cpu_util_percent',     # bigint: CPU utilization percentage
    'mem_util_percent',     # bigint: memory utilization percentage
    'cpi',                  # double: cycles per instruction
    'mem_gps',              # double: normalized memory bandwidth [0, 100]
    'mpki',                 # bigint: misses per thousand instructions
    'net_in',               # double: normalized incoming network [0, 100]
    'net_out',              # double: normalized outgoing network [0, 100]
    'disk_io_percent'       # double: disk I/O percentage [0, 100]
]

BATCH_INSTANCE_SCHEMA = [
    'instance_name',        # string: instance identifier
    'task_name',            # string: task identifier
    'job_name',             # string: job identifier
    'task_type',            # string: task type
    'status',               # string: instance status
    'start_time',           # bigint: start timestamp in seconds
    'end_time',             # bigint: end timestamp in seconds
    'machine_id',           # string: host machine identifier
    'seq_no',               # bigint: sequence number
    'total_seq_no',         # bigint: total sequences
    'cpu_avg',              # double: average CPU usage
    'cpu_max',              # double: maximum CPU usage
    'mem_avg',              # double: average memory usage
    'mem_max'               # double: maximum memory usage
]

BATCH_TASK_SCHEMA = [
    'task_name',            # string: task identifier (may contain DAG info)
    'instance_num',         # bigint: number of instances
    'job_name',             # string: job identifier
    'task_type',            # string: task type
    'status',               # string: task status
    'start_time',           # bigint: start timestamp in seconds
    'end_time',             # bigint: end timestamp in seconds
    'plan_cpu',             # double: planned CPU
    'plan_mem'              # double: planned memory
]


class AlibabaParser:
    def __init__(self, input_dir: Path, output_dir: Path):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Track entities for CloudSim
        self.machines = {}
        self.containers = {}
        self.batch_instances = []
        self.fault_events = []

    def parse_machine_meta(self):
        """Parse machine metadata and events."""
        print("\n[1/6] Parsing machine_meta.csv...")

        input_file = self.input_dir / 'machine_meta' / 'machine_meta.csv'
        output_file = self.output_dir / 'machine_meta_parsed.csv'

        if not input_file.exists():
            print(f"  ⚠ File not found: {input_file}")
            return

        machine_events = []
        machines_seen = set()

        with open(input_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) != len(MACHINE_META_SCHEMA):
                    continue

                machine_id = row[0]
                time_stamp = float(row[1])
                failure_domain_1 = int(row[2]) if row[2] and row[2] != '' else 0
                failure_domain_2 = row[3]
                cpu_num = int(row[4]) if row[4] and row[4] != '' else 1
                mem_size = float(row[5]) if row[5] and row[5] != '' else 100.0
                status = row[6]

                machine_events.append({
                    'machine_id': machine_id,
                    'time_stamp': time_stamp,
                    'failure_domain_1': failure_domain_1,
                    'failure_domain_2': failure_domain_2,
                    'cpu_num': cpu_num,
                    'mem_size': mem_size,
                    'status': status
                })

                # Track unique machines for CloudSim
                if machine_id not in machines_seen:
                    machines_seen.add(machine_id)
                    self.machines[machine_id] = {
                        'id': machine_id,
                        'cpu_num': cpu_num,
                        'mem_size': mem_size,
                        'failure_domain_1': failure_domain_1,
                        'failure_domain_2': failure_domain_2,
                        'first_seen': time_stamp
                    }

                # Track fault events (machine removals, failures)
                if status in ['shutdown', 'fail', 'error']:
                    self.fault_events.append({
                        'timestamp': time_stamp,
                        'machine_id': machine_id,
                        'event_type': 'machine_' + status,
                        'severity': 'high' if status == 'fail' else 'medium'
                    })

        # Save parsed events
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=MACHINE_META_SCHEMA)
            writer.writeheader()
            writer.writerows(machine_events)

        print(f"  ✓ Parsed {len(machine_events)} machine events")
        print(f"  ✓ Found {len(machines_seen)} unique machines")
        print(f"  ✓ Identified {len([e for e in self.fault_events if 'machine' in e['event_type']])} fault events")
        print(f"  ✓ Saved to: {output_file}")

    def parse_machine_usage(self, sample_rate: int = 1):
        """Parse machine resource usage time-series."""
        print(f"\n[2/6] Parsing machine_usage.csv (sample_rate={sample_rate})...")

        input_dir = self.input_dir / 'machine_usage'
        output_file = self.output_dir / 'machine_usage_parsed.csv'

        if not input_dir.exists():
            print(f"  ⚠ Directory not found: {input_dir}")
            return

        usage_records = []
        files_processed = 0

        for csv_file in sorted(input_dir.glob('*.csv')):
            files_processed += 1
            print(f"  Processing: {csv_file.name}...")

            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if i % sample_rate != 0:
                        continue

                    if len(row) != len(MACHINE_USAGE_SCHEMA):
                        continue

                    machine_id = row[0]
                    time_stamp = float(row[1])
                    cpu_util = int(row[2]) if row[2] and row[2] != '' else 0
                    mem_util = int(row[3]) if row[3] and row[3] != '' else 0
                    mem_gps = float(row[4]) if row[4] and row[4] != '' else 0.0
                    mkpi = int(row[5]) if row[5] and row[5] != '' else 0
                    net_in = float(row[6]) if row[6] and row[6] != '' else 0.0
                    net_out = float(row[7]) if row[7] and row[7] != '' else 0.0
                    disk_io = float(row[8]) if row[8] and row[8] != '' else 0.0

                    # Filter invalid values
                    if disk_io < 0 or disk_io > 100:
                        disk_io = 0.0

                    usage_records.append({
                        'machine_id': machine_id,
                        'time_stamp': time_stamp,
                        'cpu_util_percent': cpu_util,
                        'mem_util_percent': mem_util,
                        'mem_gps': mem_gps,
                        'mkpi': mkpi,
                        'net_in': net_in,
                        'net_out': net_out,
                        'disk_io_percent': disk_io
                    })

        # Save parsed usage
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=MACHINE_USAGE_SCHEMA)
            writer.writeheader()
            writer.writerows(usage_records)

        print(f"  ✓ Processed {files_processed} files")
        print(f"  ✓ Parsed {len(usage_records)} usage records")
        print(f"  ✓ Saved to: {output_file}")

    def parse_container_meta(self):
        """Parse container metadata and events."""
        print("\n[3/6] Parsing container_meta.csv...")

        input_dir = self.input_dir / 'container_meta'
        output_file = self.output_dir / 'container_meta_parsed.csv'

        if not input_dir.exists():
            print(f"  ⚠ Directory not found: {input_dir}")
            return

        container_events = []
        containers_seen = set()

        for csv_file in sorted(input_dir.glob('*.csv')):
            print(f"  Processing: {csv_file.name}...")

            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) != len(CONTAINER_META_SCHEMA):
                        continue

                    container_id = row[0]
                    machine_id = row[1]
                    time_stamp = int(row[2]) if row[2] else 0
                    app_du = row[3]
                    status = row[4]
                    cpu_request = int(row[5]) if row[5] and row[5] != '' else 100
                    cpu_limit = int(row[6]) if row[6] and row[6] != '' else 100
                    mem_size = float(row[7]) if row[7] and row[7] != '' else 10.0

                    container_events.append({
                        'container_id': container_id,
                        'machine_id': machine_id,
                        'time_stamp': time_stamp,
                        'app_du': app_du,
                        'status': status,
                        'cpu_request': cpu_request,
                        'cpu_limit': cpu_limit,
                        'mem_size': mem_size
                    })

                    # Track unique containers
                    if container_id not in containers_seen:
                        containers_seen.add(container_id)
                        self.containers[container_id] = {
                            'id': container_id,
                            'machine_id': machine_id,
                            'cpu_request': cpu_request,
                            'mem_size': mem_size,
                            'app_du': app_du
                        }

        # Save parsed events
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CONTAINER_META_SCHEMA)
            writer.writeheader()
            writer.writerows(container_events)

        print(f"  ✓ Parsed {len(container_events)} container events")
        print(f"  ✓ Found {len(containers_seen)} unique containers")
        print(f"  ✓ Saved to: {output_file}")

    def parse_batch_instance(self):
        """Parse batch workload instance information."""
        print("\n[4/6] Parsing batch_instance.csv...")

        input_dir = self.input_dir / 'batch_instance'
        output_file = self.output_dir / 'batch_instance_parsed.csv'

        if not input_dir.exists():
            print(f"  ⚠ Directory not found: {input_dir}")
            return

        instances = []

        for csv_file in sorted(input_dir.glob('*.csv')):
            print(f"  Processing: {csv_file.name}...")

            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) != len(BATCH_INSTANCE_SCHEMA):
                        continue

                    instance_name = row[0]
                    task_name = row[1]
                    job_name = row[2]
                    task_type = row[3]
                    status = row[4]
                    start_time = int(row[5]) if row[5] else 0
                    end_time = int(row[6]) if row[6] else start_time
                    machine_id = row[7]
                    seq_no = int(row[8]) if row[8] else 0
                    total_seq_no = int(row[9]) if row[9] else 1
                    cpu_avg = float(row[10]) if row[10] and row[10] != '' else 0.0
                    cpu_max = float(row[11]) if row[11] and row[11] != '' else 0.0
                    mem_avg = float(row[12]) if row[12] and row[12] != '' else 0.0
                    mem_max = float(row[13]) if row[13] and row[13] != '' else 0.0

                    instances.append({
                        'instance_name': instance_name,
                        'task_name': task_name,
                        'job_name': job_name,
                        'task_type': task_type,
                        'status': status,
                        'start_time': start_time,
                        'end_time': end_time,
                        'machine_id': machine_id,
                        'seq_no': seq_no,
                        'total_seq_no': total_seq_no,
                        'cpu_avg': cpu_avg,
                        'cpu_max': cpu_max,
                        'mem_avg': mem_avg,
                        'mem_max': mem_max
                    })

                    # Track failures as fault events
                    if status in ['Failed', 'Terminated', 'Cancelled']:
                        self.fault_events.append({
                            'timestamp': end_time,
                            'machine_id': machine_id,
                            'event_type': 'batch_instance_' + status.lower(),
                            'severity': 'high' if status == 'Failed' else 'low',
                            'instance_name': instance_name
                        })

        # Save parsed instances
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=BATCH_INSTANCE_SCHEMA)
            writer.writeheader()
            writer.writerows(instances)

        self.batch_instances = instances
        print(f"  ✓ Parsed {len(instances)} batch instances")
        print(f"  ✓ Saved to: {output_file}")

    def generate_cloudsim_entities(self):
        """Generate CloudSim JSON entities from parsed data."""
        print("\n[5/6] Generating CloudSim entities...")

        entities = {
            'hosts': [],
            'vms': [],
            'cloudlets': []
        }

        # Generate Hosts from machines
        for machine_id, machine in self.machines.items():
            entities['hosts'].append({
                'id': int(machine_id.split('_')[-1]) if '_' in machine_id else hash(machine_id) % 10000,
                'pesNumber': machine['cpu_num'],
                'mipsPerPe': 10000,
                'ram': int(machine['mem_size'] * 1024),  # Convert normalized to MB
                'storage': 1000000,
                'bw': 10000,
                'failureDomain1': machine['failure_domain_1'],
                'failureDomain2': machine['failure_domain_2']
            })

        # Generate VMs from containers
        for i, (container_id, container) in enumerate(self.containers.items()):
            entities['vms'].append({
                'id': i,
                'size': 10000,
                'ram': int(container['mem_size'] * 10),  # Normalized to MB
                'mips': 1000,
                'bw': 1000,
                'pesNumber': max(1, container['cpu_request'] // 100),
                'vmm': 'Xen',
                'hostId': int(container['machine_id'].split('_')[-1]) if '_' in container['machine_id'] else hash(container['machine_id']) % 10000,
                'appDu': container['app_du']
            })

        # Generate Cloudlets from batch instances
        for i, instance in enumerate(self.batch_instances):
            duration = instance['end_time'] - instance['start_time']
            length = int(instance['cpu_avg'] * duration * 1000) if duration > 0 else 10000

            entities['cloudlets'].append({
                'id': i,
                'length': max(1000, length),
                'pesNumber': 1,
                'fileSize': 300,
                'outputSize': 300,
                'submitTime': instance['start_time'],
                'taskType': instance['task_type'],
                'status': instance['status']
            })

        # Save CloudSim JSON
        output_file = self.output_dir / 'cloudsim_entities.json'
        with open(output_file, 'w') as f:
            json.dump(entities, f, indent=2)

        print(f"  ✓ Generated {len(entities['hosts'])} Hosts")
        print(f"  ✓ Generated {len(entities['vms'])} VMs")
        print(f"  ✓ Generated {len(entities['cloudlets'])} Cloudlets")
        print(f"  ✓ Saved to: {output_file}")

    def generate_fault_timeline(self):
        """Generate fault event timeline for ML labeling."""
        print("\n[6/6] Generating fault timeline...")

        # Sort events by timestamp
        self.fault_events.sort(key=lambda x: x['timestamp'])

        output_file = self.output_dir / 'fault_events.json'
        with open(output_file, 'w') as f:
            json.dump(self.fault_events, f, indent=2)

        print(f"  ✓ Identified {len(self.fault_events)} fault events")

        # Print event type breakdown
        event_types = {}
        for event in self.fault_events:
            event_type = event['event_type']
            event_types[event_type] = event_types.get(event_type, 0) + 1

        print("\n  Event type breakdown:")
        for event_type, count in sorted(event_types.items(), key=lambda x: -x[1]):
            print(f"    {event_type}: {count}")

        print(f"\n  ✓ Saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Parse Alibaba Cluster Trace 2018 dataset'
    )
    parser.add_argument('--input', type=str, required=True,
                       help='Input directory with downloaded Alibaba dataset')
    parser.add_argument('--output', type=str, default='alibaba-2018-parsed',
                       help='Output directory for parsed files')
    parser.add_argument('--sample-rate', type=int, default=1,
                       help='Sample rate for machine_usage (1=all, 10=every 10th record)')

    args = parser.parse_args()

    print("="*80)
    print("ALIBABA CLUSTER TRACE 2018 PARSER")
    print("="*80)
    print(f"Input:  {args.input}")
    print(f"Output: {args.output}")
    print(f"Sample rate: {args.sample_rate}")

    alibaba_parser = AlibabaParser(
        input_dir=Path(args.input),
        output_dir=Path(args.output)
    )

    # Parse all datasets
    alibaba_parser.parse_machine_meta()
    alibaba_parser.parse_machine_usage(sample_rate=args.sample_rate)
    alibaba_parser.parse_container_meta()
    alibaba_parser.parse_batch_instance()
    alibaba_parser.generate_cloudsim_entities()
    alibaba_parser.generate_fault_timeline()

    print("\n" + "="*80)
    print("✅ PARSING COMPLETE!")
    print("="*80)
    print(f"\nOutput files in: {Path(args.output).absolute()}")
    print("\nNext steps:")
    print(f"  1. Generate ML features:")
    print(f"     python generate_features_alibaba.py --input {args.output}")
    print(f"  2. Train fault detection models:")
    print(f"     python train_models_demo.py --data {args.output}/ml_features.csv")


if __name__ == '__main__':
    main()
