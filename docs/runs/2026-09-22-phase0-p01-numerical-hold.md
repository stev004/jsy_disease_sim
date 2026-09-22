# P0-1 numerical acceptance hold

This supersedes the push-readiness implication of the earlier director implementation acceptance PASS; that immutable report remains historical evidence. Candidate b5ef032e29c577bce634ce0933b2d7d316ac562e is NOT ready to push as an accepted unit pending numerical review.

A simulation-free director probe confirms that the declared asymptomatic candidate 0.40 minus truth 0.25 yields floating-point error 0.15000000000000002. Compared directly with declared tolerance 0.15, the endpoint is counted outside tolerance. The mathematical declared difference equals the inclusive boundary. The frozen threshold must not be relaxed or retuned.

Primary evidence: docs/runs/2026-09-22-phase0-p01-numeric-probe.log and .txt, exact candidate SHA above. P0-1's remaining Sol peer consult will assess the numerical contract and smallest correct remedy after the required clean CI mirror finishes. Three implementation attempts are already spent; no fourth Luna attempt is authorized. A director fix may only meet the standing one-line-obvious-fix exception; otherwise park a budget extension for Steven. No campaign or main code change.
