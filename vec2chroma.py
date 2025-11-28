import os
import sys

author = "Juneth Viktor Ellon Moreno"
sub_script_ver = "0.01"

def extract_vec_data(vec_file, num_pins=1):
    vector_lines = []
    current_comment = ""
    first_line_of_section = True
    first_vector_line = True

    with open(vec_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#'):
                current_comment = line[1:].strip()
                first_line_of_section = True
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            data = parts[1]

            if first_line_of_section:
                if current_comment and first_vector_line:
                    formatted = f"   *{data}*;   TS1;//{current_comment}"
                    first_vector_line = False
                else:
                    formatted = f"   *{data}*;      //{current_comment}" if current_comment else f"   *{data}*;"
                first_line_of_section = False
            else:
                formatted = f"   *{data}*;      //{current_comment}" if current_comment else f"   *{data}*;"

            vector_lines.append(formatted)
            current_comment = ""

    if vector_lines:
        last_vector = vector_lines[-1]
        stop_vector = last_vector.replace(";", "STOP  ;")
        vector_lines[-1] = stop_vector
        dummy_vector = f"   *{'X' * num_pins}*   ; // extra blank vector"
        vector_lines.append(dummy_vector)

    return "\n".join(vector_lines)

def read_cmf_file(cmf_file):
    pins = []
    try:
        with open(cmf_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(',')
                if len(parts) < 4:
                    continue
                pin_name, _, _, status = parts
                if status.strip().upper() == "USE":
                    pins.append(pin_name.strip())
    except FileNotFoundError:
        print(f"ERROR: CMF file '{cmf_file}' not found!")
        return ""

    if not pins:
        print("WARNING: No pins with 'USE' found in CMF file.")

    pins.reverse()
    pin_list = ','.join(pins)
    print(f"Collected pins: {pin_list}")
    return pin_list

def fill_template(template_file, output_file, vector_data, script_ver="1.0",
                  dec_file="DEC_FILE.DEC", pin_channels="PIN_CHANNELS",
                  pattern_name="PATTERN"):
    with open(template_file, 'r') as f:
        template = f.read()

    template = template.replace("<script_ver>", script_ver)
    template = template.replace("<DEC_File>", dec_file)
    template = template.replace("<PIN_CHANNELS>", pin_channels)
    template = template.replace("<PATTERN_NAME>", pattern_name)
    template = template.replace("<VECTOR>", vector_data)

    with open(output_file, 'w') as f:
        f.write(template)

    print(f"Output written to {output_file}")

def convert_vec_file(vec_file, cmf_file, dec_file, template_file, file_extension, script_ver=sub_script_ver):
    pin_channels = read_cmf_file(cmf_file)
    num_pins = len(pin_channels.split(',')) if pin_channels else 1
    vector_data = extract_vec_data(vec_file, num_pins=num_pins)

    base_name = os.path.splitext(os.path.basename(vec_file))[0]
    output_file = os.path.join(os.path.dirname(vec_file), f"{base_name}{file_extension}")

    fill_template(template_file, output_file, vector_data,
                  script_ver=script_ver,
                  dec_file=dec_file,
                  pin_channels=pin_channels,
                  pattern_name=base_name)

if __name__ == "__main__":
    print("#############################################################")
    print("#\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t#")
    print("#\t\t\t\t\t\tVektorConverter\t\t\t\t\t\t#")
    print(f"#\t\t\t\t\t\tvec2chroma {sub_script_ver}\t\t\t\t\t\t#")
    print(f"#\t\t\t\t\tby: {author}\t\t\t#")
    print(f"#\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t#")
    print("##############################################################")

    # Strip quotes and spaces from user input
    vec_input = input("Enter .vec file or directory: ").strip().strip('"').strip("'")
    vec_input = os.path.abspath(vec_input)
    # Ask for DEC file
    dec_file_input = input("Enter common DEC file path: ").strip().strip('"').strip("'")
    dec_file_name = os.path.basename(dec_file_input)  # get only file name
    dec_file = f"./{dec_file_name}"  # prepend './' to make it relative

    ATE = input("Enter ATE (J750,C3380,C3850): ").strip().upper()
    if ATE == "J750":
        template_file = "J750_pat_template"  # path to J750 template
        file_extension = ".atp"
    elif ATE in ["C3380", "C3850"]:
        template_file = "Chroma_pat_template"  # path to Chroma template
        file_extension = ".pat"
    else:
        print("ERROR: ATE must be J750, C3380, or C3850.")
        sys.exit(1)

    if os.path.isfile(vec_input) and vec_input.lower().endswith('.vec'):
        cmf_file = os.path.splitext(vec_input)[0] + ".cmf"
        if not os.path.exists(cmf_file):
            print(f"ERROR: CMF file '{cmf_file}' not found.")
        else:
            convert_vec_file(vec_input, cmf_file, dec_file, template_file, file_extension)
    elif os.path.isdir(vec_input):
        vec_files = [f for f in os.listdir(vec_input) if f.lower().endswith('.vec')]
        if not vec_files:
            print(f"ERROR: No .vec files found in directory '{vec_input}'")
        else:
            for file_name in vec_files:
                vec_file_path = os.path.join(vec_input, file_name)
                cmf_file = os.path.splitext(vec_file_path)[0] + ".cmf"
                if not os.path.exists(cmf_file):
                    print(f"WARNING: CMF file '{cmf_file}' not found. Skipping '{vec_file_path}'")
                    continue
                convert_vec_file(vec_file_path, cmf_file, dec_file, template_file, file_extension)
    else:
        print(f"ERROR: Input path '{vec_input}' is not a file or directory.")
