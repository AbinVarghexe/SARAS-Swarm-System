"""
Build Word and PDF Documents for 'SWARM SYSTEM FOR DISASTER RESPONSE'
Directly redirects to the updated clean builder in build_review_pdf.py.
"""
import subprocess
import sys

if __name__ == "__main__":
    ret = subprocess.run([sys.executable, r"d:\DEV\Final Year Project\ProjectReport\Journal_Paper\build_review_pdf.py"])
    sys.exit(ret.returncode)
