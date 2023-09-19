# Integrating the new filter_paths function into the original script

import subprocess
import re
import argparse


def execute_command(command):
    return subprocess.run(command, stdout=subprocess.PIPE, text=True, shell=True).stdout


def analyze_disk_usage(directory, max_depth=2):
    output = execute_command(
        f"sudo du -h --max-depth={max_depth} {directory} | sort -hr"
    )
    lines = output.strip().split("\n")
    return lines[: config["lines"]]


def convert_size_to_bytes(size_str):
    size_str = size_str.upper()
    size_num = float(re.match(r"[0-9.]+", size_str).group())
    if "K" in size_str:
        return int(size_num * 1024)
    if "M" in size_str:
        return int(size_num * 1024**2)
    if "G" in size_str:
        return int(size_num * 1024**3)
    if "T" in size_str:
        return int(size_num * 1024**4)
    return int(size_num)


def filter_paths(disk_usage_data):
    # First, create a list of split lines containing exactly two elements
    valid_lines = [
        line.split("\t") for line in disk_usage_data if len(line.split("\t")) == 2
    ]

    # Then, proceed with the existing logic using valid_lines
    converted_data = [(convert_size_to_bytes(size), path) for size, path in valid_lines]
    filtered_data, excludePath = [], False

    for parent_size, parent_path in converted_data:
        combined_child_size = 0
        for child_size, child_path in converted_data:
            if child_path.startswith(f"{parent_path}/"):
                remaining_path = child_path[len(parent_path) + 1 :]
                if remaining_path.count("/") == 0:
                    combined_child_size += child_size

        if combined_child_size / parent_size < config["maxChildParentRatio"]:
            for path in config["excludedSubPaths"]:
                if path in parent_path:
                    excludePath = True
            if not excludePath:
                filtered_data.append((str(parent_size) + "B", parent_path))

        # print(
        #     combined_child_size / parent_size,
        #     parent_path,
        #     config["maxChildParentRatio"],
        #     excludePath,
        # )

    return filtered_data


parser = argparse.ArgumentParser(description="Disk usage analysis script")
parser.add_argument("--l", default=100, type=int)
parser.add_argument("--depth", default=7, type=int)
parser.add_argument("--dir", default="/home/pimania/Syncs/Obsidian", type=str)
parser.add_argument("--sizeRatio", default=0.75, type=float)
parser.add_argument("--excludedPaths", default=[], nargs="+", type=list)

args = parser.parse_args()

config = {
    "lines": args.l,
    "maxDepth": args.depth,
    "directory_to_analyze": args.dir,
    "maxChildParentRatio": args.sizeRatio,
    "excludedSubPaths": args.excludedPaths,
}


if __name__ == "__main__":
    print(f"Analyzing disk usage for directory: {config['directory_to_analyze']}")
    disk_usage_data = analyze_disk_usage(
        config["directory_to_analyze"], config["maxDepth"]
    )

    filtered_data = filter_paths(disk_usage_data)

    for size, path in filtered_data:
        size = str(round(int(size.strip("B")) / 1000000000, 2)) + "GB"
        print(f"{size}\t{path}")
