% define and input the parameters
fstring = input("Enter the function: ", 's');
f = inline(fstring)
df = inline(diff(str2sym(fstring)))
x = input("Enter initial value: ");
tol = 1e-2;
rerror = 1;
counter = 0;

% iterative newton algorithm
while (rerror>tol)
    xold = x;
    x = x - f(x)/df(x);
    rerror = abs((x-xold)/x);
    counter=counter+1;
end 

% display output
disp("The root is:")
disp(x)
disp("The number of iterations = ")
disp(counter)