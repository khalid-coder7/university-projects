% define and input the parameters
f = inline(input("Enter the function: ", 's'));
a = input("Enter a: ");
b = input("Enter b: ");
m = (a+b)/2;
tol = 1e-9;
rerror = 1;
counter = 0;

% iterative bisection algorithm
while(abs(rerror) > tol)
    mold = m;
if f(m)*f(b) > 0
    b = m;
    m = (a+b)/2;
elseif f(m)*f(b) < 0
    a = m;
    m = (a+b)/2;
else
    break;
end
rerror = (m-mold)/m;
counter=counter+1;
end

% display output
disp("The root is:")
disp(m)
disp("The number of iterations = ")
disp(counter)