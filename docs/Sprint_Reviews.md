# Sprint Reviews and Retrospectives
## Capstone Hub

# Sprint 1: "Find an idea, form a team"
**Planned dates:** 19-23 Oct 2026 · **Jira:** Capstone Sprint 1 · **GitHub milestone:** Sprint 1

## Sprint goal
A working product where users register, explore and vote on ideas, form teams, claim an idea and get a mentor.

## Committed vs delivered

| Story | Owner | Points | Delivered |
|---|---|---|---|
| US-01 Project setup, CI | Praneel | 3 | ✅ |
| US-02 Registration, login, roles | Praneel | 5 | ✅ |
| US-03 Idea bank | Dhruv | 5 | ✅ |
| US-04 Idea voting | Meghana | 2 | ✅ |
| US-05 Team formation | Dhriti | 5 | ✅ |
| US-06 Claim idea and mentor | Dhriti | 3 | ✅ |
| **Total** | | **23** | **23 / 23** |

## Demo (sprint review)
Shown in the Sprint 1 video (`videos/Sprint1_Demo.mp4`): register and log in, browse/search/filter the idea bank, upvote, create a team and join with an invite code, claim an idea, and a faculty member takes the team as mentor.

## Retrospective
*(Written by the Scrum Master from the sprint record: PRs, CI runs and Jira history.)*

| | Notes |
|---|---|
| What went well | All 6 stories (23 points) delivered. Clear story ownership per person. CI ran tests on every PR, so broken code never reached `main`. |
| What didn't go well | Stacking each feature branch on the previous one made merges fragile: deleting a merged base branch auto-closed PR #18. Some PRs were merged by their authors instead of the owner, without review. |
| What we'll do differently | Only the repo owner merges (agreed with the team). Merge strictly in order and delete a branch only after the next PR is retargeted to `main`. Review PRs within a day. |
| Attendees | Praneel, Dhruv, Dhriti, Meghana |

# Sprint 2: "Track, submit, review"
**Planned dates:** 26-30 Oct 2026 · **Jira:** Capstone Sprint 2 · **GitHub milestone:** Sprint 2

## Sprint goal
Milestones, report submission with plagiarism check, feedback, reminders and reporting, with the product hardened for the final demo.

## Committed vs delivered

| Story | Owner | Points | Delivered |
|---|---|---|---|
| US-07 Milestones and progress | Dhriti | 5 | ✅ |
| US-08 Report submission | Meghana | 5 | ✅ |
| US-09 Plagiarism check | Praneel | 8 | ✅ |
| US-10 Faculty feedback | Meghana | 3 | ✅ |
| US-11 Reminders and notifications | Dhruv | 5 | ✅ |
| US-12 Progress report and CSV | Meghana | 3 | ✅ |
| US-13 Error pages, demo data, NFR checks | Praneel | 3 | ✅ |
| **Total** | | **32** | **32 / 32** |

## Demo (sprint review)
Shown in the Sprint 2 video (`videos/Sprint2_Demo.mp4`): mentor adds milestones, team updates status and sees progress/overdue, uploads a report, the plagiarism check flags a copied report, faculty posts feedback and a grade, reminders appear in Alerts, and the progress report is exported to CSV.

## Retrospective
*(Written by the Scrum Master from the sprint record: PRs, CI runs and Jira history.)*

| | Notes |
|---|---|
| What went well | All 7 stories (32 points) delivered; 55/55 across both sprints. The plagiarism check and CSV report worked first time in the demo. CI stayed green on `main` after every merge. |
| What didn't go well | Self-merged PRs #24-#26 landed on stacked branches instead of `main`, so an extra integration PR (#27) was needed. Retargeting a PR to `main` did not re-run CI, so checks had to be triggered by hand. |
| What we'll do differently | Branch each story from `main` instead of stacking. Turn on branch protection so only the owner can merge and CI must pass. Start reviews earlier in the sprint. |
| Attendees | Praneel, Dhruv, Dhriti, Meghana |

# Velocity

| Sprint | Committed | Completed |
|---|---|---|
| Sprint 1 | 23 | 23 |
| Sprint 2 | 32 | 32 |
| **Total** | **55** | **55** |
