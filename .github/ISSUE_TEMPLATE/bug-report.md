name: "🐛 Bug / crash report"
description: >-
  Wrong output, panic, exception, or packaging problem. The
  issue-fixer agent consumes this directly.
title: "[bug] "
labels: ["bug"]
body:
  - type: markdown
    attributes:
      value: |
        Crash or wrong output? Paste everything verbatim — the agent
        reproduces from these fields. Screenshots alone are
        unreadable to it.

  - type: textarea
    id: what-happened
    attributes:
      label: What happened?
      description: And what did you expect instead?
    validations:
      required: true

  - type: textarea
    id: repro
    attributes:
      label: Minimal reproduction (verbatim code + output)
      description: "The exact call and the exact output/traceback. For python, include the `pip install revonorm==<version>` line too."
      placeholder: |
        Python 3.12, revonorm 1.0.0 (pip)
        >> from revonorm import normalize_text
        >> normalize_text("RM10.50 sahaja", language="ms")
        Traceback (most recent call last) ...
        PanicException — unsupported language: ms
      render: shell
    validations:
      required: true

  - type: dropdown
    id: surface
    attributes:
      label: Where did it break?
      options:
        - pip wheel (python)
        - npm @revolab/revonorm (node)
        - npm @revolab/revonorm-web (browser)
        - wasm/cdylib direct
        - not sure
    validations:
      required: true

  - type: input
    id: version
    attributes:
      label: Package version
      placeholder: "1.0.0"
    validations:
      required: true

  - type: textarea
    id: environment
    attributes:
      label: Environment
      description: OS, python/node version, browser if relevant.
      placeholder: Ubuntu 24.04, Python 3.12.6 / Node 20

  - type: textarea
    id: notes
    attributes:
      label: Anything else?
      description: Does it happen every time? Only with certain text? Did it work in an earlier version?
