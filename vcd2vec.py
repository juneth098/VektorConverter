import re
import datetime

VALUE_MAP = {
    '1': '1',
    '0': '0',
    'x': 'X', 'X': 'X',
    'z': 'X', 'Z': 'X',
    'h': '1', 'H': '1',
    'l': '0', 'L': '0'
}


def parse_header_info(filename):
    date = ""
    version = ""
    timescale = ""
    csum = ""

    in_block = None

    with open(filename, "r") as f:
        for line in f:
            stripped = line.strip()

            # Handle block starts
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
                # format: $comment Csum: 1 aaaaaaaa $end
                m = re.search(r"Csum:\s*(.+)\s*\$end", stripped)
                if m:
                    csum = m.group(1)
                continue

            # Handle block content
            if in_block == "date" and stripped != "$end":
                date = stripped
            elif in_block == "version" and stripped != "$end":
                version = stripped
            elif in_block == "timescale" and stripped != "$end":
                timescale = stripped

            # Block end
            if stripped == "$end":
                in_block = None

            # Stop reading header after definitions
            if stripped == "$enddefinitions":
                break

    return date, version, timescale, csum


def parse_vcd(filename):
    symbols = []          # maintain order: [(symbol, pinname)]
    sym_to_index = {}     # symbol -> index
    value_now = {}        # symbol -> last known value
    timed_changes = {}    # time -> list of (symbol, val)

    time = 0
    in_dump = False

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()

            # -------------------------------------------
            # Parse pin header
            # -------------------------------------------
            if line.startswith("$var"):
                parts = line.split()
                symbol = parts[3]
                pin = parts[4]
                sym_to_index[symbol] = len(symbols)
                symbols.append((symbol, pin))
                continue

            # -------------------------------------------
            # Time marker
            # -------------------------------------------
            if line.startswith("#"):
                time = int(line[1:])
                if time not in timed_changes:
                    timed_changes[time] = []
                in_dump = False
                continue

            # -------------------------------------------
            # Dumpvars
            # -------------------------------------------
            if line == "$dumpvars":
                in_dump = True
                if 0 not in timed_changes:
                    timed_changes[0] = []
                continue

            if line == "$end" and in_dump:
                in_dump = False
                continue

            # -------------------------------------------
            # Value change
            # -------------------------------------------
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

    target_times = []
    n = 1
    while n * interval <= max_time:
        target_times.append(n * interval)
        n += 1

    # Build cumulative state
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


def main():
    vcd_file = input("Enter VCD file path: ").strip()
    interval = int(input("Enter timing interval (e.g. 41665): ").strip())
    # Output filename: remove the input extension
    if "." in vcd_file:
        out_file = vcd_file.rsplit(".", 1)[0] + ".vec"
    else:
        out_file = vcd_file + ".vec"

    # Extract header info
    date, version, timescale, csum = parse_header_info(vcd_file)

    symbols, timed_changes = parse_vcd(vcd_file)

    # Resolve initial state from #0
    init_state = {sym: "X" for sym, _ in symbols}
    for sym, val in timed_changes.get(0, []):
        init_state[sym] = val

    # Generate interval vectors
    vec_rows = build_state_at_times(symbols, timed_changes, interval)

    # Frequency: F = 1 / (interval * timescale)
    # timescale is like "1ps"
    ts_num = int(re.match(r"(\d+)", timescale).group(1))
    freq = int(1e12 / (interval * ts_num))  # In Hz

    # Write output file
    with open(out_file, "w") as f:
        f.write("########################################################\n")
        f.write("# Generated vec\n")
        f.write(f"# VCD : {vcd_file}\n")
        f.write(f"# Date {date}\n")
        f.write(f"# Version: {version}\n")
        f.write(f"# Timescale: {timescale}\n")
        f.write(f"# Csum: {csum}\n")
        f.write("#\n")
        f.write(f"# User Input Timing : {interval}x{timescale}\n")
        f.write(f"# Calculated Frequency : {freq} Hz\n")
        f.write("########################################################\n")

        # #0 row
        row0 = "".join(init_state[sym] for sym, _ in symbols)
        f.write("#0\n")
        f.write("0 " + row0 + "\n")

        # timed rows
        idx = 1
        for t, row in vec_rows:
            f.write(f"#{t}\n")
            f.write(f"{idx} {row}\n")
            idx += 1

    print("Output written:", out_file)


if __name__ == "__main__":
    main()
