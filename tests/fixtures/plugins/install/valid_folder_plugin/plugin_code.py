from pathlib import Path

Path("SHOULD_NOT_BE_CREATED_BY_INSTALL.txt").write_text("executed", encoding="utf-8")
