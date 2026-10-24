# 🎓 How to Share & Use the KTU S7 Seminar Report Toolkit

This document explains **what to send to your friends** and provides **step-by-step instructions** they can follow on **Windows** or **macOS**.

---

## 📤 1. What File Should You Share?

Send your friend the file:
👉 **`KTU_S7_Seminar_Report_Toolkit.zip`** *(located in this folder)*

> **Why this file?**  
> It is an all-in-one package (~2.4 MB) containing all LaTeX templates, logos, the sample PDF, official formatting PDFs, 1-click compilers for Windows/macOS, and the Antigravity AI skill. They do **NOT** need to install heavy LaTeX software (like MiKTeX or MacTeX).

---

## 📖 2. Instructions for Your Friend (Copy-Paste this to them)

---

### 👋 Welcome! Here is how to create your S7 Seminar Report in minutes:

#### Step 1: Unzip the Folder
Extract `KTU_S7_Seminar_Report_Toolkit.zip` onto your computer (e.g., Desktop or Documents).

---

### 🌟 METHOD 1: Using Antigravity AI (Easiest & Fastest)

If you use Google Antigravity or Antigravity IDE:

1. **Install the Skill:**
   - **Windows:** Copy the folder `.agents\skills\ktu-seminar-report` into:  
     `C:\Users\<YourUsername>\.gemini\config\skills\ktu-seminar-report`
   - **macOS / Linux:** Copy the folder `.agents/skills/ktu-seminar-report` into:  
     `~/.gemini/config/skills/ktu-seminar-report`
   *(Alternatively, simply open the unzipped `KTU_S7_Seminar_Report_Toolkit` folder in Antigravity — the skill is already in `.agents/`!)*

2. **Prompt the Agent in Chat:**
   Send a message like:
   > *"Create my S7 Seminar Report on [Your Topic]. My name is [Your Name], Register Number is [AJC21CS...], and my faculty guide is [Dr./Prof. Guide Name], [Assistant/Associate Professor]. Here is my base paper abstract: [paste abstract]"*

3. **Done!** Antigravity will customize all LaTeX files, auto-download the lightweight compiler in the background, and output your finalized, print-ready PDF!

---

### ⚡ METHOD 2: 1-Click Local Editing (VS Code / Text Editor)

If you prefer editing the text yourself without AI:

1. Open the folder **`Report_format_S7/`**.
2. Open and fill in your details in the `.tex` files:
   - **`Title.tex`**: Put your Seminar Title, Name, Register No, and Guide Name.
   - **`Certf.tex`**: Put your Name, Register No, and Guide Name.
   - **`Ackn.tex`**: Put your Name and Guide Name.
   - **`Abstract.tex`**: Paste your seminar abstract.
   - **`intro.tex`**: Put your Chapters 1 to 5 (Overview, Literature Survey, Methodology, Results, Conclusion).
   - **`Bibilo.tex`**: Add your reference citations.
3. **Compile to PDF in 1 Click:**
   - **On Windows:** Double-click **`compile.bat`** (or open `Report_format_S7/` and double-click `compile_report.py`).
   - **On macOS:** Double-click **`compile.command`** (or open Terminal and run `bash compile.sh`).
4. **Done!** Open **`Main.pdf`** inside `Report_format_S7/` to see your completed report.

---

### ☁️ METHOD 3: Using Overleaf (Web Browser)

1. Right-click the **`Report_format_S7`** folder $\to$ **Compress to ZIP**.
2. Go to [Overleaf.com](https://www.overleaf.com) $\to$ **New Project** $\to$ **Upload Project**.
3. Upload the zip file $\to$ Select `Main.tex` $\to$ Click **Recompile**.

---

## 📋 Checklist for Final Print & Binding

- [ ] **Margins:** Left = 3.0 cm (Binding edge), Top/Bottom/Right = 2.5 cm *(Configured automatically)*
- [ ] **Line Spacing:** 1.5 spacing *(Configured automatically)*
- [ ] **Order of Documents:**
  1. Title Page (No page number)
  2. Certificate Page (No page number)
  3. Acknowledgement (Roman `i`)
  4. Abstract (Roman `ii`)
  5. Table of Contents / List of Tables / List of Figures
  6. Abbreviations
  7. Chapters 1 through 5 (Arabic page 1 onwards)
  8. References
  9. Appendix (Screenshots / Code)
- [ ] **Physical Attachments (For Soft Binding):**
  - Attach Seminar Presentation PPT (printed **4 slides per page**).
  - Attach the Base Research Paper at the end.
