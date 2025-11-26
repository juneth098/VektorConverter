# vec_to_template_with_cmf.py

def extract_vec_data(vec_file):
    """Extracts vector data from .vec file and formats it with TS1 and ';'."""
    with open(vec_file, 'r') as f:
        lines = f.readlines()

    vector_lines = []
    current_comment = ""
    first_line_of_section = True
    first_vector_line = True

    for line in lines:
        line = line.strip()
        if not line:
            continue  # skip empty lines

        if line.startswith('#'):
            current_comment = line[1:].strip()
            first_line_of_section = True
            continue

        parts = line.split()
        if len(parts) < 2:
            continue

        data = parts[1]

        # Build formatted line
        if first_line_of_section:
            if current_comment and first_vector_line:
                formatted = f"\t*{data}*;\tTS1;//{current_comment}"
                first_vector_line = False
            elif current_comment and not first_vector_line:
                formatted = f"\t*{data}*;\t\t//{current_comment}"
            else:
                formatted = f"\t*{data}*;\t\t//{current_comment}"
            first_line_of_section = False
        else:
            if current_comment:
                formatted = f"\t*{data}*;\t\t//{current_comment}"
            else:
                formatted = f"\t*{data}*;"

        vector_lines.append(formatted)
        current_comment = ""  # only append comment to the first line

    return "\n".join(vector_lines)


def read_cmf_file(cmf_file):
    """
    Reads a CMF or DEC file and extracts all pins with 'USE'.
    Returns a comma-separated string of pin names.
    """
    pins = []
    try:
        with open(cmf_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(',')
                if len(parts) < 4:
                    continue  # skip lines that don't have at least 4 columns
                pin_name, _, _, status = parts
                if status.strip().upper() == "USE":  # case-insensitive
                    pins.append(pin_name.strip())
    except FileNotFoundError:
        print(f"ERROR: CMF/DEC file '{cmf_file}' not found!")
        return ""

    if not pins:
        print("WARNING: No pins with 'USE' found in CMF/DEC file.")

    # Reverse the pin order
    pins.reverse()

    # preserve CMF/DEC order as-is
    pin_list = ','.join(pins)
    print(f"Collected pins: {pin_list}")
    return pin_list


def fill_template(template_file, output_file, vector_data, script_ver="1.0", dec_file="DEC_FILE.DEC",
                  pin_channels="PIN_CHANNELS", pattern_name="PATTERN"):
    """Fill template placeholders and write output."""
    with open(template_file, 'r') as f:
        template = f.read()

    # Replace placeholders
    template = template.replace("<script_ver>", script_ver)
    template = template.replace("<DEC_File>", dec_file)
    template = template.replace("<PIN_CHANNELS>", pin_channels)  # replaced with CMF/DEC pins
    template = template.replace("<PATTERN_NAME>", pattern_name)
    template = template.replace("<VECTOR>", vector_data)

    # Write output
    with open(output_file, 'w') as f:
        f.write(template)

    print(f"Output written to {output_file}")


if __name__ == "__main__":
    vec_file = "tb_utmi_atpg_atpg_ft232h.vec"       # input vec file
    cmf_file = "FT4232H.cmf"                   # CMF/DEC file
    template_file = "Chroma_pat_template"           # template file
    output_file = "tb_utmi_atpg_atpg_ft232h.pat"   # final output file

    # Extract vector data
    vector_data = extract_vec_data(vec_file)

    # Extract pin channels from CMF/DEC
    pin_channels = read_cmf_file(cmf_file)

    # Fill template with extracted vector data and pins
    fill_template(template_file, output_file, vector_data,
                  script_ver="0.01",
                  dec_file=cmf_file,
                  pin_channels=pin_channels,
                  pattern_name="tb_utmi_atpg_atpg_ft232h")
