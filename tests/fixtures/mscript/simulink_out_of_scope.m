% Inert fixture for unsupported Simulink tokens.
model = 'demo.slx';
open_system(model);
sim(model);
app = 'preview.mlapp';
