# Deviations from the Submitted Plan
## Capstone Hub

The Mini-Project Deliverables Part-2 (item 2i) ask that deviations from the submitted documents be documented and explained at the final demo. These are all known deviations.

| # | Area | Planned | What actually happened | Reason / impact |
|---|---|---|---|---|
| 1 | Sprint dates | Sprint 1: 19-23 Oct, Sprint 2: 26-30 Oct | Sprint scope, stories and points followed the plan, but branches, PRs and merges happened in November | The team fell behind the course calendar. The sprint labels in GitHub and Jira keep the planned dates so the plan stays traceable. |
| 2 | Implementation tool | Not specified | Code was written with an AI coding assistant (Claude) and reviewed by the team | Allowed by Part-2 item 2e ("You can use GPTs of your choice to implement the project"). Each member is responsible for explaining their own stories. |
| 3 | Pull request flow | Each owner writes code and raises a PR | Code for each story was prepared on its own branch (`feature/US-xx-...`); each story owner raised the PR for their own story; the repo owner reviewed and merged | Matches the rule that the assigned member raises the PR (2c) and the repo owner reviews and merges (2d). |
| 3a | Merge path for US-05..US-07 | Repo owner merges each PR into `main` | Dhriti's PRs #24-#26 were merged by the author into the stacked story branches instead of `main`; the repo owner brought the same three commits into `main` through integration PR **#27** (no new code) | Teammate had write access and merged without owner review. Agreed rule going forward: only the repo owner merges. |
| 4 | Stacked branches | Independent feature branches | Each story branch builds on the previous one, so PRs are merged strictly in order US-01 to US-13 | The modules depend on each other (for example voting needs ideas, claiming needs teams). Stacking avoided merge conflicts. |
| 5 | Jira project | A separate Jira project | Stories live in the existing SCRUM project under epic **SCRUM-6** (SCRUM-7 to SCRUM-19), with sprints "Capstone Sprint 1" and "Capstone Sprint 2" | The Jira connector can't create projects; using an epic keeps the backlog separate from the earlier lab tasks. |
| 6 | Backlog tool | GitHub Project (Part-2 item 1a) | Both a GitHub Project board **and** Jira are used, kept in sync | GitHub is what Part-2 asks for; Jira matches the course schedule ("Jira backlog"). |
| 7 | Plagiarism scope | "Plagiarism checks" | Reports are compared with other teams' reports in the system, not with internet sources | Internet comparison needs paid APIs. Documented as future scope (SRS section 6). |
| 8 | Reminders | "Automated progress reminders" | In-app notifications, generated daily and by a cron command; no e-mail/SMS | E-mail needs an SMTP account; future scope. |
| 9 | Report file types | Any report | PDF, TXT and Markdown, max 10 MB | Text has to be extractable for the plagiarism check. DOCX is future scope. |

No functional requirement in the SRS was dropped. All 14 FRs and 6 NFRs are implemented and tested (see [Test Report](Test_Report.md)).
