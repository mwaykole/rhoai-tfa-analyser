---
name: debugger-dashboard
description: >
  Use when analyzing "Dashboard" component failures from RHOAI test results.
  Covers RHOAI Dashboard UI tests, Selenium/browser timing issues, DOM state
  errors, and element visibility problems.
allowed-tools: Bash(*/debugger-dashboard/scripts/*.py:*),Bash(*/tools/rp-client/*.py:*)
---

# Dashboard Debugger

## RP Component
This skill handles the `Dashboard` component from ReportPortal launches.

## Key Concepts

- UI tests are inherently flaky (timing dependent)
- No cluster inspection needed (UI-only tests)
- StaleElement errors are usually test automation issues
- ElementNotInteractable usually means element not visible yet

## Known Failure Patterns

### Test Automation Issues (most common)
- `StaleElementReference|StaleElementReferenceException` → DOM changed during test, need better waits
- `ElementNotInteractable|element.*not.*clickable` → Element not visible yet, loading issue
- `NoSuchElement|element.*not.*found` → Element selector changed or not rendered
- `timeout.*click|timeout.*element` → Element not clickable in time

### Product Bugs
- `500.*Internal.*Server.*Error` on dashboard API → Backend failure
- `dashboard.*crash|dashboard.*unavailable` → Dashboard service down
- Consistent failure across multiple runs with same error → Likely real bug

### Infrastructure Issues
- `connection.*refused.*dashboard` → Dashboard pod not running
- `ERR_CONNECTION_TIMED_OUT` → Network/route issue to dashboard

## Diagnosis Steps

1. Read test failure logs
2. Identify if it's a timing/DOM issue (most common) or actual product defect
3. Check if same test passes on retry → Flaky
4. If error is `StaleElement`, `NoSuchElement`, or timeout → Test Automation Issue
5. If error is consistent 500 or service unavailable → Product Bug
6. Classify and output structured JSON

## Notes

- Most Dashboard failures are Test Automation Issues (timing)
- Only classify as Product Bug if the dashboard itself is broken
- Consider explicit waits over implicit waits in test recommendations
