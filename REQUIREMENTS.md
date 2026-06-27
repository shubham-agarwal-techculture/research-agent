# Personal Research Agent — Requirements Document

| Field | Value |
|-------|-------|
| **Document version** | 0.1 (Draft for review) |
| **Status** | Draft |
| **Source** | `description.md` |
| **Last updated** | 2026-06-27 |

---

## 1. Executive Summary

The Personal Research Agent is a long-running, memory-aware system that acts as a **personal idea machine**. Users subscribe to topics (predefined subjects or custom themes). Twice per day, the agent autonomously gathers research from multiple sources, runs a multi-step agentic analysis loop, and delivers **interesting, unconventional, original, creative, and diverse** ideas the user can act on.

Unlike a general-purpose chat assistant, this agent is designed to **take intellectual risks**, **retain context across sessions**, **orchestrate external tools and skills**, and **evolve its agentic architecture** as new use cases are discovered.

---

## 2. Problem Statement

Researchers and builders often lack a system that:

- Proactively surfaces relevant material on topics they care about
- Goes beyond summarization to synthesize novel, actionable ideas
- Maintains continuity of thought across days and weeks
- Can be extended with new tools, skills, and reasoning patterns without a full rewrite

Existing chat-based tools typically respond reactively, forget prior context, and produce conservative outputs. This product addresses that gap with a scheduled, agentic, extensible research pipeline.

---

## 3. Goals and Success Criteria

### 3.1 Primary Goals

| ID | Goal |
|----|------|
| G-1 | Deliver twice-daily research digests and idea outputs for subscribed topics |
| G-2 | Produce outputs that are diverse, creative, and non-obvious—not generic summaries |
| G-3 | Maintain persistent memory of prior runs, conversations, and user feedback |
| G-4 | Support tool and skill integration for fetching, parsing, and analyzing research |
| G-5 | Allow the agentic loop and architecture to be modified as requirements evolve |

### 3.2 Success Criteria (Measurable)

| ID | Criterion | Target (initial) |
|----|-----------|------------------|
| SC-1 | Scheduled runs complete successfully | ≥ 95% of scheduled runs per week |
| SC-2 | User-perceived novelty of ideas | User rates ≥ 4/5 on novelty in weekly review |
| SC-3 | Cross-session continuity | Agent references relevant prior context in ≥ 80% of follow-up interactions |
| SC-4 | Time-to-extend | New tool/skill or loop step can be added without changing core orchestration |
| SC-5 | Topic coverage | All active subscriptions receive output on each scheduled run |

*Note: Targets are initial placeholders for review and should be refined with stakeholders.*

---

## 4. Scope

### 4.1 In Scope

- Topic/subject subscription management (including custom topics)
- Scheduled research runs (twice daily)
- Multi-source research ingestion
- Agentic analysis loop with self-questioning and re-analysis
- Idea synthesis and delivery to the user
- Persistent memory across conversations and runs
- Pluggable tools and skills
- Configurable/modifiable agentic loop and architecture

### 4.2 Out of Scope (Initial Release)

- Multi-user / team collaboration
- Public sharing or social features
- Full academic citation management or reference library UI
- Peer-review or publication workflow
- Mobile-native applications (unless explicitly added later)

*Out-of-scope items may be revisited in future phases.*

---

## 5. Stakeholders and Users

### 5.1 Primary User

A single researcher, builder, or curious individual who wants a **personal** system to continuously generate research-informed ideas on chosen topics.

### 5.2 Stakeholders

| Role | Interest |
|------|----------|
| End user | Quality, novelty, and reliability of ideas |
| System maintainer | Extensibility, observability, and safe operation |
| Reviewers (this document) | Clarity of requirements, feasibility, and prioritization |

---

## 6. User Stories

| ID | Story | Priority |
|----|-------|----------|
| US-1 | As a user, I can subscribe to predefined topics so the agent knows what to research | Must |
| US-2 | As a user, I can define custom topics with my own description and constraints | Must |
| US-3 | As a user, I receive research-backed idea outputs twice per day without prompting | Must |
| US-4 | As a user, I can review what sources were consulted and how ideas were derived | Should |
| US-5 | As a user, I can give feedback on ideas so future runs improve | Should |
| US-6 | As a user, I can ask follow-up questions and the agent remembers prior context | Must |
| US-7 | As a maintainer, I can add a new data source or tool without rewriting the core agent | Must |
| US-8 | As a maintainer, I can adjust the agentic loop (steps, prompts, branching) via configuration | Must |
| US-9 | As a user, I can pause, resume, or remove topic subscriptions | Should |

