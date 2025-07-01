% هذا الكود من صنع الطلاب المسؤولين عن تسليمه
clc; clear; close all;

% main code
b = [2 1]; a = [1 0.1 -0.72]; N = 10000; skip = 1000; tabs = 10;
u = randn(N + skip, 1); d = filter(b, a, u); 
u = u(skip + 1:end); d = d(skip + 1:end); N = length(u);
r = zeros(tabs, 1); for k = 0:tabs - 1; r(k + 1) = (1/N) * sum(u(1:N - k) .* u(k + 1:N)); end; R = toeplitz(r);
p = zeros(tabs, 1); for k = 0:tabs - 1; p(k + 1) = (1/N) * sum(d(k + 1:N) .* u(1:N - k)); end
mu_max = 2 / max(eig(R));
w_opt = inv(R) * p; var_d = var(d); MMSE = var_d - w_opt' * p - p' * w_opt + w_opt' * R * w_opt; % el optimum weiner
iterations = 2000; % 3adad el iterations for each run
runs = 100; % 3adad el runs for each value of mu
mus = [0.01, 0.005, 0.0015];
mse_curves = zeros(iterations, length(mus)); % kol column feeh el average mse values for each mu
w_avg = zeros(tabs, length(mus)); % kol column feeh el average w for each mu
MMSE_mus = zeros(length(mus), 1); % vector feeh el average MMSE for each mu
for mu_i = 1:length(mus)
    mu = mus(mu_i);
    mse_all = zeros(iterations, runs); % kol column feeh el mse value ba3d kol iteration for each run
    w_all = zeros(tabs, runs); % kol column feeh el w ba3d ma 5elset el iterations for each run
    for run = 1:runs
        w = zeros(tabs, 1); % vector el w for each iteration for each run for each mu
        for iter = 1:iterations
            w = w - mu * (R * w - p);
            J = var_d - w' * p - p' * w + w' * R * w;
            mse_all(iter, run) = J;
        end
        w_all(:, run) = w;
    end
    w_avg(:, mu_i) = (1/runs)*sum(w_all,2);
    mse_curves(:, mu_i) = (1/runs)*sum(mse_all, 2);
    MMSE_mus(mu_i) = (1/runs)*sum(mse_all(end, :),2);
end
h = impz(b, a, tabs);

% plots
figure; hold on; grid on;
set(gca, 'YScale', 'log');
ylim([1e-1, 1e2])
colors = ['r', 'g', 'b'];
for i = 1:length(mus)
    plot(1:iterations, mse_curves(:, i), 'Color', colors(i), 'DisplayName', ['\mu = ' num2str(mus(i))])
end
legend show
xlabel('Iteration')
ylabel('MSE (J(n))')
title('Steepest Descent MSE vs Iteration (Log Scale)')

% prints
fprintf('The R matrix:\n'); disp(R); fprintf('The p vector:\n'); disp(p);
fprintf('Maximum theoretical mu: %f\n\n', mu_max);
fprintf('The actual system impulse response weights:\n'); disp(h);
fprintf('The optimal Weiner filter weights are:\n'); disp(w_opt);
for mu_i = 1:length(mus); fprintf('For mu = %f, the weights are:\n', mus(mu_i)); disp(w_avg(:, mu_i)); end
fprintf('Mininmum Mean Square Error for optimal Weiner filter weights: %f\n\n', MMSE);
for mu_i = 1:length(mus); fprintf('Minimum Mean Square Error for mu = %f: %f\n\n', mus(mu_i), MMSE_mus(mu_i)); end
%%

close all; clc;

% main code
T = 0.2; N = 200; a_x = 2; a_y = 10;
x = zeros(6, N); x(:,1) = [0;0;a_x;0;0;a_y]; y = zeros(2, N);
F = [1 T T^2/2 0 0 0; 0 1 T 0 0 0; 0 0 1 0 0 0; 0 0 0 1 T T^2/2; 0 0 0 0 1 T; 0 0 0 0 0 1];
C = [1 0 0 0 0 0; 0 0 0 1 0 0]; Q = diag([0.1 0.1 0 0.5 1 0]); R = 100 * eye(2);

for k = 2:N
    x(:,k) = F * x(:,k-1) + mvnrnd(zeros(6,1), Q)';
    y(:,k) = C * x(:,k) + mvnrnd(zeros(2,1), R)';
end

x_estimate = zeros(6, N); P = 600 * eye(6);
for k = 2:N
    [x_estimate(:,k), P] = LKalman(F, C, Q, R, y(:,k), x_estimate(:,k-1), P);
end

% plots
measuredPosColor = [0, 102, 255]/255;   
estimatedPosColor = [0,255,0]/255;   
truePosColor = [255, 51, 0]/255;      
estimatedXColor = [255, 204, 0]/255;      
trueXColor = [255, 51, 0]/255;          
estimatedYColor = [51, 204, 255]/255;   
trueYColor = [0, 102, 255]/255;        
lineWidth = 2.5;

figure; hold on; grid on;
plot(x(1,:), x(4,:), 'Color', truePosColor, 'LineWidth', lineWidth)
plot(y(1,:), y(2,:), 'x', 'Color', measuredPosColor, 'MarkerSize', 8)
plot(x_estimate(1,:), x_estimate(4,:), '--', 'Color', estimatedPosColor, 'LineWidth', lineWidth)
xlabel('X (m)'); ylabel('Y (m)')
legend('True', 'Measured', 'Estimated', 'Location', 'best')
title('2D Position Tracking')

