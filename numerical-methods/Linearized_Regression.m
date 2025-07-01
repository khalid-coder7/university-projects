% linearized model - Y = a1*X + a0
x = [0 4 8 16 24 30];
y = [12 18 20 26 26 22];
X = x; % specify X
Y = y; % specify Y
coeff_matrix = [length(X) sum(X); sum(X) sum(X.^2)];
free_terms = [sum(Y); sum(X.*Y)];
unkowns = coeff_matrix\free_terms;
a0 = unkowns(1);
a1 = unkowns(2);
a = a0 % specify a
b = a1 % specify b
Yav = mean(Y);
st = sum((Y - Yav).^2);
sr = sum((Y - (a1*X + a0)).^2);
r2 = (st - sr)/st

% plot specific model
x_axis = min(x):0.1:max(x);
y_axis = b*x_axis+a;
plot(x,y,"*",x_axis,y_axis)
