% OSW preview fixture for figure-style script import.
x = linspace(0, 1, 5);
y = sin(2 * pi * x);
figure('visible', 'off');
plot(x, y);
title('OSW preview fixture');
print('-dpng', 'simple_plot.png');
print('-dsvg', 'simple_plot.svg');
