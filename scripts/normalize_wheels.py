#!/usr/bin/env python3
"""Rewrite every built wheel as a canonical zip (zero trailing bytes).

The manylinux x86_64 docker build has produced wheels PyPI rejects with
'ZIP archive not accepted: Trailing data' while passing testzip (which
checks entries, not framing). A zipfile round-trip writes a clean
central directory. Run from the repo root; rewrites in place.
"""

import glob
import os
import tempfile
import zipfile

count = 0
for wheel in glob.glob("revonorm-core/dist/*.whl"):
    with tempfile.TemporaryDirectory() as td:
        with zipfile.ZipFile(wheel) as z:
            z.extractall(td)
        tmp = wheel + ".tmp"
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _dirs, files in os.walk(td):
                for f in sorted(files):
                    full = os.path.join(root, f)
                    z.write(full, os.path.relpath(full, td))
    os.replace(tmp, wheel)
    count += 1
    print(f"normalized {wheel}")
print(f"{count} wheels rewritten canonically")
