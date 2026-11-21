# Plan, Direct (whole file in the prompt, no tools), sample-00000

Cost $0.864. Verbatim model output:

Here is the plan I would follow. I'm not answering yet.

**1. Build the person registry**
- Find every roster line of the form "the community roster records X under identifier P-nnn and also uses the familiar names Y". These give the only valid ID-to-name mapping.
- Only people with a roster ID can be returned, because the output needs person-ID strings.
- Index each person by full name ("Nadia Reed") and by the alias ("N. Reed").
- Check that each alias maps to exactly one ID. If an initial plus surname could belong to two people, I won't attribute a fact to either unless the context settles it.

**2. Build the organization-to-city table**
- Collect statements like "Org 031 is based in Halifax" and "Organization 026 is based in Calgary". Treat "Org N" and "Organization N" as the same entity.
- Classify each city as coastal or inland. Coastal: Halifax, Vancouver, Victoria, St. John's, Lunenburg. Inland: Calgary, Edmonton, Regina, Winnipeg, Ottawa.
- Keep only organizations whose city is known and coastal. If an organization has no location statement, c1 can't be satisfied for it.

**3. Extract the three facts per person, across all passages**
- **c1:** "currently works for / works for Org N" where Org N is coastal. A person's employer and the employer's city appear in different passages, so I join them.
- **c2:** a present-tense "routinely travels by train/bus/subway/tram".
  - Exclude "no longer does", "used the X once", "plans to use X in the future", and any other past or one-off wording.
- **c3:** a present-tense "works the night shift".
  - Exclude "in a former role", "used to work", and "works the day shift".
- Normalize name forms across all passages: full names, initials, lowercase text, and quoted first-person speech such as "I, omar foster, …". Treat a first-person "I" as the named speaker only when the passage names them.

**4. Intersect and verify**
- Keep a person only if all three facts are present, each current, and each tied to the same resolved identity.
- For every candidate, re-read the source passages to confirm tense, negation and the organization's city.
- Sort the IDs lexicographically and emit `{"matches": [...]}`.

**What could cause misses or false positives**
- Missing a person because their facts are split across passages, or appear under an alias, in lowercase, or in a quoted-speech format.
- Counting a past or negated fact as current, such as "no longer", "used to", "former role", "once" or "in the future". This is the most likely source of wrong inclusions.
- Treating an inland city as coastal, or missing an organization's city because of "Org" versus "Organization" spelling.
- Attributing a fact to the wrong person when two people share an initial and surname.
- Assuming a person works nights or commutes from only a nearby mention, without confirming it refers to them.
- Including someone who has no roster ID.
