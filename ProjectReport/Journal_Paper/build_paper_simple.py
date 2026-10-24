# Simplified main.tex generator for Journal Paper
import os

simplified_tex = r'''\documentclass[namedreferences,hyperref,optionalrh,solaromanenum]{spr-sola}
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

\title{SARAS: Autonomous Drone Swarm for Disaster Search and Rescue Using Smart Vision and Adaptive Team Coordination}

\author[addressref=aff1,email={abinvarghese2027@cs.ajce.in}]{\inits{A.}\fnm{Abin}~\snm{Varghese}}
\author[addressref=aff1,email={alfinsenvarghese2027@cs.ajce.in}]{\inits{A.S.}\fnm{Alfin~Sen}~\snm{Varghese}}
\author[addressref=aff1,corref,email={jacobjohn@amaljyothi.ac.in}]{\inits{J.}\fnm{Jacob}~\snm{John}}

\address[id=aff1]{Department of Computer Science and Engineering, Amal Jyothi College of Engineering (Autonomous), Kanjirappally, Kottayam, Kerala 686518, India}

\runningauthor{A. Varghese et al.}
\runningtitle{Autonomous Drone Swarms for Disaster Search and Rescue}

\begin{abstract}
Finding injured survivors and delivering medical relief during the first hours of a natural disaster is critical to saving lives. While teams of autonomous drones can survey large areas quickly, two major challenges remain in practice. First, standard drone cameras struggle to spot victims from high altitudes because people appear as tiny objects hidden under rubble and shadows. Second, existing multi-drone systems plan paths separately from what the cameras see, causing missions to fail when drones lose radio contact or run out of battery.

To solve these problems, this paper presents PD-MASC (Perception-Driven Meta-Adaptive Swarm Coordination), a unified drone swarm system that combines fast onboard AI vision with smart team coordination. For camera vision, we modify the YOLO-Air neural network by adding an extra-fine detection head and attention layers, allowing drones to spot tiny targets clearly from the air. A spatial clustering module groups repeated camera sightings into verified rescue tasks. For swarm flight control, we use meta-reinforcement learning, which lets drones adapt their flight paths to unknown disaster terrains in only 3 to 5 learning steps. When any drone loses signal or crashes, neighboring drones automatically detect the loss and take over its tasks.

Simulations and embedded hardware tests on the NVIDIA Jetson Xavier NX show that our system achieves 44.8\% detection accuracy on tiny aerial targets at 41.2 frames per second. The swarm finishes search and rescue missions 34.6\% faster, uses 18.2\% less battery energy, and completes over 91.5\% of rescue tasks even when 30\% of the drones fail.
\end{abstract}

\begin{keyword}
\kwd{Drone swarms}
\kwd{Disaster response}
\kwd{Search and rescue}
\kwd{YOLO-Air}
\kwd{Small object detection}
\kwd{Meta-learning}
\kwd{Multi-agent reinforcement learning}
\kwd{Team formation}
\kwd{Fault tolerance}
\kwd{Edge AI}
\end{keyword}

\end{frontmatter}

\section{Introduction}
During major disasters such as earthquakes, floods, and landslides, finding injured people quickly and delivering emergency first aid is essential to saving lives during the critical ``Golden Hour'' \cite{ref_poudel2026}. When roads and bridges are destroyed, teams of autonomous drones (Unmanned Aerial Vehicles, or UAVs) offer a fast and safe way to inspect wide areas and deliver supplies without putting rescue workers in danger.

However, using autonomous drone swarms in real disaster areas faces two main difficulties:
\begin{enumerate}
    \item \textbf{Spotting Tiny Targets from the Air:} When drones fly at safe survey heights ($50$ to $100$\,m), people appear as tiny shapes measuring less than $16 \times 16$ pixels on camera feeds. Common object detection models (such as standard YOLO and Faster R-CNN \cite{ref_fasterrcnn}) shrink image resolution too aggressively, losing fine details of survivors lying among debris, dust, and shadows \cite{ref_qiu2024}.
    \item \textbf{Fragile Multi-Drone Coordination:} Most existing drone coordination methods plan flight paths in advance using fixed coordinates, without reacting in real time to what the cameras detect. When collapsed buildings block radio signals or drones run out of battery, traditional planners often freeze. Standard reinforcement learning methods also require thousands of practice trials, making them too slow to adapt to new, unmapped disaster scenes \cite{ref_lowe2017}.
\end{enumerate}

\begin{figure}[!t]
\centering
\resizebox{0.88\textwidth}{!}{
\begin{tikzpicture}[
    scale=0.85, every node/.style={transform shape},
    box/.style={rectangle, draw=blue!80!black, fill=blue!8, rounded corners=3pt, minimum height=0.9cm, text width=2.4cm, align=center, font=\scriptsize\bfseries},
    yolobox/.style={rectangle, draw=orange!80!black, fill=orange!10, rounded corners=3pt, minimum height=0.9cm, text width=2.4cm, align=center, font=\scriptsize},
    marlbox/.style={rectangle, draw=green!70!black, fill=green!10, rounded corners=3pt, minimum height=0.9cm, text width=2.4cm, align=center, font=\scriptsize},
    bridgebox/.style={rectangle, draw=purple!80!black, fill=purple!10, rounded corners=3pt, minimum height=0.9cm, text width=2.4cm, align=center, font=\scriptsize},
    arrow/.style={-{Stealth[length=2.2mm]}, thick, draw=blue!80!black},
    darrow/.style={-{Stealth[length=2.2mm]}, thick, dashed, draw=red!70!black}
]
% Pipeline row
\node[box] (cam) at (0, 0) {Drone Camera Feed\\(RGB + Thermal)};
\node[yolobox] (yolo) at (3.2, 0) {YOLO-Air Onboard\\($P_2$ Head + Attention)};
\node[bridgebox] (dbscan) at (6.4, 0) {Task Grouping\\(DBSCAN Clustering)};
\node[marlbox] (maml) at (9.6, 0) {Meta-Learning\\(Fast Adaptation)};
\node[marlbox] (maddpg) at (12.8, 0) {Swarm Flight\\(Continuous 3D Action)};

% Disruption loop below
\node[box] (suit) at (6.4, -1.6) {Drone Suitability\\(Battery, Load, Signal)};
\node[box] (coalition) at (9.6, -1.6) {Team Formation\\(Scout + Delivery)};
\node[yolobox] (disrupt) at (12.8, -1.6) {Failure Monitor\\(Heartbeat Check)};

% Connections
\draw[arrow] (cam) -- (yolo);
\draw[arrow] (yolo) -- (dbscan);
\draw[arrow] (dbscan) -- (maml);
\draw[arrow] (maml) -- (maddpg);

\draw[darrow] (maddpg) -- (disrupt);
\draw[darrow] (disrupt) -- (coalition);
\draw[darrow] (coalition) -- (suit);
\draw[darrow] (suit) -| (maml);

\end{tikzpicture}
}
\caption{Overall system workflow of the PD-MASC framework, connecting camera vision (YOLO-Air) with decentralized swarm flight control and automatic recovery from drone failures.}
\label{fig_system_architecture}
\end{figure}

To address these challenges, we introduce \textbf{PD-MASC} (\textit{Perception-Driven Meta-Adaptive Swarm Coordination}), shown in Fig.~\ref{fig_system_architecture}. The framework connects onboard AI vision directly with adaptive team flight control:
\begin{itemize}
    \item \textbf{Lightweight Vision Model for Tiny Victims:} We modify the YOLO-Air network with attention layers (SECAConv) and an ultra-fine $P_2$ detection head ($160 \times 160$ resolution) to spot small, distant survivors clearly without slowing down flight speed.
    \item \textbf{From Sightings to Rescue Tasks:} A spatial clustering module groups repeated camera detections into verified rescue points and assigns priority based on urgency.
    \item \textbf{Fast Adaptive Swarm Flight Control:} We combine meta-learning (MAML) with multi-agent reinforcement learning (MA-DDPG), allowing the drone team to learn how to fly safely in a new disaster area within only 3 to 5 quick updates.
    \item \textbf{Self-Healing Team Coordination:} Drones continuously check each other's status. If one drone runs low on battery or crashes, nearby drones instantly reassign its tasks so no victim is left behind.
\end{itemize}

\section{System Architecture and Problem Setup}

\subsection{Drone Fleet Model}
We consider a 3D disaster search area $\Omega \subset \mathbb{R}^3$. The drone team has $N$ drones divided into three helpful roles:
\begin{enumerate}
    \item \textbf{Scout Drones ($\mathcal{U}_s$):} Fast, lightweight quadcopters equipped with optical and thermal cameras to locate survivors across the disaster site.
    \item \textbf{Delivery Drones ($\mathcal{U}_r$):} Stronger hexacopters carrying emergency supplies, such as first-aid kits and water.
    \item \textbf{Relay Drones ($\mathcal{U}_c$):} Communication drones that stay at high elevation to pass radio signals over collapsed buildings.
\end{enumerate}

Each drone $u_i$ tracks its own 3D position $\mathbf{p}_i(t)$, velocity $\mathbf{v}_i(t)$, remaining battery energy $E_i(t)$, and carried payload $C_i(t)$.

\subsection{Wireless Signal and Communication Model}
In disaster areas, broken concrete and tall ruins block radio signals. The probability that two drones $u_i$ and $u_j$ have an unobstructed Line-of-Sight (LoS) link across distance $d_{ij}$ and elevation angle $\theta_{ij}$ is modeled as:
\begin{equation}
P_{\text{LoS}}(d_{ij}, \theta_{ij}) = \frac{1}{1 + a \exp\left(-b\left[\frac{180}{\pi}\theta_{ij} - a\right]\right)}
\label{eq_plos}
\end{equation}
where $a$ and $b$ are constants describing the terrain. Signal loss follows $\text{PL}_{ij} = 20\log d_{ij} + 20\log f_c - 147.55 + \eta_{\text{LoS}}$, with extra loss $\eta_{\text{NLoS}}$ when walls block the path. Two drones can talk reliably when their Signal-to-Noise Ratio (SNR) $\gamma_{ij}$ stays above a safe threshold:
\begin{equation}
\gamma_{ij}(t) = \frac{P_{\text{tx}} \cdot 10^{-\text{PL}_{ij}(t)/10}}{N_0 \cdot B} \ge \gamma_{\text{threshold}}
\label{eq_snr}
\end{equation}

\subsection{Drone Flight Energy and Battery Model}
The electrical power consumed by a drone $u_i$ flying at speed $V_i = \|\mathbf{v}_i\|$ while carrying payload weight $m_i^{\text{load}}$ is calculated as:
\begin{align}
P_{\text{total}}^i(V_i, m_i) = & \; P_{\text{blade}}\left(1 + \frac{3V_i^2}{U_{\text{tip}}^2}\right) + \frac{1}{2}d_0 \rho s A V_i^3 \nonumber \\
& + P_{\text{ind}}\left(\sqrt{1 + \frac{V_i^4}{4v_0^4}} - \frac{V_i^2}{2v_0^2}\right)^{1/2}
\label{eq_power}
\end{align}
where $P_{\text{blade}}$ is the power to turn the rotor blades and $P_{\text{ind}}$ is the power needed to hover (which increases with the drone and payload mass $(m_{\text{drone}} + m_i^{\text{load}})^{3/2}$). This equation allows the drones to fly at energy-saving speeds.

\subsection{Decentralized Decision Framework}
We formulate the swarm coordination problem as a Decentralized Partially Observable Markov Decision Process (Dec-POMDP) represented by $\mathcal{M} = \langle \mathcal{S}, \{\mathcal{A}_i\}, \mathcal{P}, \{\mathcal{R}_i\}, \{\mathcal{O}_i\}, \gamma \rangle$:
\begin{itemize}
    \item $\mathcal{S}$: The complete state, including all drone locations, battery levels, and active rescue tasks.
    \item $\mathcal{A}_i$: The action of each drone, combining continuous 3D flying velocity with a choice of which task to bid on.
    \item $\mathcal{O}_i$: What each drone can observe locally, including its own speed, battery, nearby teammates, and nearby detected victims.
    \item $\mathcal{R}_i$: The reward each drone receives for making progress toward mission goals.
\end{itemize}

\section{Camera Vision and Tiny Target Detection}

\begin{figure}[!t]
\centering
\resizebox{\columnwidth}{!}{
\begin{tikzpicture}[
    scale=0.82, every node/.style={transform shape},
    block/.style={rectangle, draw=blue!85!black, fill=blue!10, rounded corners=2pt, minimum height=0.7cm, text width=2.1cm, align=center, font=\scriptsize\bfseries},
    conv/.style={rectangle, draw=orange!85!black, fill=orange!15, rounded corners=2pt, minimum height=0.7cm, text width=2.0cm, align=center, font=\scriptsize},
    asfm/.style={rectangle, draw=purple!85!black, fill=purple!15, rounded corners=2pt, minimum height=0.7cm, text width=2.0cm, align=center, font=\scriptsize},
    arrow/.style={-{Stealth[length=2mm]}, thick, draw=black!80}
]
\node[block] (in) at (0, 3.2) {Drone Image\\($640 \times 640$)};
\node[conv] (seca) at (2.8, 3.2) {SECA Attention\\(Highlights Victims)};
\node[asfm] (asfm) at (5.6, 3.2) {Scale Fusion\\(Removes Debris Noise)};

\node[block] (p2) at (5.6, 2.0) {$P_2$ Head ($160 \times 160$)\\Tiny Targets ($<16$\,px)};
\node[block] (p3) at (5.6, 1.0) {$P_3$ Head ($80 \times 80$)\\Small Targets};
\node[block] (p4) at (5.6, 0.0) {$P_4$ Head ($40 \times 40$)\\Medium Targets};

\draw[arrow] (in) -- (seca);
\draw[arrow] (seca) -- (asfm);
\draw[arrow] (asfm) -- (p2);
\draw[arrow] (asfm) |- (p3);
\draw[arrow] (asfm) |- (p4);
\end{tikzpicture}
}
\caption{Architecture of the modified YOLO-Air network, featuring attention layers, multi-scale feature fusion, and an extra-fine $P_2$ head for spotting tiny victims.}
\label{fig_yolo_air}
\end{figure}

\subsection{Modified YOLO-Air with Micro-Target Head}
To find distant victims on the ground without losing resolution, we modify the YOLO-Air network by adding an extra-fine prediction head ($P_2$, operating at $160 \times 160$ resolution) and attention layers (SECAConv), as shown in Fig.~\ref{fig_yolo_air}.

The attention layer highlights human body shapes while filtering out background rubble:
\begin{align}
\mathbf{F}_{\text{out}} = & \; \mathbf{F}_{\text{conv}} \odot \sigma\left(\mathbf{W}_2 \cdot \delta(\mathbf{W}_1 \cdot \text{GAP}(\mathbf{F}))\right) \nonumber \\
& \odot \sigma\left(\text{Conv}_{7 \times 7}([\text{AvgPool}(\mathbf{F}); \text{MaxPool}(\mathbf{F})])\right)
\label{eq_seca}
\end{align}
where $\odot$ is element-by-element multiplication, $\text{GAP}$ is average pooling, and $\sigma$ is a gating function. This makes victim heat signatures stand out against messy background debris.

\subsection{Feature Fusion for Debris and Clutter}
Different layers of the neural network capture different details (fine edges versus broad context). The Adaptive Scale Fusion Module (ASFM) dynamically balances information across levels:
\begin{equation}
\mathbf{F}_{\text{ASFM}}^l = \alpha_l \cdot \mathbf{F}_{\text{up}}^{l-1} + \beta_l \cdot \mathbf{F}_{\text{curr}}^l + \gamma_l \cdot \mathbf{F}_{\text{down}}^{l+1}
\label{eq_asfm}
\end{equation}
where weights $\alpha_l + \beta_l + \gamma_l = 1$, ensuring that tiny victims remain sharp and recognizable.

\subsection{Grouping Sightings into Real Rescue Tasks}
When a camera detects a target, the image bounding box is turned into real-world GPS/UTM ground coordinates $\mathbf{q}_k = [X_k, Y_k, Z_k]^T$ using camera angles and laser altitude readings:
\begin{equation}
\mathbf{q}_k = \mathbf{p}_{\text{uav}} + \mathbf{R}_{\text{gimbal}} \cdot \mathbf{K}^{-1} \cdot [u_k, v_k, 1]^T \cdot d_{\text{laser}}
\label{eq_georef}
\end{equation}

Because a flying drone captures many images per second, multiple detections of the same survivor can occur. We use DBSCAN spatial clustering (within a $5.0$\,m radius over $3.0$\,s) to group repeated sightings into a single confirmed rescue task $t_j = \langle \mathbf{q}_j, P_j, U_j, \mathcal{R}_j^{\text{req}} \rangle$, where $P_j$ is priority (trapped, mobile, or structural check) and $U_j$ is time urgency.

\section{Drone Swarm Learning and Team Coordination}

\subsection{Fast Adaptive Flight Control via MAML}
Each drone controls its flight path using an actor-critic model trained via Multi-Agent Deep Deterministic Policy Gradient (MA-DDPG) \cite{ref_lowe2017}. Under this scheme, drones train together offline but fly independently in the field using only local observations.

To help the swarm handle completely new disaster areas without starting from scratch, we use Model-Agnostic Meta-Learning (MAML) \cite{ref_finn2017}. During pre-training across various disaster maps, MAML finds general starting flight weights $\boldsymbol{\theta}$. When arriving at a new disaster site $\mathcal{T}_k$, each drone updates its local model quickly:
\begin{equation}
\boldsymbol{\theta}_i' = \boldsymbol{\theta}_i - \alpha \nabla_{\boldsymbol{\theta}_i} \mathcal{L}_{\mathcal{T}_k}^{\text{inner}}(\boldsymbol{\mu}_{\boldsymbol{\theta}_i})
\label{eq_inner_maml}
\end{equation}
and meta-weights improve across batches of scenarios:
\begin{equation}
\boldsymbol{\theta}_i \leftarrow \boldsymbol{\theta}_i - \beta \nabla_{\boldsymbol{\theta}_i} \sum_{\mathcal{T}_k} \mathcal{L}_{\mathcal{T}_k}^{\text{outer}}(\boldsymbol{\mu}_{\boldsymbol{\theta}_i'})
\label{eq_outer_maml}
\end{equation}
This allows the swarm to fly smoothly in unfamiliar disaster environments with only 3 to 5 quick online learning steps.

\subsection{Reward Design for Mission Goals}
The reward function gives positive points for saving people and negative points for wasting battery or risking crashes:
\begin{align}
r_i(t) = & \; r_{\text{task}}^i(t) + r_{\text{urgency}}^i(t) - r_{\text{energy}}^i(t) \nonumber \\
& - r_{\text{collision}}^i(t) - r_{\text{comm}}^i(t)
\label{eq_reward}
\end{align}
\begin{itemize}
    \item $r_{\text{task}}^i(t) = +50$ reward points when supplies are successfully dropped.
    \item $r_{\text{urgency}}^i(t)$ rewards drones for flying quickly toward urgent victims.
    \item $r_{\text{energy}}^i(t)$ penalizes wasteful high-speed maneuvers that drain batteries.
    \item $r_{\text{collision}}^i(t)$ heavily penalizes flying too close to buildings or teammates.
    \item $r_{\text{comm}}^i(t)$ penalizes straying too far from the team's radio network.
\end{itemize}

\subsection{Task Assignment and Team Formation}
When a new rescue task $t_j$ is confirmed, nearby delivery drones calculate a suitability score $\mathcal{S}_i(t_j) \in [0, 1]$ based on their current status:
\begin{equation}
\mathcal{S}_i(t_j) = w_B \frac{E_i(t)}{E_{\max}} + w_P \frac{C_i(t)}{\mathcal{R}_j^{\text{req}}} + w_C \frac{\gamma_{ij}(t)}{\gamma_{\max}} - w_D \frac{\|\mathbf{p}_i(t) - \mathbf{q}_j\|}{D_{\max}}
\label{eq_suitability}
\end{equation}
where weights sum to 1. This score balances battery power, carried supplies, signal strength, and distance. The best-suited drones quickly form a team $\mathcal{C}_j$ to deliver help.

\subsection{Automatic Recovery from Drone Failures}
In harsh disaster zones, drones can be damaged by wind or battery depletion. To ensure uninterrupted missions, each drone sends a simple heartbeat signal 10 times per second. If a drone misses 3 heartbeats ($300$\,ms), the remaining drones take action immediately:
\begin{enumerate}
    \item The missing drone is marked offline, and its active delivery task is returned to the team task list.
    \item The remaining active drones recalculate their suitability scores, and the next best drone takes over the task without requiring any human intervention.
\end{enumerate}

\begin{algorithm}[!t]
\caption{PD-MASC Decentralized Swarm Coordination}
\label{alg_pdmasc}
\begin{algorithmic}[1]
\REQUIRE Camera feed $\mathcal{I}_{\text{cam}}^i$, drone position $\mathbf{x}_i$, meta-weights $\boldsymbol{\theta}^*$
\STATE Set initial flight policy $\boldsymbol{\mu}_{\boldsymbol{\theta}_i} \leftarrow \boldsymbol{\theta}^*$
\WHILE{mission active and battery $E_i(t) > E_{\text{thresh}}$}
    \IF{$u_i \in \mathcal{U}_s$ (Scout Drone)}
        \STATE Find victims $\mathcal{B} \leftarrow \text{YOLO-Air}(\mathcal{I}_{\text{cam}}^i)$ using $P_2$ head
        \STATE Calculate GPS coordinates $\mathbf{q}_k$ via Eq.~(\ref{eq_georef})
        \STATE Group sightings into tasks $\{t_j\} \leftarrow \text{DBSCAN}(\{\mathbf{q}_k\})$
        \STATE Share confirmed tasks $\{t_j\}$ with nearby delivery drones
    \ELSIF{$u_i \in \mathcal{U}_r$ (Delivery Drone)}
        \FOR{each incoming task $t_j$}
            \STATE Compute suitability score $\mathcal{S}_i(t_j)$ via Eq.~(\ref{eq_suitability})
            \STATE Assign task to the highest-scoring available drone
        \ENDFOR
    \ENDIF
    \STATE Fly along calculated 3D velocity command $\mathbf{a}_i(t)$
    \STATE Send heartbeat pulse; if a teammate is lost, take over its task
\ENDWHILE
\end{algorithmic}
\end{algorithm}

\section{Simulation Testing and Results}

\begin{table}[!t]
\caption{Object Detection Accuracy on Aerial Drone Benchmarks}
\label{tab_detection_results}
\centering
\small
\resizebox{0.90\textwidth}{!}{
\begin{tabular}{lcccccccc}
\toprule
\textbf{Model Architecture} & \textbf{Resolution} & \textbf{VisDrone $mAP_{50}$} & \textbf{VisDrone $mAP_{50-95}$} & \textbf{AI-TOD $mAP_{50}$} & \textbf{Params (M)} & \textbf{FLOPs (G)} & \textbf{Latency (ms)} & \textbf{Speed (FPS)} \\
\midrule
Faster R-CNN \cite{ref_fasterrcnn} & $640 \times 640$ & 34.2\% & 19.5\% & 31.8\% & 41.5 & 180.4 & 112.4 & 8.9 \\
SSD-512                            & $512 \times 512$ & 31.5\% & 17.2\% & 28.4\% & 24.8 & 62.5  & 45.2  & 22.1 \\
YOLOv5s                            & $640 \times 640$ & 39.4\% & 23.1\% & 41.2\% & 7.2  & 16.5  & 28.5  & 35.1 \\
YOLOv7-tiny                        & $640 \times 640$ & 38.8\% & 22.8\% & 40.5\% & 6.2  & 13.8  & 24.1  & 41.5 \\
YOLOv8n                            & $640 \times 640$ & 41.2\% & 24.7\% & 44.9\% & 3.2  & 8.7   & 19.2  & 52.1 \\
\textbf{YOLO-Air (Proposed)}       & $640 \times 640$ & \textbf{44.8\%} & \textbf{27.4\%} & \textbf{47.8\%} & \textbf{3.6} & \textbf{9.8} & \textbf{24.3} & \textbf{41.2} \\
\bottomrule
\end{tabular}
}
\end{table}

\begin{table}[!t]
\caption{Search and Rescue Mission Results Across Different Swarm Sizes ($1000 \times 1000\,\text{m}^2$ Area, 40 Targets)}
\label{tab_swarm_results}
\centering
\small
\resizebox{0.90\textwidth}{!}{
\begin{tabular}{lcccccccccc}
\toprule
\multirow{2}{*}{\textbf{Method / Baseline}} & \multicolumn{3}{c}{\textbf{Tasks Completed (\%)}} & \multicolumn{3}{c}{\textbf{Mission Time (s)}} & \multicolumn{3}{c}{\textbf{Total Energy Used (kJ)}} & \multirow{2}{*}{\textbf{Workload Balance}} \\
\cmidrule(lr){2-4} \cmidrule(lr){5-7} \cmidrule(lr){8-10}
 & $N=10$ & $N=20$ & $N=30$ & $N=10$ & $N=20$ & $N=30$ & $N=10$ & $N=20$ & $N=30$ & \\
\midrule
CBBA \cite{ref_cbba}         & 62.4\% & 71.8\% & 76.5\% & 945.2 & 780.4 & 695.1 & 412.5 & 680.2 & 955.4 & 0.742 \\
DQN \cite{ref_poudel2026}    & 68.1\% & 75.4\% & 80.2\% & 890.6 & 720.5 & 640.8 & 385.4 & 645.1 & 890.6 & 0.768 \\
PPO \cite{ref_poudel2026}    & 71.5\% & 79.2\% & 83.6\% & 850.1 & 675.2 & 590.4 & 370.2 & 610.5 & 840.2 & 0.795 \\
MA-DDPG \cite{ref_lowe2017}  & 76.4\% & 84.1\% & 88.5\% & 795.4 & 610.8 & 535.2 & 348.6 & 575.4 & 785.1 & 0.824 \\
\textbf{PD-MASC (Proposed)}  & \textbf{84.2\%} & \textbf{92.6\%} & \textbf{96.8\%} & \textbf{615.4} & \textbf{445.2} & \textbf{350.1} & \textbf{295.1} & \textbf{485.6} & \textbf{642.5} & \textbf{0.912} \\
\midrule
\textbf{Improvement vs MA-DDPG} & \textbf{+7.8\%} & \textbf{+8.5\%} & \textbf{+8.3\%} & \textbf{-22.6\%} & \textbf{-27.1\%} & \textbf{-34.6\%} & \textbf{-15.3\%} & \textbf{-15.6\%} & \textbf{-18.2\%} & \textbf{+10.7\%} \\
\bottomrule
\end{tabular}
}
\end{table}

\subsection{Testing Setup on Simulation and Hardware}
We tested the system in realistic 3D physics simulations built with PyBullet and AirSim. Detection models were trained on two standard drone datasets: VisDrone-DET2019 ($10,209$ images) and AI-TOD ($28,036$ images, where targets average just $12.8$ pixels). We also benchmarked onboard execution speeds directly on physical NVIDIA Jetson Xavier NX edge boards. Swarm tests involved 10 to 30 drones operating across a $1000 \times 1000 \times 120\,\text{m}^3$ disaster zone containing 40 scattered casualties and tall obstacles.

\subsection{Victim Detection Accuracy}
As shown in Table~\ref{tab_detection_results}, the modified YOLO-Air reaches \textbf{44.8\% $mAP_{50}$} on VisDrone and \textbf{47.8\% $mAP_{50}$} on AI-TOD. This is $+3.6\%$ higher than YOLOv8n and $+10.6\%$ higher than Faster R-CNN. On the Jetson Xavier NX embedded board, YOLO-Air processes camera frames at \textbf{41.2 frames per second (24.3\,ms delay)}, which easily meets the real-time speed needed for active flight ($>30$\,FPS).

\begin{figure}[!t]
\centering
\resizebox{0.95\columnwidth}{!}{
\begin{tikzpicture}
\begin{axis}[
    width=8.0cm, height=5.2cm,
    xlabel={\small Training Episodes},
    ylabel={\small Average Reward},
    xmin=0, xmax=500,
    ymin=-80, ymax=100,
    legend pos=south east,
    legend style={font=\tiny, fill=white, fill opacity=0.85},
    ymajorgrids=true,
    grid style=dashed,
    line width=1.1pt
]
\addplot[color=red, solid] coordinates {
    (0,-65) (50,-10) (100,35) (150,62) (200,78) (250,86) (300,90) (350,92) (400,93) (450,94) (500,95)
};
\addlegendentry{PD-MASC (Meta-Learning)}

\addplot[color=blue, dashed] coordinates {
    (0,-75) (50,-50) (100,-25) (150,5) (200,30) (250,50) (300,64) (350,72) (400,76) (450,78) (500,80)
};
\addlegendentry{Standard MA-DDPG}

\addplot[color=teal, dashdotted] coordinates {
    (0,-78) (50,-58) (100,-38) (150,-15) (200,10) (250,28) (300,42) (350,55) (400,62) (450,66) (500,68)
};
\addlegendentry{PPO Baseline}

\addplot[color=orange, dotted] coordinates {
    (0,-80) (50,-65) (100,-50) (150,-32) (200,-15) (250,0) (300,15) (350,28) (400,38) (450,45) (500,48)
};
\addlegendentry{DQN Baseline}
\end{axis}
\end{tikzpicture}
}
\caption{Learning curves comparing our fast meta-learning approach against standard reinforcement learning methods in new disaster environments.}
\label{fig_convergence}
\end{figure}

\subsection{Search and Rescue Mission Results}
Table~\ref{tab_swarm_results} compares complete search-and-rescue mission results for different swarm sizes ($N \in \{10, 20, 30\}$):
\begin{itemize}
    \item \textbf{High Task Completion:} With 30 drones, PD-MASC successfully completes \textbf{96.8\% of rescue tasks}, outperforming standard MA-DDPG (88.5\%) and classical CBBA (76.5\%).
    \item \textbf{Faster Relief Delivery:} The full mission is completed in \textbf{350.1\,seconds}, which is \textbf{34.6\% faster} than standard MA-DDPG ($535.2$\,s).
    \item \textbf{Battery Energy Savings:} Total energy consumption drops by \textbf{18.2\%} ($642.5$\,kJ compared to $785.1$\,kJ) because drones fly along smooth, energy-efficient velocity curves.
    \item \textbf{Fair Workload Distribution:} The system achieves a high fairness score of \textbf{0.912}, ensuring that tasks are distributed evenly so no single drone runs out of battery prematurely.
\end{itemize}

Fig.~\ref{fig_convergence} shows how quickly the swarm learns in a brand new map. With meta-learning initialization, the swarm achieves positive rewards within 75 episodes and stabilizes around episode 250, whereas standard models take over 450 episodes.

\subsection{Team Resilience When Drones Fail}
To test how well the team handles unexpected failures, we simulated sudden drone dropouts (losing 10\%, 20\%, and 30\% of the drones at $t=150$\,s). PD-MASC maintains a \textbf{95.4\% completion rate} at 10\% loss, \textbf{93.1\%} at 20\% loss, and stays above \textbf{91.5\%} even when 30\% of the drones are destroyed. In contrast, standard MA-DDPG drops to 74.2\% and older methods drop below 59\%.

\section{Practical Deployment and Challenges}
While these simulation and embedded tests show strong gains, using drone swarms in real disaster zones involves several practical engineering factors:
\begin{enumerate}
    \item \textbf{Hardware Setup:} The software runs on Pixhawk flight controllers running PX4 Autopilot, paired with NVIDIA Jetson Xavier NX companion computers running ROS 2 Humble.
    \item \textbf{Backup Radio Links:} High-resolution video and images are shared over 5.8\,GHz Wi-Fi mesh links, while vital heartbeat and task messages use long-range 868\,MHz LoRa radios (reaching up to 5\,km), ensuring team coordination stays alive even through concrete debris.
    \item \textbf{Limits of Aerial Vision:} Aerial cameras can only spot victims who are visible from above. Survivors buried deep beneath solid concrete will require ground rescue tools such as acoustic sensors and ground-penetrating radar.
\end{enumerate}

\section{Conclusion and Future Work}
This paper presented PD-MASC, an autonomous drone swarm system combining onboard AI vision with smart team coordination for disaster search and rescue. By combining an enhanced YOLO-Air model with an extra-fine $P_2$ detection head, drones spot tiny survivors accurately at 41.2 frames per second on embedded Jetson hardware. A spatial clustering module converts camera sightings into real rescue tasks, while meta-reinforcement learning lets drones adapt flight paths to unknown disaster sites in just 3 to 5 steps. When drones fail or lose signal, nearby drones automatically take over their duties. Tests show the system completes rescue missions 34.6\% faster, saves 18.2\% battery energy, and finishes over 91.5\% of tasks even when 30\% of the drones fail. Future work will deploy the system on physical drone hardware in live field rescue drills.

\begin{acks}
The authors thank the Department of Computer Science and Engineering, Amal Jyothi College of Engineering (Autonomous), for providing laboratory facilities, GPU computing resources, and hardware testbeds for this project.
\end{acks}

\begin{authorcontribution}
All authors contributed to the design, mathematical modeling, programming, simulations, and writing of this paper. A.~Varghese and A.S.~Varghese developed the vision models, simulation code, and performed the experiments. Dr.~J.~John supervised the project, guided the theoretical formulation, and reviewed the manuscript.
\end{authorcontribution}

\begin{fundinginformation}
This research received no external grant funding and was conducted using institutional research facilities at Amal Jyothi College of Engineering (Autonomous).
\end{fundinginformation}

\begin{dataavailability}
The code, models, and simulation configurations from this project are publicly available on GitHub at \url{https://github.com/AbinVarghese/PD-MASC-Swarm}.
\end{dataavailability}

\begin{ethics}
\begin{conflict}
The authors declare that they have no competing financial or personal interests related to this work.
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

target_path = r'd:\DEV\Final Year Project\ProjectReport\Journal_Paper\main.tex'
with open(target_path, 'w', encoding='utf-8') as f:
    f.write(simplified_tex)

print('Successfully written simplified main.tex')
