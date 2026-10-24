import os
import sys
import subprocess
from pathlib import Path

def main():
    paper_dir = Path(__file__).resolve().parent
    workspace_dir = paper_dir.parent
    tectonic_bin = workspace_dir / "bin" / "tectonic.exe"

    if not tectonic_bin.exists():
        print(f"Error: Tectonic compiler not found at {tectonic_bin}")
        sys.exit(1)

    tex_file = paper_dir / "main.tex"
    if not tex_file.exists():
        print(f"Error: LaTeX source file not found at {tex_file}")
        sys.exit(1)

    print(f"Compiling {tex_file.name} using Tectonic...")
    cmd = [str(tectonic_bin), str(tex_file), "--outdir", str(paper_dir)]
    
    result = subprocess.run(cmd, cwd=str(paper_dir))
    if result.returncode == 0:
        pdf_file = paper_dir / "main.pdf"
        print(f"\n[SUCCESS] Journal paper compiled successfully -> {pdf_file}")
    else:
        print(f"\n[ERROR] Compilation failed with exit code {result.returncode}")
        sys.exit(result.returncode)

if __name__ == "__main__":
    main()
