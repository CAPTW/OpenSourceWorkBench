x = [0, 1, 2];
figure('visible', 'off');
plot(x, x);
print('-dpng', 'figure_one.png');
figure('visible', 'off');
plot(x, x.^2);
print('-dpng', 'figure_two.png');
