name: "🌍 New language support"
description: >-
  Add a new language as a pack. The agent adds the pack module +
  registry entry + snapshot cases — no core pipeline edits.
title: "[lang] "
labels: []
body:
  - type: markdown
    attributes:
      value: |
        Adding a language is adding one **pack** (vocabulary tables +
        a normalizer module). The more of the tables you fill below,
        the less the agent invents. Unknown cells: write `?` — the
        agent will ask in the PR rather than guess silently.

  - type: input
    id: code
    attributes:
      label: Language code (lowercase, e.g. `tl`, `ta`, `vi`)
      placeholder: tl
    validations:
      required: true

  - type: input
    id: name
    attributes:
      label: Language name
      placeholder: Tagalog
    validations:
      required: true

  - type: textarea
    id: numbers
    attributes:
      label: Number words (0–10, teens rule, tens, magnitudes)
      description: What are the spoken words? Is there a special teens rule (like Malay `sebelas`) or a magnitude system (like `万` grouping)?
      placeholder: |
        0=sero, 1=isa, 2=dalawa, 3=tatlo …
        teens: sampu + "isang"?
        1,000,000 = isang milyón
    validations:
      required: true

  - type: textarea
    id: currency
    attributes:
      label: Currency (symbol, unit words, subunit, slang suffixes)
      placeholder: |
        ₱ / PHP → "pisos", subunit "sentimo"
        "5K" = five thousand pisos?

  - type: textarea
    id: dates-times
    attributes:
      label: Dates & times (month names, formats, meridians)
      placeholder: |
        months: Enero, Pebrero, Marso …
        time meridians: umaga (am), tanghali (noon), hapon (pm), gabi (night)

  - type: textarea
    id: symbols
    attributes:
      label: Symbol words (& % @ * ! ? and URL speech)
      description: How should each symbol be spoken? Which are dropped silently? What is "dot"/"slash" in a URL?
      placeholder: |
        & = "at", % = "porsyento", * dropped, ! kept

  - type: textarea
    id: examples
    attributes:
      label: Input → expected output (the contract)
      description: Same format as the rule-change template — the rows become snapshot cases.
      placeholder: |
        `₱500` | `tl` | `limang daang pisos`
        `3:30 pm` | `tl` | `alas-tres y medya ng hapon`
    validations:
      required: true
