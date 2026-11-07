# AI Code Trust Studies

Empirical studies of when AI-generated code can be trusted. Each study is written as a short report, with its limits,
a reflection and open directions.

> **Status:** work in progress. Studies are added as they are finished.

## Studies
| # | Study | Question | Status |
|---|---|---|---|
| 01 | Memory or Task Pressure? ([PDF](studies/01-benchmark-audit/report.pdf), [web](studies/01-benchmark-audit/README.md)) | Does a scam-URL benchmark measure model memory or task pressure? | Done, not peer reviewed |
| 02 | Does Rewording a Bug Report Reveal Wrong Tests? ([PDF](studies/02-rephrase-check/report.pdf), [web](studies/02-rephrase-check/README.md)) | Can rephrasing tell a user which of AssertFlip's accepted tests to trust? | Done, not peer reviewed |
| 03 | Model-Built References and Graphs for Car Manuals ([PDF](studies/03-car-manual-qa-proposal/report.pdf), [web](studies/03-car-manual-qa-proposal/README.md)) | Where do people still matter when LLMs build car-assistant knowledge from manuals? | Proposal from reading; no experiment run |
| 04 | Does Human Review Intent Help a Coding Agent? ([PDF](studies/04-review-intent/report.pdf), [web](studies/04-review-intent/README.md)) | Given up front, does a summary of human code review bring an agent's fix closer to what the project merged, and more than a summary of AI-agent review? | Done, not peer reviewed |

## How this was built
Each study states who did what. Code is written with Claude Code under my direction. Commits written with the agent carry a `Co-Authored-By` line.

## Author
Zili Luo, MSc in Computing, Queen's University (2023) · zili.luo@queensu.ca
