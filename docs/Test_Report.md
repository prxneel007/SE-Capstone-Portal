# Test Summary Report
## Capstone Hub

| | |
|---|---|
| Related | [Test Plan](Test_Plan.md), [SRS](SRS.md) |
| Build tested | Final story branch `feature/US-13-nfr-hardening` (all 13 stories) |
| Environment | Python 3.14 on macOS (local); Python 3.10, 3.11, 3.12 on Ubuntu (GitHub Actions CI) |
| Tools | pytest 9, pytest-cov / coverage 7 (branch mode), flake8 7 |

## 1. Summary

| Metric | Result |
|---|---|
| Test cases executed | **88** |
| Passed | **88** |
| Failed / errors / skipped | 0 / 0 / 0 |
| Statement coverage | 897 of 898 statements (99.9%) |
| **Branch coverage (combined)** | **99%** (233 of 236 branches fully covered) |
| flake8 | 0 warnings |
| CI coverage gate | ≥ 80%, met on every story branch (lowest: 93% on US-01) |
| Execution time | about 12 seconds |

**Verdict:** all exit criteria in the Test Plan (section 5) are met. No open defects.

## 2. Results by feature

| Test file | Feature / requirement | Tests | Result |
|---|---|---|---|
| test_core.py | App factory, health check, CLI (NFR-05/06) | 4 | Pass |
| test_security.py | Login/role decorators, CSRF, safe redirects, event bus (NFR-01) | 10 | Pass |
| test_auth.py | Registration, login, roles (FR-01, NFR-01) | 14 | Pass |
| test_ideas.py | Idea bank: create, edit, delete, search, filter (FR-02, FR-03) | 8 | Pass |
| test_votes.py | Voting (FR-04) | 5 | Pass |
| test_teams.py | Team formation and leave rules (FR-05, NFR-04) | 8 | Pass |
| test_allocation.py | Claim idea, mentor assignment (FR-06) | 6 | Pass |
| test_milestones.py | Milestones, progress, overdue (FR-07, FR-08) | 5 | Pass |
| test_submissions.py | Report upload, versioning, access, size limit (FR-09, NFR-04) | 7 | Pass |
| test_plagiarism.py | Similarity algorithm and flagging (FR-10) | 5 | Pass |
| test_feedback.py | Faculty feedback and grades (FR-11) | 3 | Pass |
| test_notifications.py | Reminders, inbox, event alerts (FR-12, FR-13) | 6 | Pass |
| test_reports.py | Progress report and CSV (FR-14) | 2 | Pass |
| test_nfr.py | Error pages, demo seed, 500-idea performance, viewport (NFR-02, NFR-03) | 5 | Pass |
| **Total** | | **88** | **All pass** |

Several test functions are parameterised or check multiple conditions, so the 37 test cases TC-01 to TC-37 in the Test Plan are spread across these 88 tests.

## 3. Coverage by module

| Module | Statements | Branches | Coverage |
|---|---|---|---|
| allocation.py, core.py, dashboard.py, db.py, errors.py, events.py, feedback.py, milestones.py, plagiarism.py, reports.py, security.py, seed.py, submissions.py, teams.py, votes.py, \_\_init\_\_.py | all covered | all covered | 100% |
| auth.py | 54 | 22 (1 partial) | 99% |
| ideas.py | 95 | 32 (1 partial) | 99% |
| notifications.py | 96 (1 missed) | 24 (1 partial) | 98% |
| **Total** | **898** | **236** | **99%** |

The uncovered pieces are defensive branches, for example an `if` that only matters when a form field is missing entirely. They don't affect any requirement.

## 4. Coverage growth per sprint story

Each story branch was linted and tested before its PR was raised:

| Branch | Tests | Coverage |
|---|---|---|
| US-01 project setup | 14 | 93% |
| US-02 auth and roles | 28 | 96% |
| US-03 idea bank | 36 | 97% |
| US-04 voting | 41 | 97% |
| US-05 teams | 49 | 98% |
| US-06 claim and mentor | 55 | 99% |
| US-07 milestones | 60 | 99% |
| US-08 submissions | 67 | 99% |
| US-09 plagiarism | 72 | 99% |
| US-10 feedback | 75 | 99% |
| US-11 notifications | 81 | 99% |
| US-12 reports | 83 | 99% |
| US-13 hardening | 88 | 99% |

## 5. Non-functional results

| NFR | Check | Result |
|---|---|---|
| NFR-01 Security | Passwords hashed; POST without CSRF token gives 400; `//evil.com` and `https://evil.com` redirects blocked; role checks give 403 | Pass |
| NFR-02 Performance | Idea bank with 500 ideas and votes, sorted by votes | Renders in well under 1 s (limit 1 s) |
| NFR-03 Usability | Friendly 400/403/404/413 pages; viewport meta present; layout collapses below 600 px | Pass |
| NFR-04 Reliability | 413 for uploads over the limit; last member can't delete a team with submissions; one team per idea under concurrent claims | Pass |
| NFR-05 Maintainability | flake8 clean; coverage ≥ 80% gate | Pass (99%) |
| NFR-06 Portability | CI matrix on Python 3.10, 3.11, 3.12 | Pass |

## 6. Defects found during development

| # | Found by | Description | Fix |
|---|---|---|---|
| D-1 | test_core::test_init_db_command | CLI commands ran outside the Flask app context | Added `@with_appcontext` to `init-db`, `seed-demo`, `send-reminders` |
| D-2 | test_notifications::test_daily_run_on_first_request | Test helper didn't commit, so setup changes were rolled back | Test helper now commits after each statement |
| D-3 | Code review | Last member leaving a team would cascade-delete its submitted reports | Leaving is blocked when the team has submissions (TC-15) |
| D-4 | CI on US-01 | Security core under-tested on the first branch (67% < 80% gate) | Added `test_security.py` unit tests (now 100%) |

All defects are fixed and covered by regression tests.

## 7. How to reproduce

```
pip install -r requirements-dev.txt
python -m pytest --cov --cov-report=term-missing
flake8 capstone tests
```
