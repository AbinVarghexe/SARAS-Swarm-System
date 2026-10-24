#!/bin/bash
# Download helper script for SARAS research papers
# Searches Google Scholar for each paper title
# Note: This script generates search URLs. Downloading requires institutional access or arXiv/open-access versions.

echo "================================================"
echo "SARAS Research Paper Downloader"
echo "================================================"
echo ""
echo "This script generates Google Scholar search URLs for each paper."
echo "Many papers are behind paywalls; prefer open-access versions (arXiv, IEEE Xplore Open, MDPI, etc.)"
echo ""

# Function to generate scholar search URL
google_scholar_url() {
    local title="$1"
    # URL encode title for search
    local encoded=$(echo "$title" | sed 's/ /+/g' | sed 's/:/%3A/g')
    echo "https://scholar.google.com/scholar?q=${encoded}"
}

echo "Software Papers:"
echo "---"
echo "CV:"
google_scholar_url "Deep Learning for Aerial Scene Understanding A Survey"
echo ""
echo "Object Detection:"
google_scholar_url "Real-time Object Detection Using Deep Learning on Aerial Images"
echo ""
echo "Object Tracking:"
google_scholar_url "ByteTrack Multi-Object Tracking by Associating Every Detection Box"
echo ""
echo "Swarm Robotics:"
google_scholar_url "A Review of Multi-UAV Cooperative Mission Planning and Control"
echo ""
echo "Multi-Agent RL:"
google_scholar_url "Multi-Agent Reinforcement Learning A Comprehensive Survey"
echo ""
echo "Task Allocation:"
google_scholar_url "Distributed Auction Algorithms for Multi-Agent Task Allocation"
echo ""
echo "Real-time AI Systems:"
google_scholar_url "Real-Time Object Detection for Embedded Systems A Survey"
echo ""

echo ""
echo "Hardware Papers:"
echo "---"
echo "Autonomous UAVs:"
google_scholar_url "A Review of Unmanned Aerial Vehicles for Search and Rescue Operations"
echo ""
echo "Communication:"
google_scholar_url "Communication Protocols for UAV Swarms A Survey"
echo ""
echo "Edge Inference:"
google_scholar_url "Optimizing YOLO Networks with TensorRT for Real-Time Object Detection"
echo ""

echo ""
echo "================================================"
echo "For direct downloads, use these Chrome extensions or tools:"
echo "  - Unpaywall (browser extension for find free PDFs)"
echo "  - Zotero + Sci-Hub plugin (automatic DOI resolution)"
echo "  - arXiv.org (for preprints of many ML/robotics papers)"
echo "  - IEEE Xplore (institutional access required)"
echo "================================================"
