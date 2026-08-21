name: Pull request
description: Contribute a change to the New Body control plane
labels: []
body:
  - type: textarea
    id: summary
    attributes:
      label: Summary
      description: What does this PR change and why?
    validations:
      required: true
  - type: dropdown
    id: type
    attributes:
      label: Change type
      options:
        - New subsystem / sensor suite
        - Power delivery topology
        - Chassis / form-factor
        - Telemetry / instrumentation
        - Refactor / internal
        - Docs / tooling
  - type: textarea
    id: testing
    attributes:
      label: Testing & validation
      description: Confirm `make test lint` passes and describe any new tests.
    validations:
      required: true
  - type: checkboxes
    id: checks
    attributes:
      label: Checklist
      options:
        - label: "Tests added/updated and passing (`make test`)"
        - label: "Lint clean (`make lint`)"
        - label: "Docs/ARCHITECTURE.md updated if extension points changed"
        - label: "Type hints and docstrings maintained"
