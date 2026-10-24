---
name: ktu-seminar-report
description: >-
  Create, format, and compile official KTU S7 B.Tech Computer Science Seminar Reports
  (Amal Jyothi College of Engineering standard). Handles automated LaTeX document generation,
  Title & Certificate signature alignments, Department Vision/Mission/PEOs/PSOs,
  Chapter structuring, and automatic downloading/compilation with standalone Tectonic compiler.
---

# KTU B.Tech S7 Seminar Report Skill

This skill guides the AI assistant in creating, customizing, and compiling standard B.Tech S7 Seminar Reports for the **Department of Computer Science and Engineering, Amal Jyothi College of Engineering (Autonomous), APJ Abdul Kalam Technological University (KTU)**.

---

## 1. Information Gathering Checklist

Before generating or updating a report, always ask or confirm these details with the user:

1. **Seminar Topic & Base Paper:** Title, authors, conference/journal, year, and key methodology/abstract.
2. **Student Details:** Student Name and KTU Register Number (e.g. `AJC21CS...`).
3. **Faculty Guide Details:** Full name (with prefix: Dr. / Prof. / Mr. / Ms.) and designation (*Assistant Professor / Associate Professor / Professor*).
4. **Academic Year & Month:** e.g., *October 2026*, Academic Year *2026–2027*.
5. **Department Authority Defaults:**
   - **Head of Department (CSE):** Dr. Juby Mathew
   - **Seminar Coordinators:** Dr. Anju J Prakash & Ms. Shiney Thomas
   - **College Administration (in Acknowledgement):** Manager (Rev. Fr. Boby Alex Mannamplackal), Director (Fr. Dr. Roy Abraham Pazhayaparampil), Principal (Dr. Lillykutty Jacob).

---

## 2. Formatting & Typography Specifications

The generated report must strictly conform to these KTU S7 specifications:

- **Paper Size:** A4 (`\documentclass[a4paper,12pt]{report}`)
- **Margins:** Left (binding edge) = **3.0 cm** (1.2 in); Right, Top, Bottom = **2.5 cm** (1.0 in).
- **Line Spacing:** **1.5 (one-and-a-half)** throughout the body using `\usepackage{setspace}` and `\onehalfspacing`.
- **Headings:**
  - Chapter titles: `\chapterfont{\Large\centering\MakeUppercase}`.
  - Sections: Numbered hierarchically (`1.1`, `1.2`, `1.1.1`).
- **Page Numbering:**
  - Front matter (*Acknowledgement, Abstract, TOC, LOT, LOF, Abbreviations*): Lowercase Roman numerals (`i, ii, iii...`).
  - Body (*Chapter 1 Introduction to References/Appendix*): Arabic numerals (`1, 2, 3...`) starting at `1` on Chapter 1.
  - Title Page & Certificate: **No visible page number**.
- **Tables & Figures:**
  - Table captions: Placed **above** the table.
  - Figure captions: Placed **below** the image.
- **Headers & Footers:** Configured with `fancyhdr`:
  - Left Footer: `\textit{Department of CSE, Amal Jyothi College of Engineering}`
  - Right Footer: `\textit{\thepage}`
  - Right Header: `\nouppercase{\textit{\leftmark}}`

---

## 3. Standard Document Ordering

```
1. Title Page (Title.tex)
2. Certificate Page (Certf.tex)
3. Vision, Mission, PEOs, PSOs (VisionMission.tex) [Optional / Record Book]
4. Acknowledgement (Ackn.tex)
5. Abstract (Abstract.tex)
6. Table of Contents (\tableofcontents)
7. List of Tables (\listoftables)
8. List of Figures (\listoffigures)
9. List of Abbreviations (Abbrevations.tex)
10. Chapter 1 – Introduction (1.1 Overview, 1.2 Motivation and Objectives, 1.3 Report Organization)
11. Chapter 2 – Literature Survey (Subsections + IEEE citations \cite{...})
12. Chapter 3 – Proposed Methodology (Architecture, Algorithms, Datasets)
13. Chapter 4 – Results and Discussions (Tables, Graphs, Comparative Analysis)
14. Chapter 5 – Conclusion and Future Work (Summary, Future Directions)
15. References (Bibilo.tex)
16. Appendix (Appendix.tex - Screenshots, Code)
```

---

## 4. Automated Compilation Workflow

The skill includes `scripts/compile_report.py` which guarantees zero-configuration compilation:

```bash
python scripts/compile_report.py <path-to-Main.tex> [output-directory]
```

### What `compile_report.py` does:
1. Searches for existing LaTeX compilers (`tectonic`, `pdflatex`, `xelatex`) in the system `PATH`.
2. If none is found, it **automatically downloads the standalone Tectonic LaTeX engine** (no admin rights needed, no multi-GB installation).
3. Compiles the report with automatic package downloading from CTAN and generates the final PDF with all cross-references resolved.

---

## 5. Physical Binding Instructions (For Student)
- Soft bind, 1 copy.
- Attached after the report:
  1. Seminar presentation PPT slides (printed **4 slides per page**).
  2. The base research paper.
