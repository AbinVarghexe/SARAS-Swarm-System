"""
Automated Cross-Platform LaTeX Project Report Compiler (Windows, macOS, Linux)
- Checks for existing LaTeX compilers (tectonic, pdflatex, xelatex).
- If none is found, auto-detects OS & CPU architecture (Windows, macOS Apple Silicon / Intel, Linux).
- Automatically downloads standalone Tectonic LaTeX engine and compiles main.tex to PDF.
"""

import os
import sys
import subprocess
import shutil
import urllib.request
import zipfile
import tarfile
import io
import platform

def get_download_url():
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        return "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-pc-windows-msvc.zip"
    elif system == "darwin":  # macOS
        if machine in ["arm64", "aarch64"]:
            # Apple Silicon M1/M2/M3/M4
            return "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-aarch64-apple-darwin.tar.gz"
        else:
            # Intel Mac
            return "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-apple-darwin.tar.gz"
    elif system == "linux":
        if machine in ["arm64", "aarch64"]:
            return "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-aarch64-unknown-linux-musl.tar.gz"
        else:
            return "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-unknown-linux-musl.tar.gz"
    else:
        raise OSError(f"Unsupported operating system: {system}")

def find_or_install_compiler(target_dir):
    # 1. Check system PATH
    for cmd in ["tectonic", "pdflatex", "xelatex"]:
        path = shutil.which(cmd)
        if path:
            print(f"[+] Found system LaTeX compiler: {path}")
            return path

    # 2. Check local bin/ folder in target_dir, parent dir, or script dir
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_bin_dirs = [
        os.path.join(target_dir, "bin"),
        os.path.join(os.path.dirname(target_dir), "bin"),
        os.path.join(os.path.dirname(os.path.dirname(target_dir)), "Latex", "bin"),
        os.path.join(script_dir, "bin"),
    ]
    exe_name = "tectonic.exe" if platform.system().lower() == "windows" else "tectonic"
    for bin_dir in local_bin_dirs:
        candidate = os.path.join(bin_dir, exe_name)
        if os.path.exists(candidate) and os.path.isfile(candidate):
            print(f"[+] Found local Tectonic compiler: {candidate}")
            return candidate

    # 3. Auto-download standalone Tectonic for current OS & Architecture
    print(f"[*] No LaTeX compiler found. Detected OS: {platform.system()} ({platform.machine()})")
    print("[*] Auto-downloading standalone Tectonic LaTeX engine...")

    dest_bin = os.path.join(target_dir, "bin")
    os.makedirs(dest_bin, exist_ok=True)
    dest_exe = os.path.join(dest_bin, exe_name)

    url = get_download_url()
    print(f"[*] Downloading from: {url}")

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        content = resp.read()

    if url.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            z.extractall(dest_bin)
    else:
        with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as tar:
            tar.extractall(dest_bin)

    if platform.system().lower() != "windows":
        os.chmod(dest_exe, 0o755)
        if platform.system().lower() == "darwin":
            try:
                subprocess.run(["xattr", "-d", "com.apple.quarantine", dest_exe], capture_output=True)
            except Exception:
                pass

    print(f"[+] Successfully installed standalone Tectonic to: {dest_exe}")
    return dest_exe

def compile_report(main_tex_path, out_dir=None):
    if not os.path.exists(main_tex_path):
        print(f"[-] Error: File not found: {main_tex_path}")
        sys.exit(1)

    work_dir = os.path.dirname(os.path.abspath(main_tex_path))
    if out_dir is None:
        out_dir = work_dir
    os.makedirs(out_dir, exist_ok=True)

    compiler = find_or_install_compiler(work_dir)
    print(f"[*] Compiling {os.path.basename(main_tex_path)} using {os.path.basename(compiler)}...")

    if "tectonic" in os.path.basename(compiler).lower():
        cmd = [compiler, main_tex_path, "--outdir", out_dir]
        result = subprocess.run(cmd, cwd=work_dir)
    else:
        # Run pdflatex twice for cross references and TOC
        cmd = [compiler, "-interaction=nonstopmode", f"-output-directory={out_dir}", main_tex_path]
        print("[*] Pass 1/2...")
        subprocess.run(cmd, cwd=work_dir)
        print("[*] Pass 2/2...")
        result = subprocess.run(cmd, cwd=work_dir)

    pdf_name = os.path.splitext(os.path.basename(main_tex_path))[0] + ".pdf"
    pdf_path = os.path.join(out_dir, pdf_name)
    if os.path.exists(pdf_path) and result.returncode == 0:
        print(f"\n[SUCCESS] Compiled PDF generated: {pdf_path}")
        return pdf_path
    else:
        print(f"\n[-] Compilation finished with return code {result.returncode}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = "main.tex" if os.path.exists("main.tex") else os.path.join(os.path.dirname(__file__), "main.tex")

    out = sys.argv[2] if len(sys.argv) > 2 else None
    compile_report(target, out)