---

## 7. Functional Requirements

### 7.1 Topic Subscription

| ID | Requirement |
|----|-------------|
| FR-1.1 | The system SHALL allow users to create, read, update, and delete topic subscriptions |
| FR-1.2 | A subscription SHALL support predefined subjects and user-defined custom topics |
| FR-1.3 | Each subscription SHALL store at minimum: topic name, description, active/inactive status, and creation date |
| FR-1.4 | The system SHALL support multiple concurrent active subscriptions |

### 7.2 Scheduled Research Runs

| ID | Requirement |
|----|-------------|
| FR-2.1 | The system SHALL execute a full research-and-analysis pipeline **twice per day** for each active subscription |
| FR-2.2 | Run schedule SHALL be configurable (default: two fixed times per day, timezone-aware) |
| FR-2.3 | Failed runs SHALL be retried according to a defined retry policy and logged |
| FR-2.4 | The system SHALL prevent duplicate processing of the same source material within a single run where deduplication is possible |

### 7.3 Research Ingestion

| ID | Requirement |
|----|-------------|
| FR-3.1 | The agent SHALL fetch research material from **multiple heterogeneous sources** (e.g., papers, articles, preprints, web content—exact sources TBD) |
| FR-3.2 | Ingestion SHALL be performed via pluggable connectors/tools |
| FR-3.3 | Retrieved material SHALL be normalized into a common internal representation for analysis |
| FR-3.4 | Source metadata (title, URL, date, origin) SHALL be retained for traceability |

### 7.4 Agentic Analysis Loop

| ID | Requirement |
|----|-------------|
| FR-4.1 | For each run, the agent SHALL execute a **multi-step agentic loop**, not a single-pass summarization |
| FR-4.2 | The loop SHALL include at minimum: initial read/analysis → cross-questioning → re-analysis → second pass over material → further questioning → internal self-conversation |
| FR-4.3 | The agent SHALL be explicitly oriented toward **risk-taking and unconventional thinking** in its synthesis step (within configured safety bounds) |
| FR-4.4 | Loop steps, prompts, and branching logic SHALL be externalized so they can be modified without core code changes |
| FR-4.5 | The agent MAY invoke tools and skills during any loop phase (search, retrieval, computation, domain-specific analysis) |

### 7.5 Idea Synthesis and Delivery

| ID | Requirement |
|----|-------------|
| FR-5.1 | Each completed run SHALL produce a structured output containing: synthesized ideas, supporting rationale, and source references |
| FR-5.2 | Ideas SHALL aim to be **interesting, unconventional, original, creative, and diverse** relative to the topic and prior outputs |
| FR-5.3 | Outputs SHALL be delivered to the user via a defined channel (UI, email, file, or notification—TBD) |
| FR-5.4 | The system SHALL distinguish new ideas from repeats of previously delivered ideas where memory is available |

### 7.6 Memory and Context

| ID | Requirement |
|----|-------------|
| FR-6.1 | The system SHALL persist memory across conversations and scheduled runs |
| FR-6.2 | Memory SHALL include: prior ideas delivered, user feedback, topic evolution, and salient findings from past analyses |
| FR-6.3 | The agent SHALL retrieve relevant memory during both scheduled runs and interactive follow-ups |
| FR-6.4 | Users SHALL be able to inspect or clear memory per topic (Should) |

### 7.7 Tools and Skills Integration

| ID | Requirement |
|----|-------------|
| FR-7.1 | The system SHALL support registration and invocation of external tools (APIs, scrapers, databases, etc.) |
| FR-7.2 | The system SHALL support agent skills (reusable instruction/prompt modules with defined capabilities) |
| FR-7.3 | Tool and skill failures SHALL be handled gracefully without aborting the entire run unless critical |
| FR-7.4 | New tools and skills SHALL be addable without modifying the core orchestration engine |

### 7.8 Interactive Follow-Up

| ID | Requirement |
|----|-------------|
| FR-8.1 | Users SHALL be able to converse with the agent about delivered ideas and source material |
| FR-8.2 | Follow-up conversations SHALL have access to run history and persistent memory |
| FR-8.3 | User feedback during follow-up MAY influence future scheduled runs for the same topic |

### 7.9 Extensibility and Architecture Modification

