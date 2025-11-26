import re
from vcd import VCDWriter

# Hardcoded file names
STIL_FILE = "sample.stil"
VCD_FILE = "example.vcd"
TIMESTEP = 10  # time per vector in ns

def parse_signals(stil_text):
    signals = []
    for m in re.finditer(r'SIGNALS\s*\(\s*([^)]+)\)', stil_text, re.IGNORECASE):
        inner = m.group(1)
        parts = re.split(r'[,\s]+', inner.strip())
        for p in parts:
            if p:
                signals.append(p.strip(',;'))
    return signals

def parse_vectors(stil_text):
    vectors = []
    for m in re.finditer(r'VECTOR\s*\(\s*([^)]+)\)', stil_text, re.IGNORECASE | re.DOTALL):
        inner = m.group(1)
        for line in inner.splitlines():
            line = line.strip()
            if not line or line.startswith('!'):
                continue
            tokens = re.split(r'[\s,]+', line)
            vec = [t.upper() if t else 'X' for t in tokens]
            vectors.append(vec)
    return vectors

def stil_to_vcd():
    with open(STIL_FILE, 'r') as f:
        text = f.read()

    signals = parse_signals(text)
    vectors = parse_vectors(text)

    if not signals:
        raise ValueError("No signals found in STIL file")
    if not vectors:
        raise ValueError("No vectors found in STIL file")

    with open(VCD_FILE, 'w') as f, VCDWriter(f, timescale='1ns', date='today') as writer:
        sig_vars = {s: writer.register_var('top', s, 'wire', size=1) for s in signals}

        time = 0
        for vec in vectors:
            for i, sig in enumerate(signals):
                val = vec[i] if i < len(vec) else 'X'
                if val not in ('0','1','X','Z','x','z'):
                    val = 'X'
                writer.change(sig_vars[sig], time, val)
            time += TIMESTEP

if __name__ == '__main__':
    stil_to_vcd()
    print(f"Converted {STIL_FILE} -> {VCD_FILE}")
