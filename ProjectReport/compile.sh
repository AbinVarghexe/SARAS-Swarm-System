#!/usr/bin/env bash
set -e
echo "========================================================"
echo "  Compiling KTU B.Tech Project Report..."
echo "========================================================"
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"
python3 compile_report.py main.tex
echo ""
echo "========================================================"
echo "  Finished! Check main.pdf"
echo "========================================================"
