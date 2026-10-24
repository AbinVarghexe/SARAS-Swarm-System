import os
import re

source_path = r'C:\Users\abinv\Downloads\IJERA_TEMPLATE\IJERA_TEMPLATE\journal_paper.tex'
with open(source_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Extract abstract
abs_m = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', text, re.DOTALL)
abstract_text = abs_m.group(1).strip() if abs_m else ''

# Extract body
kw_end = text.find(r'\end{IEEEkeywords}')
if kw_end == -1:
    kw_end = text.find(r'\end{abstract}') + len(r'\end{abstract}')
else:
    kw_end += len(r'\end{IEEEkeywords}')

bib_start = text.find(r'\begin{thebibliography}')
body_text = text[kw_end:bib_start].strip()

# Adjust figure* / table*
body_text = body_text.replace(r'\begin{figure*}', r'\begin{figure}')
body_text = body_text.replace(r'\end{figure*}', r'\end{figure}')
body_text = body_text.replace(r'\begin{table*}', r'\begin{table}')
body_text = body_text.replace(r'\end{table*}', r'\end{table}')

header = r'''\documentclass[namedreferences,hyperref,optionalrh,solaromanenum]{spr-sola}
\usepackage{graphicx}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{color}
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{tikz}
\usetikzlibrary{shapes.geometric, arrows.meta, positioning, fit, calc, backgrounds}
\usepackage{pgfplots}
\pgfplotsset{compat=1.17}
\usepackage{algorithm}
\usepackage{algorithmic}
\usepackage{url}

% Definitions for math and vectors
\renewcommand{\vec}[1]{{\mathbfit #1}}
\newcommand{\rmd}{{\ \mathrm d}}

\begin{document}

\begin{frontmatter}

\title{Perception-Driven Meta-Adaptive Swarm Coordination: Integrating Multi-Spectral YOLO-Air Perception with MAML-Enhanced Multi-Agent Reinforcement Learning for Resilient Disaster Search and Rescue}

\author[addressref=aff1,email={abinvarghese2027@cs.ajce.in}]{\inits{A.}\fnm{Abin}~\snm{Varghese}}
\author[addressref=aff1,email={alfinsenvarghese2027@cs.ajce.in}]{\inits{A.S.}\fnm{Alfin~Sen}~\snm{Varghese}}
\author[addressref=aff1,corref,email={jacobjohn@amaljyothi.ac.in}]{\inits{J.}\fnm{Jacob}~\snm{John}}

\address[id=aff1]{Department of Computer Science and Engineering, Amal Jyothi College of Engineering (Autonomous), Kanjirappally, Kottayam, Kerala 686518, India}

\runningauthor{A. Varghese et al.}
\runningtitle{Perception-Driven Meta-Adaptive Swarm Coordination (PD-MASC)}

\begin{abstract}
''' + abstract_text + r'''
\end{abstract}

\begin{keyword}
\kwd{Unmanned Aerial Vehicle (UAV) swarms}
\kwd{Disaster response}
\kwd{Search and rescue}
\kwd{YOLO-Air}
\kwd{Small object detection}
\kwd{Model-Agnostic Meta-Learning (MAML)}
\kwd{Multi-Agent Reinforcement Learning (MARL)}
\kwd{Coalition formation}
\kwd{Fault tolerance}
\kwd{Edge artificial intelligence}
\end{keyword}

\end{frontmatter}
'''

end_matter = r'''
\begin{acks}
The authors express their gratitude to the Department of Computer Science and Engineering, Amal Jyothi College of Engineering (Autonomous), for providing laboratory resources, GPU computing nodes, and hardware testbeds supporting this research.
\end{acks}

\begin{authorcontribution}
All authors contributed extensively to the conceptualization, mathematical formulation, algorithmic implementation, simulation experiments, and manuscript preparation of this work. A.~Varghese and A.S.~Varghese developed the perception models, simulation pipeline, and conducted empirical evaluations. Dr.~J.~John supervised the research, formulated the theoretical framework, and reviewed the final manuscript.
\end{authorcontribution}

\begin{fundinginformation}
This research received no external grant funding and was conducted utilizing institutional research facilities at Amal Jyothi College of Engineering (Autonomous).
\end{fundinginformation}

\begin{dataavailability}
The data supporting the findings of this study, including the modified YOLO-Air weights, SITL simulation environment configurations, and evaluation trajectories, are openly accessible via GitHub at \url{https://github.com/AbinVarghese/PD-MASC-Swarm}.
\end{dataavailability}

\begin{ethics}
\begin{conflict}
The authors declare that they have no competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.
\end{conflict}
\end{ethics}

\begin{thebibliography}{}

\bibitem[\protect\citeauthoryear{Poudel and Moh}{2026}]{ref_poudel2026}
Poudel, S., Moh, S.: 2026, MAML-Integrated Multi-Agent Reinforcement Learning for Adaptive Coalition-Based UAV Coordination in Disaster Scenarios. \textit{Internet of Things} \textbf{37}, 101930.

\bibitem[\protect\citeauthoryear{Qiu et al.}{2024}]{ref_qiu2024}
Qiu, J., Cai, F., Fu, N., Yao, X.: 2024, YOLO-Air: An efficient deep learning network for small object detection in drone-based imagery. \textit{IEEE Access} \textbf{12}, 69607--69622.

\bibitem[\protect\citeauthoryear{Ren et al.}{2017}]{ref_fasterrcnn}
Ren, S., He, K., Girshick, R., Sun, J.: 2017, Faster R-CNN: Towards real-time object detection with region proposal networks. \textit{IEEE Trans. Pattern Anal. Mach. Intell.} \textbf{39}(6), 1137--1149.

\bibitem[\protect\citeauthoryear{Choi, Brunet, and How}{2009}]{ref_cbba}
Choi, H.-L., Brunet, L., How, J.P.: 2009, Consensus-based decentralized auctions for robust task allocation. \textit{IEEE Trans. Robot.} \textbf{25}(4), 912--926.

\bibitem[\protect\citeauthoryear{Lowe et al.}{2017}]{ref_lowe2017}
Lowe, R., Wu, Y., Tamar, A., Harb, J., Abbeel, P., Mordatch, I.: 2017, Multi-agent actor-critic for mixed cooperative-competitive environments. In: \textit{Proc. NeurIPS}, pp. 6379--6390.

\bibitem[\protect\citeauthoryear{Finn, Abbeel, and Levine}{2017}]{ref_finn2017}
Finn, C., Abbeel, P., Levine, S.: 2017, Model-agnostic meta-learning for fast adaptation of deep networks. In: \textit{Proc. ICML}, pp. 1126--1135.

\bibitem[\protect\citeauthoryear{Chen, Lin, and Bao}{2021}]{ref_chen2021}
Chen, Y., Lin, X., Bao, F.: 2021, Coalition formation game for cooperative multi-UAV target tracking. \textit{IEEE Internet Things J.} \textbf{8}(14), 11456--11467.

\bibitem[\protect\citeauthoryear{Wang et al.}{2022}]{ref_wang2022aitod}
Wang, J., Yang, W., Li, H.-C., Zhang, H., Xia, G.-S.: 2022, Tiny object detection in aerial images. In: \textit{Proc. IEEE/CVF ICPR}, pp. 3791--3798.

\bibitem[\protect\citeauthoryear{Ester et al.}{1996}]{ref_ester1996dbscan}
Ester, M., Kriegel, H.-P., Sander, J., Xu, X.: 1996, A density-based algorithm for discovering clusters in large spatial databases with noise. In: \textit{Proc. KDD}, pp. 226--231.

\bibitem[\protect\citeauthoryear{Dryden}{1952}]{ref_dryden1952}
Dryden, H.L.: 1952, A review of the statistical theory of turbulence. \textit{Q. Appl. Math.} \textbf{1}(1), 7--42.

\bibitem[\protect\citeauthoryear{Jain, Chiu, and Hawe}{1984}]{ref_jain1984fairness}
Jain, R., Chiu, D.-M., Hawe, W.R.: 1984, A quantitative measure of fairness and discrimination for resource allocation in shared computer systems. \textit{DEC Tech. Rep.} TR-301.

\bibitem[\protect\citeauthoryear{Meier, Honegger, and Lee}{2015}]{ref_px4autopilot}
Meier, L., Honegger, D., Lee, P.J.: 2015, PX4: A modular minimal architectural framework for autonomous UAV flight control. In: \textit{Proc. IEEE ICRA}, pp. 2645--2652.

\bibitem[\protect\citeauthoryear{Macenski et al.}{2022}]{ref_ros2humble}
Macenski, S., Foote, T., Gerkey, B., Lalancette, C., Woodall, W.: 2022, Robot Operating System 2: Design, architecture, and uses in the wild. \textit{Science Robotics} \textbf{7}(66), eabm6074.

\bibitem[\protect\citeauthoryear{NDMA}{2024}]{ref_ndrf2024}
National Disaster Management Authority: 2024, Standard operating procedure for drone deployments in humanitarian disaster search and rescue operations. Government of India.

\bibitem[\protect\citeauthoryear{FLIR}{2023}]{ref_flirthermal}
FLIR Systems Inc.: 2023, Thermal imaging fundamentals for unmanned aerial systems in emergency response. Tech. Rep. FLIR-SAR-2023.

\bibitem[\protect\citeauthoryear{Varghese and John}{2026}]{ref_sih2026}
Varghese, A., John, J.: 2026, SkyRescue-AI: Hybrid edge-cloud multi-agent swarm architecture for rapid disaster casualty localization. \textit{TechRxiv Preprint}, doi:10.36227/techrxiv.2026.0401.

\end{thebibliography}

\end{document}
'''

full_main = header + '\n' + body_text + '\n' + end_matter

target_path = r'd:\DEV\Final Year Project\ProjectReport\Journal_Paper\main.tex'
with open(target_path, 'w', encoding='utf-8') as f:
    f.write(full_main)

print('Successfully generated main.tex, characters:', len(full_main))
