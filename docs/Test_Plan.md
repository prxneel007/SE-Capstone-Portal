# Test Plan
## Capstone Hub

| | |
|---|---|
| Version | 1.0 |
| Related | [SRS](SRS.md), [Design Document](Design_Document.md) |

## 1. Objectives
Verify that every functional (FR-01 to FR-14) and non-functional (NFR-01 to NFR-06) requirement in the SRS is met, and keep it verified automatically on every change.

## 2. Scope
**In scope:** all routes, business rules, access control, plagiarism and reminder algorithms, CLI commands, error handling.
**Out of scope:** browser compatibility testing beyond a manual check, load testing beyond the NFR-02 timing test, penetration testing.

## 3. Approach
| Level | Tool | What |
|---|---|---|
| Unit | pytest | Pure functions: `validate_registration`, `clean_tags`, `parse_due`, `shingles`, `similarity`, `best_match`, `extract_text`, `generate_reminders` |
| Integration | pytest + Flask test client | Each route end-to-end against a fresh temporary SQLite database, logged in as different roles |
| Non-functional | pytest | CSRF, password hashing, 403/404/413 pages, 500-idea timing test, viewport meta |
| Static analysis | flake8 | Style and unused-code checks |
| Coverage | pytest-cov (line + branch) | Gate at 80% in CI |
| Manual / demo | Browser | Sprint review demos using `seed-demo` data, mobile width check |

Test design techniques: equivalence partitioning and boundary values (password length 7/8, team size 4/5, similarity 40% threshold, due date today/yesterday), decision tables for permissions (student / member / mentor / other faculty / admin), and state transitions for milestones (pending → in progress → done).

## 4. Environment
- Python 3.10, 3.11, 3.12 on Ubuntu (GitHub Actions) and macOS (developer machines).
- Each test gets a new SQLite file in a temporary directory and a pinned date (`FAKE_TODAY = 2026-10-20`) so date logic is deterministic.

## 5. Entry and exit criteria
- **Entry:** feature branch builds; PR links a backlog issue.
- **Exit (per PR):** CI green: flake8 clean, all tests pass on all 3 Python versions, coverage ≥ 80%.
- **Exit (release):** all test cases below pass; no open high-severity defects.

## 6. Test cases

| TC | Requirement | Test (file::function) | Expected result |
|---|---|---|---|
| TC-01 | FR-01 | test_auth::test_register_and_login | Account created, password hashed, login redirects to dashboard |
| TC-02 | FR-01 | test_auth::test_duplicate_email_rejected | "already exists" error |
| TC-03 | FR-01 | test_auth::test_validate_registration (5 cases) | Each invalid field gives its error |
| TC-04 | FR-01 | test_auth::test_faculty_needs_code | Faculty created only with correct code |
| TC-05 | FR-01 | test_auth::test_bad_login, test_logout | Wrong password rejected; logout ends session |
| TC-06 | NFR-01 | test_auth::test_csrf_enforced, test_login_next_is_safe | POST without token gets 400; `//evil.com` redirect blocked |
| TC-07 | FR-02 | test_ideas::test_create_and_view_idea, test_create_idea_validation | Idea saved with normalised tags; invalid input rejected |
| TC-08 | FR-02 | test_ideas::test_edit_and_delete_by_author_only, test_admin_can_edit_any_idea | Non-authors get 403; admin allowed |
| TC-09 | FR-03 | test_ideas::test_search_filter_and_sort | Keyword and domain filters narrow results |
| TC-10 | FR-04 | test_votes::test_vote_toggle, test_one_vote_per_user_and_sorting | Toggle works; most-voted idea listed first |
| TC-11 | FR-04 | test_votes::test_cannot_vote_own_idea | Author vote refused |
| TC-12 | FR-05 | test_teams::test_create_team_and_join, test_team_rules | Invite code works (case-insensitive); duplicates refused |
| TC-13 | FR-05 | test_teams::test_team_is_full_at_four | 5th member refused (boundary) |
| TC-14 | FR-05 | test_teams::test_team_page_access, test_leave_team | Non-members get 403; last member leaving deletes team |
| TC-15 | NFR-04 | test_teams::test_last_member_cannot_leave_with_submissions | Leave refused, data kept |
| TC-16 | FR-06 | test_allocation::test_claim_and_release_idea, test_claim_rules | One idea per team and one team per idea |
| TC-17 | FR-06 | test_allocation::test_faculty_mentor_flow, test_admin_assigns_mentor | Mentor rules enforced |
| TC-18 | FR-07 | test_milestones::test_mentor_adds_and_team_updates | Milestones created; status updated |
| TC-19 | FR-07 | test_milestones::test_milestone_validation_and_permissions | Bad date and bad status rejected; outsiders 403 |
| TC-20 | FR-08 | test_milestones::test_mentor_adds_and_team_updates | Progress 50%, overdue counted correctly |
| TC-21 | FR-09 | test_submissions::test_upload_versions_and_download, test_upload_per_milestone_versioning | Versions 1, 2; download returns same bytes |
| TC-22 | FR-09 | test_submissions::test_upload_validation, test_pdf_text_extracted | .exe, empty and broken PDF rejected; PDF text extracted |
| TC-23 | FR-09 | test_submissions::test_access_control | Other students get 403 |
| TC-24 | NFR-04 | test_submissions::test_upload_size_limit | Over-limit upload gets 413 |
| TC-25 | FR-10 | test_plagiarism::test_shingles_and_similarity, test_best_match | Identical = 100%, unrelated = 0% |
| TC-26 | FR-10 | test_plagiarism::test_copied_report_is_flagged | Copied report ≥ 40%, appears on flagged list |
| TC-27 | FR-10 | test_plagiarism::test_same_team_versions_not_compared | Own versions give 0% |
| TC-28 | FR-11 | test_feedback::test_faculty_feedback_visible_to_team | Team sees comment and grade |
| TC-29 | FR-11 | test_feedback::test_feedback_validation_and_permissions | Students 403; empty or invalid grade rejected |
| TC-30 | FR-12 | test_notifications::test_reminders_due_soon_and_overdue | 5 reminders, re-run creates 0 |
| TC-31 | FR-12 | test_notifications::test_daily_run_on_first_request, test_cli_send_reminders | Automatic daily run and CLI work |
| TC-32 | FR-13 | test_notifications::test_inbox_open_and_read_all, test_event_notifications | Badge count, own-only, safe links, event notifications |
| TC-33 | FR-14 | test_reports::test_report_and_csv | Correct %, overdue, reports, CSV columns |
| TC-34 | FR-14 | test_reports::test_reports_staff_only | Students 403 |
| TC-35 | NFR-02 | test_nfr::test_idea_list_fast_with_500_ideas | < 1 s |
| TC-36 | NFR-03 | test_nfr::test_error_pages, test_csrf_error_page, test_viewport_meta_present | Friendly error pages; viewport present |
| TC-37 | NFR-05/06 | CI workflow | flake8 clean, coverage ≥ 80% on Python 3.10-3.12 |

## 7. Defect management
Defects are raised as GitHub issues with the `bug` label, linked to the failing test case, and fixed through a PR that adds a regression test.

## 8. Schedule
| When | Activity |
|---|---|
| Sprint 1 (19-23 Oct) | TC-01 to TC-17 written with the features |
| Sprint 2 (26-30 Oct) | TC-18 to TC-37; full regression in CI |
| Final demo | Test summary report (`docs/Test_Report.md`) generated from the CI run |

## 9. Responsibilities
Each story owner writes the tests for their story; the repo owner (Praneel) reviews tests in the PR and maintains CI.
