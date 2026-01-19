# vcd2vec.py
# Copyright (c) 2025 Juneth Viktor Ellon Moreno
# All rights reserved
import re
import os
import metadata
from datetime import datetime

author = metadata.author
sub_script_ver = metadata.script_ver

VALUE_MAP = {
    '1': '1',
    '0': '0',
    'x': 'X', 'X': 'X',
    'z': 'X', 'Z': 'X',
    'h': '1', 'H': '1',
    'l': '0', 'L': '0'
}

# ---------------------- CMF Generation ----------------------
def generate_cmf_from_vcd(vcd_file, cmf_file=None):
    pins = []
    with open(vcd_file, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("$var"):
                parts = line.split()
                if len(parts) >= 5:
                    pin_name = " ".join(parts[4:-1])  # handle spaces in pin name
                    pins.append(pin_name)

    if not cmf_file:
        cmf_file = os.path.splitext(vcd_file)[0] + ".cmf"

    with open(cmf_file, "w") as f:
        for idx, pin in enumerate(pins):
            f.write(f"{pin},{idx},T2,USE\n")

    print(f"CMF file generated: {cmf_file}")
    return cmf_file

# ---------------------- VCD Parsing ----------------------
def parse_header_info(filename):
    date = ""
    version = ""
    timescale = ""
    csum = ""

    in_block = None

    with open(filename, "r") as f:
        for line in f:
            stripped = line.strip()

            if stripped == "$date":
                in_block = "date"
                continue
            if stripped == "$version":
                in_block = "version"
                continue
            if stripped == "$timescale":
                in_block = "timescale"
                continue

            if stripped.startswith("$comment") and "Csum" in stripped:
                m = re.search(r"Csum:\s*(.+)\s*\$end", stripped)
                if m:
                    csum = m.group(1)
                continue

            if in_block == "date" and stripped != "$end":
                date = stripped
            elif in_block == "version" and stripped != "$end":
                version = stripped
            elif in_block == "timescale" and stripped != "$end":
                timescale = stripped

            if stripped == "$end":
                in_block = None
            if stripped == "$enddefinitions":
                break

    return date, version, timescale, csum

def parse_vcd(filename):
    symbols = []
    sym_to_index = {}
    value_now = {}
    timed_changes = {}

    time = 0
    in_dump = False

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("$var"):
                parts = line.split()
                symbol = parts[3]
                pin = " ".join(parts[4:-1]) if len(parts) > 5 else parts[4]
                sym_to_index[symbol] = len(symbols)
                symbols.append((symbol, pin))
                continue
            if line.startswith("#"):
                time = int(line[1:])
                if time not in timed_changes:
                    timed_changes[time] = []
                in_dump = False
                continue
            if line == "$dumpvars":
                in_dump = True
                if 0 not in timed_changes:
                    timed_changes[0] = []
                continue
            if line == "$end" and in_dump:
                in_dump = False
                continue
            m = re.match(r"([01xXzZhHlL])(.+)", line)
            if m:
                raw_val, symbol = m.groups()
                symbol = symbol.strip()
                if symbol not in sym_to_index:
                    continue
                val = VALUE_MAP.get(raw_val, "X")
                if in_dump:
                    timed_changes[0].append((symbol, val))
                    value_now[symbol] = val
                else:
                    if value_now.get(symbol) != val:
                        value_now[symbol] = val
                        timed_changes[time].append((symbol, val))
    return symbols, timed_changes

def build_state_at_times(symbols, timed_changes, interval):
    all_times = sorted(timed_changes.keys())
    max_time = max(all_times)
    target_times = [n * interval for n in range(1, max_time // interval + 1)]
    state = {sym: "X" for sym, _ in symbols}
    vec_rows = []

    changes_iter = iter(all_times)
    event_time = next(changes_iter, None)

    for t in target_times:
        while event_time is not None and event_time <= t:
            for sym, val in timed_changes.get(event_time, []):
                state[sym] = val
            event_time = next(changes_iter, None)
        row = "".join(state[sym] for sym, _ in symbols)
        vec_rows.append((t, row))

    return vec_rows

# ---------------------- Export VEC + CMF ----------------------
def convert_vcd_to_vec(vcd_file, interval, vec_file=None, cmf_file=None):
    """Convert a VCD to VEC + CMF. Returns paths of vec and cmf files."""
    if cmf_file is None:
        cmf_file = os.path.splitext(vcd_file)[0] + ".cmf"
    if vec_file is None:
        vec_file = os.path.splitext(vcd_file)[0] + ".vec"

    generate_cmf_from_vcd(vcd_file, cmf_file)
    date, version, timescale, csum = parse_header_info(vcd_file)
    symbols, timed_changes = parse_vcd(vcd_file)

    init_state = {sym: "X" for sym, _ in symbols}
    for sym, val in timed_changes.get(0, []):
        init_state[sym] = val

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    vec_rows = build_state_at_times(symbols, timed_changes, interval)
    ts_num = int(re.match(r"(\d+)", timescale).group(1))
    freq = int(1e12 / (interval * ts_num))
    print("i am here")
    with open(vec_file, "w") as f:
        f.write("########################################################\n")
        f.write(f"# Generated by VektorConverter: vcd2vec v{sub_script_ver}\n")
        f.write(f"# VCD                 : {vcd_file}\n")
        #f.write(f"# Date     : {date}\n")
        #f.write(f"# Version  : {version}\n")
        #f.write(f"# Timescale: {timescale}\n")
        #f.write(f"# Csum     : {csum}\n")
        f.write(f"# User Input Timing   : [{interval}] x [{timescale}]\n")
        f.write(f"# Calculated Frequency: {freq} Hz\n")
        f.write(f"# Timestamp           : {timestamp}\n")
        f.write("########################################################\n")
        row0 = "".join(init_state[sym] for sym, _ in symbols)
        f.write("#0\n0 " + row0 + "\n")
        idx = 1
        for t, row in vec_rows:
            f.write(f"#{t}\n{idx} {row}\n")
            idx += 1

    print("VEC file written:", vec_file)
    print("CMF file written:", cmf_file)
    return vec_file, cmf_file

# ---------------------- Optional CLI ----------------------
if __name__ == "__main__":
    print("#############################################################")
    print("#\t\t\t\t\t\tVektorConverter\t\t\t\t\t\t#")
    print(f"#\t\t\t\t\t\tvcd2vec + cmf v{sub_script_ver}\t\t\t\t\t#")
    print(f"#\t\t\t\t\tby: {author}\t\t\t#")
    print("##############################################################")
    try:
        vcd_file = input("Enter VCD file path: ").strip()
        interval = int(input("Enter timing interval (e.g. 41665): ").strip())
        convert_vcd_to_vec(vcd_file, interval)
    except Exception as e:
        print("Error:", e)
