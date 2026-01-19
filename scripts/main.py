# main.py
import os
from datetime import datetime
import ate2vec
import stil2vec
import vcd2vec
import vec2ate
import metadata

author = metadata.author
sub_script_ver = metadata.script_ver

def run_conversion(file_path, ate_type=None, dec_file=None, interval=None):
    """
    file_path: str, path to input file
    ate_type: str, J750/C3380/C3850, only for vec->ATE conversion
    dec_file: str, only needed for Chroma vec2ate conversion
    interval: int, only for VCD->VEC
    """
    if not os.path.exists(file_path):
        print(f"ERROR: Path '{file_path}' does not exist")
        return

    ext = os.path.splitext(file_path)[1].lower()

    vec_file = None
    cmf_file = None

    # --- ATE input ---
    if ext in [".atp", ".pat"]:
        print(f"Processing {ext} file with ate2vec...")
        vectors = ate2vec.parse_j750_atp_vectors(file_path) if ext == ".atp" else ate2vec.parse_chroma_pat_vectors(file_path)
        pins = ate2vec.parse_j750_pins(file_path) if ext == ".atp" else ate2vec.parse_chroma_pins(file_path)
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        vec_file = os.path.join(os.path.dirname(file_path), base_name + ".vec")
        cmf_file = os.path.join(os.path.dirname(file_path), base_name + ".cmf")
        ate2vec.generate_vec_file(vectors, vec_file, os.path.basename(file_path), date)
        ate2vec.generate_cmf_file(pins, cmf_file)
        print(f"VEC file written: {vec_file}")
        print(f"CMF file written: {cmf_file}")
        print("ate2vec conversion done!")

        # If ate_type is specified, convert vec -> ATE
        if ate_type != "VEC":
            #template_file = "J750_pat_template" if ate_type.upper() == "J750" else "Chroma_pat_template"
            file_ext = ".atp" if ate_type.upper() == "J750" else ".pat"
            print(f"Converting {vec_file} -> {ate_type} using vec2ate...")
            vec2ate.convert_vec_file(vec_file, cmf_file, dec_file or "",
                                     file_extension=file_ext,
                                     ate_type=ate_type.upper(),
                                     script_ver=sub_script_ver)
            print("vec2ate conversion done!")

    # --- STIL input ---
    elif ext == ".stil":
        print("Processing STIL file with stil2vec...")
        vec_file, cmf_file = stil2vec.convert_stil_to_vec(file_path)
        print(f"VEC file: {vec_file}, CMF file: {cmf_file}")
        if ate_type != "VEC":
            #template_file = vec2ate.J750_TEMPLATE if ate_type.upper() == "J750" else vec2ate.CHROMA_TEMPLATE
            file_ext = ".atp" if ate_type.upper() == "J750" else ".pat"
            print(f"Converting {vec_file} -> {ate_type} using vec2ate...")
            vec2ate.convert_vec_file(vec_file, cmf_file, dec_file or "",
                                     file_extension=file_ext,
                                     ate_type=ate_type.upper(),
                                     script_ver=sub_script_ver)
            print("vec2ate conversion done!")

    # --- VCD input ---
    elif ext == ".vcd":
        print("Processing VCD file with vcd2vec...")
        if interval is None:
            while True:
                try:
                    interval = int(input("Enter timing interval (ns, e.g. 41665): ").strip())
                    if interval <= 0:
                        raise ValueError
                    break
                except ValueError:
                    print("Invalid input. Enter a positive integer for interval.")
        vec_file, cmf_file = vcd2vec.convert_vcd_to_vec(file_path, interval)
        print(f"VEC file: {vec_file}, CMF file: {cmf_file}")
        if ate_type != "VEC":
            #template_file = vec2ate.J750_TEMPLATE if ate_type.upper() == "J750" else vec2ate.CHROMA_TEMPLATE
            file_ext = ".atp" if ate_type.upper() == "J750" else ".pat"
            print(f"Converting {vec_file} -> {ate_type} using vec2ate...")
            vec2ate.convert_vec_file(vec_file, cmf_file, dec_file or "",
                                     file_extension=file_ext,
                                     ate_type=ate_type.upper(),
                                     script_ver=sub_script_ver)
            print("vec2ate conversion done!")

    # --- VEC input ---
    elif ext == ".vec":
        print("Converting .vec to ATE pattern using vec2ate...")
        if not ate_type:
            ate_type = input("Enter ATE type (J750,C3380,C3850): ").strip().upper()
        cmf_file = os.path.splitext(file_path)[0] + ".cmf"
        #template_file = vec2ate.J750_TEMPLATE if ate_type.upper() == "J750" else vec2ate.CHROMA_TEMPLATE
        file_ext = ".atp" if ate_type.upper() == "J750" else ".pat"
        vec2ate.convert_vec_file(file_path, cmf_file, dec_file or "",
                                 file_extension=file_ext,
                                 ate_type=ate_type.upper(),
                                 script_ver=sub_script_ver)
        print("vec2ate conversion done!")

    else:
        print("Unsupported file type:", ext)
