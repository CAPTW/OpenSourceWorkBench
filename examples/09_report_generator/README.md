# Report Generator Example

Export the curated HeatSink_Flow demo project to a deterministic HTML report:

```powershell
.venv\Scripts\python.exe -m osw.cli project-demo-json --out artifacts\report\demo_project.json
.venv\Scripts\python.exe -m osw.cli report-export artifacts\report\demo_project.json --out artifacts\report\demo_report.html
```

Report export is data-only. It does not execute solvers, scripts, MATLAB,
Octave, or external commands.
