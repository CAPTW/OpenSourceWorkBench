% Simple plot preview fixture.
% Shows basic plotting calls without side effects.
x = 0:0.1:1;
y = sin(2*pi*x);
figure;
plot(x, y);
title('Sine preview');
xlabel('x');
ylabel('sin(x)');
grid on;
