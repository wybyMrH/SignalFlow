# Technical Research Record

Use this only when a confirmed requirement creates a concrete technical choice.

## Question

Write the concrete project question first. Research should resolve a requirement or boundary, not fill an empty project with technology names.

- Requirement or boundary: `[To be confirmed]`
- Existing responsibility: `[To be confirmed]`
- Why research is needed now: `[To be confirmed]`

## Project shape and downstream work

State which actual platform, component, runtime, or ownership boundary raises this question. Compare options against that boundary, and explain which later implementation stage and verification surface the choice affects. Avoid carrying one project's architecture or slicing method into another project by default.

- Confirmed project characteristics relevant to this choice: `[To be confirmed]`
- Responsibility and system boundaries affected: `[To be confirmed]`
- Backend, frontend, mobile, worker, or other stages affected: `[only actual boundaries; To be confirmed]`
- Evidence required at each affected boundary: `[To be confirmed]`

## Candidate comparison

Compare only candidates that could actually serve this boundary. Primary sources and versioned evidence matter more than popularity.

| Candidate | Relevant capability | Integration boundary | Failure/retry/persistence behavior | Version/license/cost | Source |
| --- | --- | --- | --- | --- | --- |
| `[To be confirmed]` | `[To be confirmed]` | `[To be confirmed]` | `[To be confirmed]` | `[To be confirmed]` | `[Official docs or source repository]` |

## Smallest proof

Describe the smallest isolated check that can distinguish fit from assumption, including what it cannot prove.

- Fixed non-sensitive input: `[To be confirmed]`
- Real boundary exercised: `[To be confirmed]`
- Fixture or substitute used: `[To be confirmed]`
- Observed result and limits: `[To be confirmed]`
- Date and version: `[To be confirmed]`

## Decision or open question

Record adoption, rejection, or the question that remains for the user. Do not silently add a dependency from this record.

`[To be confirmed]`

Do not add a dependency because it is popular or because a search snippet looks convincing. Record what the proof does not establish and how the candidate can be removed or replaced.
