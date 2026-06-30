# MATLAB/Octave Script Agent Rules

This directory owns MATLAB/Octave-compatible script and data preview workflows.

- `.m` and `.mat` handling is preview-first. Parse, inspect, and summarize
  before any project mutation.
- Do not execute arbitrary `.m` scripts by default.
- Do not support or claim Simulink, `.slx`, `.mlapp`, or proprietary MATLAB
  toolbox compatibility.
- Treat scripts and `.mat` contents as untrusted input. Surface file mutation,
  shell escape, subprocess, and network intent during preview when detectable.
- Figure output should map toward FigureDataset and report evidence.
- Unit tests must use small local fixtures and must not require MATLAB, Octave,
  network access, or proprietary toolboxes.
