# Adaptive discovery questions

Ask one question per turn. Start from facts already provided, skip answered
dimensions, and stop as soon as the remaining choices no longer change the
recommendation or file manifest. A detailed initial brief may justify moving
directly to the research summary.

## Core sequence

1. **Outcome:** What should the project deliver, and for whom?
2. **Project shape:** Application, service, library, CLI, data system, monorepo,
   or another form?
3. **Language and runtime:** What is fixed, preferred, or open to recommendation?
4. **Quality horizon:** Experiment, production-track MVP, or long-lived system?
5. **Team and governance:** Solo, small team, multi-team, or public contributors?
6. **Runtime and distribution:** Where will it run or be published?
7. **Repository host and CI:** Hosted service, local-only repository, existing
   organizational standard, or no CI for now?
8. **Assistant stack:** Which coding agents or local harnesses will actually use
   the repository?
9. **Hard constraints:** Security, compliance, licenses, internal tooling,
   compatibility, budget, or deadlines?

## Fast-exit test

Before asking another question, check whether its answer could change the stack,
profiles, verification command, governance, or file list. If not, stop discovery
and say: “I have enough context to research and recommend a concrete plan. Shall
I present it?” This remains one question.

## Follow-up rules

- Ask a distribution question for libraries and CLIs.
- Ask package ownership and root-tooling questions for monorepos.
- Ask data sensitivity and retention questions for systems handling user data.
- Ask deployment constraints only when deployment is in the requested scope.
- Ask no provider question when the user explicitly chose local-only and no CI.
- Do not turn examples into a checklist the user must answer all at once.