figure; hold on; grid on;
MSE_x = cumsum((x(1,:) - x_estimate(1,:)).^2) ./ (1:N);
MSE_y = cumsum((x(4,:) - x_estimate(4,:)).^2) ./ (1:N);
plot(MSE_x, 'Color', trueXColor, 'LineWidth', lineWidth)
plot(MSE_y, 'Color', trueYColor, 'LineWidth', lineWidth)
xlabel('Time Index (n)')
ylabel('Position MSE (m^2)')
legend('MSE Position X', 'MSE Position Y', 'Location', 'best')
title('Mean Squared Error')

figure; hold on; grid on;
plot(x(2,:), 'Color', trueXColor, 'LineWidth', lineWidth)
plot(x_estimate(2,:), '--', 'Color', estimatedXColor, 'LineWidth', lineWidth)
plot(x(5,:), 'Color', trueYColor, 'LineWidth', lineWidth)
plot(x_estimate(5,:), '--', 'Color', estimatedYColor, 'LineWidth', lineWidth)
xlabel('Time Index (n)')
ylabel('Velocity (m/s)')
legend('True V_x', 'Estimated V_x', 'True V_y', 'Estimated V_y', 'Location', 'best')
title('Velocity')

figure; hold on; grid on;
plot(x(3,:), 'Color', trueXColor, 'LineWidth', lineWidth)
plot(x_estimate(3,:), '--', 'Color', estimatedXColor, 'LineWidth', lineWidth)
plot(x(6,:), 'Color', trueYColor, 'LineWidth', lineWidth)
plot(x_estimate(6,:), '--', 'Color', estimatedYColor, 'LineWidth', lineWidth)
xlabel('Time Index (n)')
ylabel('Acceleration (m/s^2)')
legend('True A_x', 'Estimated A_x', 'True A_y', 'Estimated A_y', 'Location', 'best')
title('Acceleration')

% Given Kalman Filter Function
 function [x, P] = LKalman(F, C, QN, RN, y, xo, Po)

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
% implements the linear kalamn filter for the STATE SPACE MODEL
%
% F: the system matrix
% C: the measurement matrix
% y: the measurement (desired sequence)
% QN: the covariance matrix of the system noise v
% RN: the covariance matrix of the measurement noise w
% xo: state initial condition
% Po: state estimate innitial covariance matrix
%
%               April 28, 2024
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 1- PROPAGATION STEP
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% A- propagate the state to the next step

x = F*xo;

% B-propagate the covariance matrix P

P = F*Po*F'+QN;


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 2- KALMAN GAIN COMPUTSTION STEP
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

[N,M] = size(C);

if M ==1
    C = C';
end

% A-compute the measurment prediciton covariance (innovation)

S = C*P*C'+RN;

% B-Kalman Gain

K = P*C'*inv(S);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 3- CORRECTION STEP
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% the predicted measurement of the next step

y_hat = C*x;

% A-correct the predicted estimate
error = y-y_hat;

x = x +K*error;

% B-corret the covariance estimate

P = P - K*S*K';
 end

%%

clc; clear; close all;

function netbp
%NETBP Uses backpropagation to train a network

%%%%%%% DATA %%%%%%%%%%%
x = [0 0 0 0 1 1 1 1];
y = [0 0 1 1 0 0 1 1];
z = [0 1 0 1 0 1 0 1];
input = [x; y; z];
target = [0 1 1 0 1 0 0 1];

% Initialize weights and biases
rng(5000);
W2 = 0.5*randn(4,3); W3 = 0.5*randn(3,4); W4 = 0.5*randn(1,3);
b2 = 0.5*randn(4,1); b3 = 0.5*randn(3,1); b4 = 0.5*randn(1,1);

% Forward and Back propagate
eta = 0.05; % learning rate
Niter = 1e6; % number of SG iterations
savecost = zeros(Niter,1); % value of cost function at each iteration
for counter = 1:Niter
    k = randi(8); % choose a training point at random
    xk = input(:,k);
    % Forward pass
    a2 = activate(xk,W2,b2);
    a3 = activate(a2,W3,b3);
    a4 = activate(a3,W4,b4);
    % Backward pass
    delta4 = a4.*(1-a4).*(a4 - target(k));
    delta3 = a3.*(1-a3).*(W4'*delta4);
    delta2 = a2.*(1-a2).*(W3'*delta3);
    % Gradient step
    W2 = W2 - eta*delta2*xk';
    W3 = W3 - eta*delta3*a2';
    W4 = W4 - eta*delta4*a3';
    b2 = b2 - eta*delta2;
    b3 = b3 - eta*delta3;
    b4 = b4 - eta*delta4;
    % Monitor progress
    newcost = cost(W2,W3,W4,b2,b3,b4); % display cost to screen
    savecost(counter) = newcost;
end

% Show decay of cost function
save costvec
semilogy([1:1e4:Niter],savecost(1:1e4:Niter))

    function costval = cost(W2,W3,W4,b2,b3,b4)
        costvec = zeros(8,1);
        for i = 1:8
            xk = [x(i); y(i); z(i)];
            a2 = activate(xk,W2,b2);
            a3 = activate(a2,W3,b3);
            a4 = activate(a3,W4,b4);
            costvec(i) = norm(target(i) - a4,2);
        end
        costval = norm(costvec,2)^2;
    end % of nested function

end

function y = activate(x,W,b)
%ACTIVATE Evaluates sigmoid function.
%
% x is the input vector, y is the output vector
% W contains the weights, b contains the shifts
%
% The ith component of y is activate((Wx+b)_i)
% where activate(z) = 1/(1+exp(-z))
y = 1./(1+exp(-(W*x+b)));
end