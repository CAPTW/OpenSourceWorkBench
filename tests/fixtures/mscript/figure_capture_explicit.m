x = [0, 1, 2];
y = [0, 1, 4];
figure('visible', 'off');
plot(x, y);
title('OSW explicit figure capture');
print('-dpng', 'explicit_plot.png');
print('-dsvg', 'explicit_plot.svg');
