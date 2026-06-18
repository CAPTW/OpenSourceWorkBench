# v0.1.4 post-EXP-018 environment repair

## 1. Context
- OSW-EXP-018A blocked on SSH auth.
- OSW-EXP-018B completed remote push via HTTPS using gh-auth transport.
- `origin` SSH remains configured and may still fail for some operations.
- `v0.1.4-rc1` remains unchanged and public prerelease.

## 2. Editable install repair
- **Before import path**: `C:\Users\USER\source\repos\Workbench\src\osw\__init__.py`
- **Before CLI version**: `osw 0.1.2`
- **Repair command run**: `.venv\\Scripts\\python.exe -m pip install --no-deps -e .`
- **After import path**: `D:\dev\repos\Workbench\src\osw\__init__.py`
- **After CLI version**: `osw 0.1.4rc1`
- `open-solver-workbench` remains installed from local editable checkout under `D:\dev\repos\Workbench`.
- No dependency upgrades were performed.

## 3. Duplicate-file hygiene
- Inventory scanned for untracked names containing `'(1)'`.
- **Duplicates found**: 12
- **Exact duplicate**: 0
- **Divergent**: 12
- **Orphan**: 0
- **Unknown**: 0
- **Quarantine path**: `artifacts/hygiene/duplicate_files_backup/OSW-MAINT-016`
- `duplicate_inventory.json` and `README.md` were written in quarantine path.
- All found duplicates were moved to preserve data and remove workspace clutter.

## 4. Timeout-cleanup tests
- Focused runner/timeout tests:
  - `pytest tests/unit -q -k "timeout or runner"` -> `51 passed, 933 deselected`
  - `pytest tests/unit/test_cli_surface.py -q` -> `28 passed`
  - `pytest tests/unit/test_qa_tools.py -q` -> `7 passed`
- No timeout-specific failure observed after repair.
- **Hardening changes applied**: none.
- Full suite was executed after repairs and remained stable.

## 5. GUI investigation
- Aggregate GUI suite command:
  - `pytest tests/gui -q`
- Result: `156 passed, 5 skipped` in ~8:55.
- No per-file fallback was required.

## 6. Recommended QA command pattern
- Use `.venv\\Scripts\\python.exe` for local QA and CLI verification.
- Avoid process-local `PYTHONPATH` overrides after this repair path correction.
- For aggregate GUI slowness in other environments, use per-file fallback:
  - `pytest <test_file> -q` for each file under `tests/gui`.

## 7. Non-goals
- No release mutation
- No tag mutation
- No dependency install/upgrade beyond local editable reinstall
- No solver execution
- No issue closure
- No solver validation claims beyond scope

## 8. Check outcomes
- `gh`/release metadata and local checks after repair all passed.
- `tests/unit` and `tests/gui` both passed.
- `ruff` and maintenance QA scripts passed.
