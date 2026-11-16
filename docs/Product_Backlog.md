# Product Backlog and Sprint Plan
## Capstone Hub

Story points use the Fibonacci scale (1, 2, 3, 5, 8). Velocity target: about 25 points per one-week sprint for a team of four.

| ID | User story | Requirements | Points | Owner | Sprint |
|---|---|---|---|---|---|
| US-01 | As the team, we want a project skeleton, database schema and CI pipeline so that everyone can build features on a tested base. | NFR-05, NFR-06 | 3 | Chirra Yuktha Praneel | 1 |
| US-02 | As a user, I want to register and log in with my role so that I see the features meant for me. | FR-01, NFR-01 | 5 | Chirra Yuktha Praneel | 1 |
| US-03 | As a student, I want to browse, search and filter capstone ideas, and propose my own, so that I can find a project I like. | FR-02, FR-03 | 5 | Dhruv Uppalapati | 1 |
| US-04 | As a student, I want to vote for ideas so that popular ideas rise to the top. | FR-04 | 2 | Meghana | 1 |
| US-05 | As a student, I want to create a team or join one with an invite code so that I can work with my friends. | FR-05 | 5 | Dhriti L Krishna | 1 |
| US-06 | As a team, we want to claim an idea and get a faculty mentor so that our project is officially allocated. | FR-06 | 3 | Dhriti L Krishna | 1 |
| US-07 | As a mentor, I want to set milestones with due dates and see each team's progress so that I know who is on track. | FR-07, FR-08 | 5 | Dhriti L Krishna | 2 |
| US-08 | As a team member, I want to upload versioned reports against milestones so that faculty can review our work. | FR-09 | 5 | Meghana | 2 |
| US-09 | As faculty, I want every report automatically checked for plagiarism against other teams so that copied work is flagged. | FR-10 | 8 | Chirra Yuktha Praneel | 2 |
| US-10 | As faculty, I want to give comments and grades on a report so that the team knows what to improve. | FR-11 | 3 | Meghana | 2 |
| US-11 | As a student, I want automatic reminders and an in-app inbox so that I never miss a milestone or feedback. | FR-12, FR-13 | 5 | Dhruv Uppalapati | 2 |
| US-12 | As faculty, I want a progress report of all teams with CSV export so that I can report to the coordinator. | FR-14 | 3 | Meghana | 2 |
| US-13 | As the team, we want friendly error pages, demo data and automated performance and coverage checks so that the product is robust and easy to demo. | NFR-02, NFR-03, NFR-04 | 3 | Chirra Yuktha Praneel | 2 |

## Sprint 1 (19-23 Oct 2026): "Find an idea, form a team"
**Goal:** a working product where users register, explore and vote on ideas, form teams, claim an idea and get a mentor.
Stories: US-01, US-02, US-03, US-04, US-05, US-06. **23 points.**

## Sprint 2 (26-30 Oct 2026): "Track, submit, review"
**Goal:** milestones, report submission with plagiarism check, feedback, reminders and reporting, with the product hardened for the final demo.
Stories: US-07 to US-13. **32 points.**

## Points per member
| Member | Stories | Points |
|---|---|---|
| Chirra Yuktha Praneel (repo owner) | US-01, US-02, US-09, US-13 | 19 |
| Dhruv Uppalapati | US-03, US-11 | 10 |
| Dhriti L Krishna | US-05, US-06, US-07 | 13 |
| Meghana | US-04, US-08, US-10, US-12 | 13 |

## Definition of Done
- Code on a `feature/US-xx-...` branch; PR raised by the story owner with `Closes #<issue>`.
- CI green (flake8, tests on Python 3.10-3.12, coverage ≥ 80%).
- Reviewed and merged by the repo owner; issue closed and moved to Done on the board.
