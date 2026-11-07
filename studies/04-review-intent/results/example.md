Drawn with seed `20261107-example` from the 56 complete PRs, leaving out the two spot-check PRs (`scripts/example.py`): **apache/superset #34763** (Python).

**Issue given to every arm** (shortened here):

> #31813 Upload forms have non-actionable error message
> 
> ### Bug description
> 
> When trying to upload a CSV file to Superset, if there's a problem with the data such as a numeric column containing an empty value or a data column with wrong formatting, the modal shows `Database upload file failed` or `Table already exists` without any context about the error. This message does not help users to find what's the problem with their CSV file resulting in a very poor user experience and frequent on-call requests.
> 
> The error should contain more information about what the problem was such as the column, row and type of problem.
> 
> ### Screenshots/recordings
> 
> _No response_
> 
> ### Superset version
> 
> master / latest-dev
> 
> ### Python version
> 
> 3.9
> 
> ### Node version
> 
> 16
> 
> ### Browser
> 
> Chrome
> 
> ### Additional context
> 
> _No response_
> 
> ### Checklist
> 
> - [x] I have searched Superset docs and Slack and didn't find a solution to my problem.
> - [x] I have searched the GitHub issue tracker and didn't find a similar bug report.
> - [x] I have checked Superset's logs for errors and if I found a relevant Python stacktrace, I included it here as text in the "additional context" section.

**Summary of human review (arm B, 147 words):**

> - Track the selected database as one piece of state holding the whole database object, not an id plus a separate parallel state. Duplicate state is unnecessary.
> - Don't add frontend checks for particular engines, such as rejecting Trino table names that contain spaces. Instead, catch failures from the backend step that runs the table-creation statement and return them to the user as clear error messages. This general approach is preferred over checking for specific cases.
> - Keep the maximum number of detailed errors shown, with a note on how many more exist, as a fixed value. Don't make it a new configuration option. The limit depends on how much space the UI has, so admins don't need to tune it.
> - In the tests, set up the shared database-list mock before each test and reset it after each one, rather than repeating it in every test.

**Summary of agent review (arm C, 143 words):**

> The CSV upload should report specific, actionable errors when data fails type conversion. The finished change needs to do the following:
> 
> - **Find all bad values in a column.** Don't stop at the first invalid value. Users should get a full picture of what's wrong with their file. The number of errors actually shown can still be capped.
> - **Keep the display limit configurable.** The cap on how many errors are shown exists to avoid huge responses and a poor experience when a file has thousands of errors. Deployments that have already set their own limit through the existing configuration option must keep that behaviour, so don't replace it with a fixed value.
> - **Test the no-truncation case properly.** When the number of errors is under the limit, the test should confirm that no "and N more errors" style summary appears at all.

**Rubric and Opus verdicts per arm** (met / not_met / cant_tell):

| Item | Behaviour | A | B | C |
|---|---|---|---|---|
| R1 | When a CSV upload sets a column's data type explicitly and some values in that column can't be converted to it (e.g. 'abc' in an int column, 'one point five' in a float column), the upload fails with an error message that names the column and the target type, not a generic 'Database upload file failed'. | not_met | not_met | met |
| R2 | The error message points to where each bad value is: it gives the offending value and the 1-based line number in the file. The line number accounts for the header line and for any configured header_row offset (with the default header, data row index 0 is line 2; with header_row=1 it is line 3). | not_met | not_met | met |
| R3 | The error reports how many invalid values the column has in total, but lists only a capped number of them (the first 5). If there are more, it adds a summary such as '... and N more error(s)' so a large file doesn't produce a huge message. | not_met | not_met | not_met |
| R4 | Empty or null cells are not counted as invalid values in the detailed report. Only non-null values that can't be converted are listed and counted. | not_met | not_met | met |
| R5 | Valid explicit types still work. Integer and float columns (int32/int64/float32/float64, including integer values in a float column) convert to the requested dtype. If a type is given for a column that isn't in the file, it is ignored and no error is raised. Uploads with no explicit types keep pandas' normal type inference. | met | cant_tell | met |
| R6 | The detailed message reaches the user. The generic upload exception handler doesn't swallow it or replace it with a generic message: it passes through the underlying exception's message (or its str()). Also, an explicit upload error raised inside the CSV read isn't re-wrapped by the reader's broader exception handlers. | met | not_met | not_met |
| R7 | If the detailed analysis of invalid values itself fails, or no specific bad rows can be found, the error still names the column and target type and includes the original conversion error text instead of crashing. | not_met | not_met | not_met |
| R8 | The 'table already exists' check is case-insensitive in the sense that a table stored under a lower-cased name also counts as existing, so the 'Table already exists' handling matches what the database actually stores. | not_met | not_met | not_met |

Rubric score: A 0.25, B 0.00, C 0.50.