# Integrating the new filter_paths function into the original script

import subprocess
import re


config = {}
config["lines"] = 100
config["max_depth"] = 7
config["directories_to_analyze"] = ["/"]
config["minChildParentRatio"] = 0.75
config["excludedSubPaths"] = ["pimania/Syncs"]


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
    filtered_data = []

    for parent_size, parent_path in converted_data:
        combined_child_size = 0
        for child_size, child_path in converted_data:
            if child_path.startswith(f"{parent_path}/"):
                combined_child_size += child_size

        if combined_child_size / parent_size < config["minChildParentRatio"]:
            for path in config["excludedSubPaths"]:
                if path not in parent_path:
                    filtered_data.append((str(parent_size) + "B", parent_path))

    return filtered_data


if __name__ == "__main__":
    for directory in config["directories_to_analyze"]:
        print(f"Analyzing disk usage for directory: {directory}")
        disk_usage_data = analyze_disk_usage(directory, config["max_depth"])

        filtered_data = filter_paths(disk_usage_data)

        for size, path in filtered_data:
            size = str(round(int(size.strip("B")) / 1000000000, 2)) + "GB"
            print(f"{size}\t{path}")
