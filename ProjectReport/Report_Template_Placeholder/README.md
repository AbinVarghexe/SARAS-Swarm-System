# KTU B.Tech Project Report Starter Template
**Department of Computer Science and Engineering**  
**Amal Jyothi College of Engineering (Autonomous), Kanjirappally**  
*APJ Abdul Kalam Technological University (KTU)*

---

## 📖 Complete Documentation & User Manual
For comprehensive documentation, including detailed formatting guidelines, multi-author setup, image instructions, and troubleshooting, read the **[USER MANUAL (USER_MANUAL.md)](./USER_MANUAL.md)**.

---

## ⚡ Quick Start in 3 Easy Steps

### Step 1: Provide Your Project Content & Images
1. Open [`content.md`](./content.md) and fill in your project details (Title, Names, Guide, Chapter outlines).
2. Copy your diagrams, architecture flowcharts, and performance graphs into the [`assets/`](./assets/) folder.

### Step 2: Edit LaTeX or Use the AI Skill
- **Automated AI Generation:** If you use Google Antigravity, install the bundled `ktu-project-report` skill (from `KTU_Project_Report_Skill.zip`) and ask the agent to generate your report from `content.md` and `assets/`.
- **Manual Editing:** Edit the modular `.tex` files directly:
  - `title.tex` — Cover & Title Page
  - `declaration.tex` — Student Declaration
  - `certificate.tex` — Department Certificate & Signatures
  - `ackn.tex` — Acknowledgement
  - `abstract.tex` — Project Abstract
  - `Abbrevations.tex` — List of Abbreviations
  - `intro.tex` — Chapter 1: Introduction
  - `litsurvey.tex` — Chapter 2: Literature Survey
  - `implementation.tex` — Chapter 3: Implementation Details
  - `results.tex` — Chapter 4: Results and Discussion
  - `conclusion.tex` — Chapter 5: Conclusion & Future Work
  - `bibilo.tex` — IEEE Bibliography

### Step 3: One-Click Compile to PDF
- **On Windows:** Double-click [`compile.bat`](./compile.bat) or run:
  ```powershell
  python compile_report.py main.tex
  ```
- **On macOS / Linux:** In Terminal, run:
  ```bash
  chmod +x compile.sh
  ./compile.sh
  ```
*(Zero setup needed! The script automatically uses your local LaTeX or downloads the standalone Tectonic compiler).*
