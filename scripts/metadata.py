# metadata.py
author = "Juneth Viktor Ellon Moreno"
#script_ver = "0.1"
#initial beta release of VektorConverter
#convert Design Vectors to ATE-ready pattern files
#script_ver = "1.0"
#Official Release for Production use
#no known-issues
#documentation is ready
script_ver = "1.1"
#Official Release for Production use
# Major Issue: Error in Pattern Compiler; Cannot generate pat.gz file
# Fix: Setup- CMF or Vector pins must match the current Pin Map sheet in the IG-XL Workbook
#      vec2ate.py - must contain at least 1 space between bits
#      ate2vec.py - updated to detect the spaces between vectors
# Verification: Done checking vec/cmf/.atp/pat. Tried the atp with PatternCompiler, no more issues

info_text = (
    f"VektorConverter\n"
    f"Version: {script_ver}\n\n"
    f"Copyright (c) 2026 {author}\n"
    f"All rights reserved"
)