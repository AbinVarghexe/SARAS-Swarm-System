# KTU B.Tech Project Report Toolkit — Complete User Manual
**Amal Jyothi College of Engineering (Autonomous), Kanjirappally**  
*Department of Computer Science and Engineering | APJ Abdul Kalam Technological University (KTU)*

---

## 1. Introduction & Overview

Welcome to the **KTU B.Tech Computer Science Project Report Toolkit**. This package provides an end-to-end, publication-grade LaTeX reporting environment specifically pre-configured to comply with university and college submission guidelines for both **Phase I Project Reports (S7)** and **Final Project Reports (S8)**.

### Key Highlights
- **Zero-Dependency One-Click Compilation:** No need to install massive 5GB+ distributions like MiKTeX or TeXLive. The bundled compiler automatically runs or fetches the standalone cross-platform `tectonic` engine on Windows, macOS (Apple Silicon & Intel), and Linux.
- **Strict KTU Alignment & Layout:**
  - Guaranteed single-page **Title / Cover Page** with highlighted typography and exact vertical spacing.
  - Guaranteed single-page **Certificate** with balanced, parallel two-column signature layout (`Internal Supervisor` & `Project Coordinator`) and centered `Head of Department`.
  - Single-page **Declaration**, **Acknowledgement**, and **Abstract** (250--300 words without unexpanded abbreviations).
  - Proper Roman numeral numbering for front matter (`i`, `ii`, `iii`...) and Arabic numbering for body chapters (`1`, `2`, `3`...).
  - Automated detection and prevention of orphan lines (1–2 trailing lines on a blank page).
- **Comprehensive 6-Chapter Standard:**
  - **Chapter 1: Introduction** (Background, Motivation, Problem Statement, Objectives, Scope & Limitations, Contributions, Report Organization)
  - **Chapter 2: Literature Survey** (Problem Domain Overview, Classical ML, Deep Learning, Hybrid/Recent, Datasets, Comparison Table, Research Gap)
  - **Chapter 3: Proposed Methodology** (System Overview, Dataset Description, Preprocessing, Feature Representation, Architecture, Loss Functions & Optimization, Training Strategy, Metrics)
  - **Chapter 4: Implementation** (Hardware & Software, Tools & Frameworks, Dataset Split, Hyperparameters, Training Flow, Deployment / UI)
  - **Chapter 5: Results and Discussion** (Experimental Setup, Training Curves, Performance Metrics, Confusion Matrix, Baseline Comparisons, Literature Benchmarking, Ablation Study, Error Analysis, Discussion)
  - **Chapter 6: Conclusion and Future Work** (Conclusion mapping to objectives, Limitations, Future Extensions)
  - **Back Matter:** IEEE-style References, Appendix A (Key Code Snippets), Appendix B (Visual Demonstrations)

---

## 2. Package File Structure

```text
KTU_BTech_Project_Report_Template_Toolkit/
│
├── main.tex                  # Master LaTeX driver file (defines geometry, packages, fonts)
├── title.tex                 # Front cover / Title page with college logo & guide details
├── declaration.tex           # Student bonafide declaration (single page)
├── certificate.tex           # Official department certificate with signature blocks
├── ackn.tex                  # Acknowledgement section (single page)
├── abstract.tex              # Project Abstract (single page, 250-300 words)
├── Abbrevations.tex          # Acronyms & Abbreviations table
│
├── intro.tex                 # Chapter 1: Introduction (Sections 1.1 - 1.7)
├── litsurvey.tex             # Chapter 2: Literature Survey (Sections 2.1 - 2.7)
├── methodology.tex           # Chapter 3: Proposed Methodology (Sections 3.1 - 3.8)
├── implementation.tex        # Chapter 4: Implementation (Sections 4.1 - 4.6)
├── results.tex               # Chapter 5: Results and Discussion (Sections 5.1 - 5.9)
├── conclusion.tex            # Chapter 6: Conclusion and Future Work (Sections 6.1 - 6.3)
├── bibilo.tex                # IEEE-formatted Bibliography (20-30 references)
├── Appendix.tex              # Appendix A (Code snippets) & Appendix B (Visualizations)
│
├── content.md                # Interactive Markdown guide to draft your project details
├── USER_MANUAL.md            # This comprehensive step-by-step user manual
├── README.md                 # Quick reference overview
│
├── compile_report.py         # Python-powered cross-platform auto-compiler
├── compile.bat               # Windows 1-click batch compiler
├── compile.sh                # macOS & Linux 1-click shell compiler
│
└── assets/                   # Folder for project diagrams, architecture charts, photos
    └── ajcelogo2023.png      # Official Amal Jyothi College vector logo (do not delete)
```

---

## 3. How to Use the Toolkit

### Method A: Automated Generation with Antigravity AI (Recommended)

1. **Install the Skill:**
   - Unzip `KTU_Project_Report_Skill.zip`.
   - Copy `ktu-project-report` to your global skills directory (`~/.gemini/config/skills/ktu-project-report/`) or active project (`.agents/skills/ktu-project-report/`).
   - In Antigravity IDE, reload window (`Ctrl+Shift+P` $\rightarrow$ `Developer: Reload Window`).
2. **Prepare Your Input:**
   - Fill in `content.md` with your project metadata, objectives, model architecture, and results.
   - Drop your figures, system architecture diagrams, and test charts into `assets/`.
3. **Run Prompt in Chat:**
   > *"Generate my KTU project report using the ktu-project-report skill from my content.md and assets/ folder."*
   The AI will automatically populate all 6 chapters, format equations and tables with `\resizebox`, verify zero-orphan line constraints, and compile the final publication-ready PDF.

---

### Method B: Manual Editing Workflow

1. **Front Matter:**
   - Update `title.tex` with your project title, name, registration number, and faculty guide details. For multiple students, uncomment lines 14–17.
   - Update `declaration.tex`, `certificate.tex`, `ackn.tex`, and `abstract.tex`.
2. **Chapters:**
   - Follow the pre-structured sections in `intro.tex`, `litsurvey.tex`, `methodology.tex`, `implementation.tex`, `results.tex`, and `conclusion.tex`.
   - Wrap wide tables in `\resizebox{0.95\columnwidth}{!}{...}` to prevent margin overflow.
   - Add references in `bibilo.tex` using standard IEEE format.
3. **Compile:**
   - **Windows:** Double click `compile.bat` or run `python compile_report.py main.tex`.
   - **macOS / Linux:** Run `./compile.sh` or `python3 compile_report.py main.tex`.
