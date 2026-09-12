"""Generate the code reference pages and navigation."""

from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

for path in sorted(Path("zdem_dfn").rglob("*.py")):
    module_path = path.with_suffix("")
    parts = tuple(module_path.parts)

    if parts[-1] == "__main__":
        continue
    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = Path("reference") / path.parent / "index.md"
    else:
        doc_path = Path("reference") / path.with_suffix(".md")

    identifier = ".".join(parts)
    mkdocs_gen_files.set_edit_path(doc_path, path)

    with mkdocs_gen_files.open(doc_path, "w") as f:
        print(f"::: {identifier}", file=f)

    nav[parts] = doc_path.as_posix()

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav.build_literate_nav(nav_file)
