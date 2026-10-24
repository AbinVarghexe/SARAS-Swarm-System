# KTU B.Tech S7 Seminar Report LaTeX Toolkit & Antigravity Skill
*(Cross-Platform: Windows, macOS Apple Silicon & Intel, Linux)*

An all-in-one automated LaTeX template and Antigravity Skill for **KTU S7 B.Tech Computer Science and Engineering Seminar Reports** (Amal Jyothi College of Engineering standard).

---

## 📦 What's Included in This Bundle

- **`Report_format_S7/`**: Complete modular LaTeX template files ready to edit.
- **`Report_format_S7/compile_report.py`**: Cross-platform auto-compiler script (auto-detects Windows, macOS Apple Silicon/Intel, Linux and downloads standalone Tectonic LaTeX engine if needed).
- **`compile.bat`**: 1-click runner for **Windows** (double-click to compile).
- **`compile.command` / `compile.sh`**: 1-click runner for **macOS / Linux** (double-click or run in terminal).
- **`.agents/skills/ktu-seminar-report/`**: Antigravity AI skill to automate the entire report generation.
- **`Seminar_Report_Sample.pdf`**: Pre-compiled reference PDF.
- **Official References**:
  - `Seminar_Report_Formatting_Instructions_ Template.pdf`
  - `po_peo_vision_mission_recordbook_17_08_2026_CSE.pdf`

---

## 🚀 Quick Start: 3 Ways to Use

### 🌟 Method 1: Using Antigravity AI (Windows & macOS)

1. Copy the `.agents/` folder into your project root.  
   *(Or copy `.agents/skills/ktu-seminar-report` to `~/.gemini/config/skills/ktu-seminar-report` on Mac/Linux or `C:\Users\<Username>\.gemini\config\skills\` on Windows)*.
2. In Antigravity, simply prompt:
   > *"Create my S7 Seminar Report on [Your Topic]. My name is [Your Name], Reg No is [AJC21CS...], and my guide is [Dr./Prof. Name]."*
3. Antigravity will automatically fill in all sections and compile the PDF for you.

---

### ⚡ Method 2: 1-Click Local Compilation (No LaTeX Installation Needed!)

#### On Windows:
1. Edit the `.tex` files in `Report_format_S7/` with your content.
2. **Double-click `compile.bat`**.

#### On macOS (Apple Silicon M1/M2/M3/M4 & Intel) / Linux:
1. Edit the `.tex` files in `Report_format_S7/` with your content.
2. **Double-click `compile.command`** in Finder (or open Terminal in this folder and run `bash compile.sh` or `python3 Report_format_S7/compile_report.py`).

*The script auto-detects your operating system and CPU architecture, downloads the lightweight standalone compiler if missing, and outputs `Main.pdf`.*

---

### ☁️ Method 3: Using Overleaf (Cloud)

1. Zip the `Report_format_S7` folder.
2. Go to [Overleaf](https://www.overleaf.com) $\to$ **New Project** $\to$ **Upload Project**.
3. Select `Main.tex` as the root document and click **Recompile**.

---

## 📋 Document Structure & Guidelines

| File | Section | Notes |
| :--- | :--- | :--- |
| `Title.tex` | Title Page | Single-page layout with student, guide, and college crest. |
| `Certf.tex` | Certificate Page | Signature blocks for Guide, Coordinators, and HOD. |
| `VisionMission.tex` | Dept Vision & Mission | Vision, Mission, PEOs 1-3, PSOs 1-3 (Optional). |
| `Ackn.tex` | Acknowledgement | Roman page `i`. |
| `Abstract.tex` | Abstract | Roman page `ii`. |
| `Abbrevations.tex`| Abbreviations | Two-column acronym list. |
| `intro.tex` | Chapters 1 – 5 | Core report body (Arabic numbering starting from page 1). |
| `Bibilo.tex` | References | IEEE citation format (`\cite{1}`). |
| `Appendix.tex` | Appendix | Screenshots and sample code listings. |

---

## 🖨️ Final Printing & Binding Instructions
- **Binding Style:** Soft bind (1 copy).
- **Physical Attachment Order:**
  1. Main Seminar Report (Title page to Appendix).
  2. Seminar Presentation PPT slides (printed **4 slides per page**).
  3. Seminar Base Research Paper attached at the very end.