| ID | Requirement |
|----|-------------|
| FR-9.1 | The agentic loop architecture SHALL be modular (distinct phases with clear inputs/outputs) |
| FR-9.2 | Maintainers SHALL be able to add, remove, reorder, or replace loop phases via configuration |
| FR-9.3 | The system SHALL document extension points for tools, skills, sources, and loop steps |
| FR-9.4 | Architectural changes SHALL not require migration of existing topic subscriptions or memory |

---

## 8. Non-Functional Requirements

### 8.1 Performance

| ID | Requirement |
|----|-------------|
| NFR-1.1 | A scheduled run for a single topic SHOULD complete within an agreed SLA (TBD, e.g., 30 minutes) |
| NFR-1.2 | Interactive follow-up responses SHOULD begin streaming within 5 seconds under normal load |

### 8.2 Reliability and Availability

| ID | Requirement |
|----|-------------|
| NFR-2.1 | Scheduled runs SHALL survive transient source or tool failures via retries and partial results |
| NFR-2.2 | System state (subscriptions, memory, run history) SHALL be durable and recoverable |

### 8.3 Security and Privacy

| ID | Requirement |
|----|-------------|
| NFR-3.1 | All user data, memory, and credentials SHALL be stored securely and accessible only to the owning user |
| NFR-3.2 | API keys and secrets SHALL NOT be logged or exposed in outputs |
| NFR-3.3 | External source fetching SHALL respect rate limits and terms of service |

### 8.4 Observability

| ID | Requirement |
|----|-------------|
| NFR-4.1 | Each run SHALL produce structured logs: start/end time, steps executed, tools invoked, errors |
| NFR-4.2 | Maintainers SHALL be able to inspect run traces for debugging the agentic loop |

### 8.5 Maintainability and Extensibility

| ID | Requirement |
|----|-------------|
| NFR-5.1 | Loop configuration, tools, and skills SHALL be version-controlled independently where practical |
| NFR-5.2 | Changes to prompts or loop structure SHOULD be testable in isolation before production use |

### 8.6 Output Quality

| ID | Requirement |
|----|-------------|
| NFR-6.1 | The agent SHALL prioritize **novelty and diversity** over safe, generic summaries |
| NFR-6.2 | "Risk-taking" behavior SHALL operate within configurable guardrails (e.g., no harmful content, clear speculation labeling) |

---

## 9. Differentiators vs. Simple Chat Agents

| Dimension | Simple Chat Agent | Personal Research Agent |
|-----------|-------------------|---------------------------|
| Trigger | User-initiated | Scheduled + user-initiated |
| Depth | Single-turn or shallow multi-turn | Multi-phase agentic loop with self-questioning |
| Output | Answers questions | Proactively generates ideas |
| Memory | Session-limited or basic | Persistent, topic-aware long-term memory |
| Tools | Optional, ad hoc | First-class, orchestrated tool/skill integration |
| Risk profile | Conservative by default | Encourages unconventional, creative synthesis |
| Architecture | Fixed | Modifiable loop and extensible design |

---

## 10. Conceptual Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                            │
│         (subscriptions · outputs · follow-up chat)               │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     Orchestration Engine                         │
│              (scheduler · loop runner · config)                  │
└─┬──────────────┬──────────────┬──────────────┬──────────────────┘
  │              │              │              │
  ▼              ▼              ▼              ▼
