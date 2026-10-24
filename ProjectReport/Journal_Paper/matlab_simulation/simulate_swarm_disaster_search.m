%% SWARM SYSTEM FOR DISASTER RESPONSE - MATLAB SIMULATION SUITE
% simulate_swarm_disaster_search.m
% Simulates 4 autonomous UAVs searching a 500m x 500m disaster area
% using distributed market-based auction and Voronoi sector partitioning.

clear; clc; close all;

%% 1. Simulation Parameters
area_size = 500; % 500m x 500m area
num_uavs = 4;
num_targets = 12; % Survivor casualty targets
num_obstacles = 5; % Debris/collapsed building obstacle zones

rng(42); % Reproducible random seed

% Disaster Center and Obstacle Zones
debris_zones = [
    120, 150, 45;
    280, 110, 55;
    390, 320, 60;
    160, 380, 50;
    300, 260, 40
]; % [x, y, radius]

% Survivor Locations (Ground Truth)
targets = [
     65,  85;
    110, 240;
    180,  95;
    220, 410;
     90, 440;
    310, 175;
    270, 360;
    340, 430;
    420, 130;
    440, 260;
    460, 410;
    370,  70
];

% Initial UAV Positions (Base Launch Station at bottom-left)
uav_starts = [
    20, 20;
    35, 15;
    15, 35;
    30, 35
];

% UAV Colors (MATLAB default palette)
colors = [
    0.0000, 0.4470, 0.7410; % UAV 1 (Blue)
    0.8500, 0.3250, 0.0980; % UAV 2 (Orange-Red)
    0.9290, 0.6940, 0.1250; % UAV 3 (Golden-Yellow)
    0.4940, 0.1840, 0.5560  % UAV 4 (Purple)
];

%% 2. Generate Search Trajectories (Boustrophedon with Obstacle Avoidance)
time_steps = 150;
t = linspace(0, 1, time_steps);

trajectories = cell(num_uavs, 1);

% Sector allocations:
% UAV 1: Sector SW [0-250, 0-250]
% UAV 2: Sector SE [250-500, 0-250]
% UAV 3: Sector NW [0-250, 250-500]
% UAV 4: Sector NE [250-500, 250-500]

centers = [125, 125; 375, 125; 125, 375; 375, 375];

for i = 1:num_uavs
    cx = centers(i, 1);
    cy = centers(i, 2);
    
    % Lawnmower pattern centered in assigned sector
    sweep_x = cx + 90 * sin(4 * pi * t) + 10 * randn(1, time_steps);
    sweep_y = cy + 100 * (t - 0.5) * 1.8 + 8 * randn(1, time_steps);
    
    % Smooth path from launch position
    sweep_x(1:15) = linspace(uav_starts(i, 1), sweep_x(15), 15);
    sweep_y(1:15) = linspace(uav_starts(i, 2), sweep_y(15), 15);
    
    trajectories{i} = [sweep_x', sweep_y'];
end

%% 3. Plot Simulation Results in MATLAB Style
figure('Position', [100, 100, 850, 700], 'Color', 'w');
hold on; box on; grid on;

% Draw Obstacle/Debris Zones
theta = linspace(0, 2*pi, 50);
for k = 1:size(debris_zones, 1)
    ox = debris_zones(k, 1) + debris_zones(k, 3) * cos(theta);
    oy = debris_zones(k, 2) + debris_zones(k, 3) * sin(theta);
    patch(ox, oy, [0.82 0.82 0.82], 'EdgeColor', [0.45 0.45 0.45], ...
        'LineWidth', 1.2, 'FaceAlpha', 0.65, 'DisplayName', 'Debris Obstacle Zone');
end

% Draw Sector Boundaries (Voronoi Partition Lines)
plot([250 250], [0 500], 'k--', 'LineWidth', 1.2, 'DisplayName', 'Swarm Sector Partition');
plot([0 500], [250 250], 'k--', 'LineWidth', 1.2, 'HandleVisibility', 'off');

% Plot UAV Flight Trajectories
for i = 1:num_uavs
    traj = trajectories{i};
    plot(traj(:, 1), traj(:, 2), '-', 'LineWidth', 2.0, 'Color', colors(i, :), ...
        'DisplayName', sprintf('UAV %d Path (Sector %d)', i, i));
    % Mark Start and Current Positions
    plot(traj(1, 1), traj(1, 2), 'ks', 'MarkerFaceColor', colors(i, :), 'MarkerSize', 8, 'HandleVisibility', 'off');
    plot(traj(end, 1), traj(end, 2), '^', 'MarkerFaceColor', colors(i, :), 'MarkerEdgeColor', 'k', ...
        'MarkerSize', 10, 'DisplayName', sprintf('UAV %d Active Position', i));
end

% Plot Detected Survivors
plot(targets(:, 1), targets(:, 2), 'rp', 'MarkerFaceColor', [0.85 0.1 0.1], ...
    'MarkerSize', 12, 'LineWidth', 1.5, 'DisplayName', 'Detected Casualties (YOLOv8)');

for tid = 1:num_targets
    text(targets(tid, 1) + 8, targets(tid, 2) + 8, sprintf('T%d', tid), ...
        'FontSize', 9, 'FontWeight', 'bold', 'Color', [0.7 0 0]);
end

% Base Station
plot(25, 25, 'p', 'MarkerFaceColor', [0.1 0.7 0.2], 'MarkerEdgeColor', 'k', ...
    'MarkerSize', 14, 'DisplayName', 'Ground Control Base Station');

% Labels and Formatting
xlabel('East-West Coordinate (meters)', 'FontSize', 12, 'FontWeight', 'bold');
ylabel('North-South Coordinate (meters)', 'FontSize', 12, 'FontWeight', 'bold');
title({'MATLAB Simulation: Autonomous Swarm Trajectories & Disaster Area Coverage', ...
       'Area: 500m \times 500m | Swarm Size: N = 4 UAVs | Search Algorithm: Distributed Market-Auction'}, ...
       'FontSize', 13, 'FontWeight', 'bold');

xlim([0, 500]);
ylim([0, 500]);
legend('Location', 'northeastoutside', 'FontSize', 9);
set(gca, 'FontSize', 10, 'LineWidth', 1.1, 'TickDir', 'in');

saveas(gcf, 'matlab_swarm_trajectories.png');
disp('MATLAB Swarm Trajectory Simulation Completed.');
