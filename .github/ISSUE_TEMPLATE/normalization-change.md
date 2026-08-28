name: "🔧 Normalization rule change / fix"
description: >-
  Change how text is normalized (numbers, currency, dates, times,
  symbols, entities, pronunciation) in the Rust engine. The
  issue-fixer agent consumes this directly.
title: "[norm] "
labels: []
body:
  - type: markdown
    attributes:
      value: |
        **Every field below becomes the agent's specification.** The
        clearer the examples, the better the Rust implementation. The
        issue-fixer will: implement in Rust → regenerate snapshot
        fixtures → run all gates → open a PR labeled
        `needs-test-review`. You review the unit tests, then comment
        `/tests-approved` on the PR.

  - type: textarea
    id: what-happened
    attributes:
      label: What is wrong / what should change?
      description: One paragraph. What does the engine do today, and why is that incorrect?
      placeholder: |
        The engine speaks "RM1.5M" as "satu juta lima ratus ribu ringgit"
        but our TTS dataset uses "M" to mean miliar in Indonesian text,
        so the spoken amount is 1000x too small for language="id".
    validations:
      required: true

  - type: textarea
    id: examples
    attributes:
      label: Input → expected output (the contract)
      description: >-
        THE most important field. One case per line:
        `input text` | `language code` | `exact expected spoken output`.
        The agent turns each row into a snapshot case; ambiguous rows
        produce ambiguous Rust.
      placeholder: |
        `Rp5M` | `id` | `lima miliar rupiah`
        `Rp5M` | `en` | `five million rupiah`
        `suhu -5C` | `ms` | `suhu negatif lima celcius`
    validations:
      required: true

  - type: dropdown
    id: language
    attributes:
      label: Which language(s)?
      options:
        - ms (Malay)
        - id (Indonesian)
        - en (English)
        - zh (Chinese)
        - zh_my (Malaysian Chinese)
        - all languages
        - not language-specific (engine/pipeline)
    validations:
      required: true

  - type: dropdown
    id: feature
    attributes:
      label: Which feature area?
      options:
        - currency (RM/rupiah/$, suffixes K/M/B/T, sen)
        - numbers (cardinals, decimals, digit-by-digit, negatives)
        - dates
        - times (meridians, hour-only, 24h)
        - measurements (km, kg, temperature C/F/K)
        - fractions / x-kali
        - symbols (!, &, ?, URL speech)
        - entities (URL, email, phone, IC, address-slash)
        - pronunciation mappings
        - profiles / feature gating
        - other / not sure
    validations:
      required: true

  - type: textarea
    id: current-output
    attributes:
      label: Current (wrong) output — verbatim
      description: Run the input through and paste the exact wrong output. "It's wrong" without the actual string forces the agent to guess.
      placeholder: |
        `Rp5M` (id) currently → "lima juta rupiah"
      validations:
        required: true

  - type: textarea
    id: edge-cases
    attributes:
      label: Edge cases & boundaries
      description: Inputs that must NOT change, ambiguity notes, things the agent might over-fix.
      placeholder: |
        - "Rp5jt" must keep meaning juta (not miliar)
        - bare "5M" with no currency symbol stays as-is
        - en keeps en-semantics M = million

  - type: textarea
    id: context
    attributes:
      label: Why / source of truth
      description: Where does the expected form come from? (TTS model behavior, dataset convention, native-speaker review, existing Python behavior…)
      placeholder: Validated on the omnivoice TTS server / native speaker review / matches pre-1.0 python output.