┌────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐
│ Source │  │  Agentic │  │  Memory  │  │ Tools &     │
│ Connect│  │  Loop    │  │  Store   │  │ Skills      │
│  ors   │  │  Phases  │  │          │  │ Registry    │
└────────┘  └──────────┘  └──────────┘  └─────────────┘
```

### 10.1 Agentic Loop (Conceptual Phases)

1. **Gather** — Fetch new material for subscribed topics from configured sources
2. **Initial analyze** — Read and extract key claims, gaps, and tensions
3. **Cross-question** — Generate challenging questions about assumptions and implications
4. **Re-analyze** — Revisit material with those questions in mind
5. **Self-conversation** — Internal dialogue to stress-test and combine ideas
6. **Synthesize** — Produce diverse, creative, actionable idea candidates
7. **Deliver & persist** — Send output to user; update memory

Phases are configurable and reorderable per FR-9.x.

---

## 11. Data Entities (Initial)

| Entity | Description |
|--------|-------------|
| **TopicSubscription** | User-defined research interest with metadata and status |
| **ResearchRun** | A single scheduled or manual execution for one or more topics |
| **SourceDocument** | Normalized ingested material with metadata |
| **IdeaOutput** | Synthesized ideas with rationale and references |
| **MemoryEntry** | Persistent context item (feedback, prior ideas, insights) |
| **Tool/SkillDefinition** | Registered capability available to the agent |
| **LoopConfiguration** | Definition of agentic phases, prompts, and branching |

---

## 12. Assumptions

| ID | Assumption |
|----|------------|
| A-1 | Single-user deployment initially; no multi-tenancy required in v1 |
| A-2 | User has access to required API keys and source credentials |
| A-3 | "Twice daily" means two configurable cron-like triggers in the user's timezone |
| A-4 | LLM or equivalent reasoning backend is available for agentic steps |
| A-5 | User accepts that unconventional outputs may require human judgment |

---

## 13. Open Questions for Review

| ID | Question | Impact |
|----|----------|--------|
| OQ-1 | What are the initial research sources (arXiv, Semantic Scholar, RSS, web search, etc.)? | FR-3.1, tooling |
| OQ-2 | What is the preferred delivery channel (web app, email, Slack, markdown files)? | FR-5.3 |
| OQ-3 | What are the exact default run times and timezone handling rules? | FR-2.1, FR-2.2 |
| OQ-4 | How should "risk-taking" be bounded (speculation labels, content filters, user toggles)? | NFR-6.2 |
| OQ-5 | What memory technology and retention policy (full history vs. summarized)? | FR-6.x |
| OQ-6 | Should runs be per-topic or batched across all subscriptions? | Architecture, cost |
| OQ-7 | What constitutes duplicate idea detection—semantic similarity threshold? | FR-5.4 |
| OQ-8 | Is offline/degraded mode needed when sources are unavailable? | NFR-2.1 |
| OQ-9 | What is the target stack/runtime (Python, Node, Cursor agent SDK, etc.)? | Implementation |
| OQ-10 | Are there budget/LLM token limits per run that constrain loop depth? | FR-4.x, NFR-1.1 |

---

## 14. Phased Delivery (Proposed)

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| **Phase 0** | Foundation | Subscriptions, scheduler, basic ingestion, simple output |
| **Phase 1** | Agentic loop | Multi-phase analysis, self-questioning, idea synthesis |
| **Phase 2** | Memory & interaction | Persistent memory, follow-up chat, feedback loop |
| **Phase 3** | Extensibility | Tool/skill registry, configurable loop, documentation |
| **Phase 4** | Quality & polish | Deduplication, observability, guardrails, UX refinement |

*Phasing is a proposal for review and may be reprioritized.*

---

## 15. Acceptance Criteria (Release Readiness)

The initial release MAY be considered ready when:

- [ ] User can create and manage at least one custom topic subscription
- [ ] System runs twice daily and produces structured idea output
- [ ] Agentic loop executes multiple phases including re-analysis and self-conversation
- [ ] At least two research source connectors are integrated
- [ ] Memory persists across runs and is used in follow-up conversation
- [ ] At least one new tool or skill can be added via documented extension point
- [ ] Agentic loop can be modified via configuration without core rewrite
- [ ] Run logs and errors are inspectable
- [ ] Open questions OQ-1 through OQ-5 are resolved and reflected in implementation

---

## 16. Glossary

| Term | Definition |
|------|------------|
| **Agentic loop** | A multi-step autonomous workflow where the agent iteratively reads, questions, and re-analyzes material |
| **Self-conversation** | Internal multi-turn reasoning within a single run, not shown as final output unless configured |
| **Tool** | An executable capability (API call, script, integration) invoked by the agent |
| **Skill** | A reusable instruction module defining how the agent should behave for a specific task |
| **Topic subscription** | A user-configured research interest that triggers scheduled runs |
| **Idea output** | The final synthesized creative proposals delivered to the user |

---

## 17. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-06-27 | — | Initial draft derived from `description.md` |

---

## 18. Review Checklist

Use this checklist when reviewing this document:

- [ ] Goals and success criteria align with the original vision
- [ ] Functional requirements are complete and testable
- [ ] Non-functional requirements are realistic for v1
- [ ] Out-of-scope items are acceptable
- [ ] Open questions are answered or assigned owners
- [ ] Phasing matches delivery expectations
- [ ] Differentiators are accurately captured
- [ ] Acceptance criteria are sufficient for sign-off
