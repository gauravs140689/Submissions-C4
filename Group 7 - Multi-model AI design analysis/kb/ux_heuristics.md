# UX Heuristics for AI SaaS Landing Pages

This heuristic set extends classic Nielsen-style principles for modern AI product experiences.

## 1) Intent Transparency

### What good looks like
- Users immediately understand core jobs supported by the product.
- The page names boundaries (what the product does and does not do).
- Claims are scoped by context (for example: "for product teams", "for code reviews", "for support agents").

### Red flags
- Broad claims that fit any AI tool.
- Feature lists without problem framing.

### Audit questions
- Can a first-time visitor explain product purpose in one sentence?
- Is the target user segment explicit?

## 2) Time-to-First-Value Orientation

### What good looks like
- Path to first success is clear ("Try sample prompt", "Use template", "Import data").
- Setup effort is visible before commitment.
- Demo assets mirror realistic production usage.

### Red flags
- CTA says "Get started" but no expectation setting on next step.
- Hidden onboarding complexity.

### Audit questions
- Does the page reduce uncertainty about effort and payoff?
- Can a motivated user predict the first 10 minutes accurately?

## 3) Recognition Over Recall for Prompting

### What good looks like
- Prompt examples are domain-specific and outcome-oriented.
- Suggested prompts are grouped by use case.
- Input affordances guide quality prompts (tone, constraints, format hints).

### Red flags
- Empty prompt canvas with no guidance.
- Example prompts are gimmicky and not tied to buyer value.

### Audit questions
- Is prompt quality scaffolding visible before sign-up?
- Are examples aligned to top conversion personas?

## 4) Progressive Disclosure of Complexity

### What good looks like
- Advanced capabilities are discoverable without overwhelming new users.
- Core path is simple; power features are layered later.
- Technical depth (APIs, agents, automation) is presented in digestible chunks.

### Red flags
- Enterprise controls mixed into beginner onboarding blocks.
- Too many decisions at first interaction.

### Audit questions
- Is the first action low cognitive load?
- Are advanced controls separated from initial conversion path?

## 5) Trust Through Explainability

### What good looks like
- Model behavior limits and risk notes are easy to find.
- Data handling posture is explicit.
- Accuracy expectations are framed responsibly.

### Red flags
- Overpromising certainty for probabilistic AI behavior.
- Safety/privacy details buried or absent.

### Audit questions
- Are confidence, risk, and verification needs communicated?
- Does trust copy appear before high-intent conversion moments?

## 6) Consistency Across Message, Visuals, and Flow

### What good looks like
- Visual style and interaction language reinforce the same product promise.
- CTA labels are consistent with funnel stage.
- Section hierarchy follows a coherent decision journey.

### Red flags
- "Try free" in hero but "Book demo" elsewhere without audience split.
- Inconsistent terminology for same feature (assistant/copilot/agent/bot).

### Audit questions
- Are terms and actions consistent throughout the page?
- Does each section logically advance the buying decision?

## 7) Decision Friction Management

### What good looks like
- Objections are answered before form friction appears.
- Pricing, security, and implementation questions are easy to resolve.
- Alternative conversion paths exist by intent (self-serve vs sales-led).

### Red flags
- Aggressive conversion asks without qualification info.
- High-friction form before trust proof.

### Audit questions
- Are blockers handled in sequence (value -> trust -> risk -> action)?
- Is there a clear path for both SMB and enterprise buyers?

## 8) Feedback and State Clarity

### What good looks like
- Interactive demos communicate state changes and latency.
- Loading states are informative, not ambiguous.
- Success states reinforce next best action.

### Red flags
- Simulated interactions with no indication they are mockups.
- Silent failures or frozen states.

### Audit questions
- Does the page make progress and state obvious in interactive areas?
- Is waiting behavior explained clearly?

## 9) Comparative Differentiation Clarity

### What good looks like
- Product is differentiated against known alternatives in concrete terms.
- Tradeoffs are acknowledged honestly.
- "Why choose us" proof is tied to measurable outcomes.

### Red flags
- Competitor references without meaningful distinction.
- Generic feature parity presented as differentiation.

### Audit questions
- Can users explain why this product is better for their specific job?
- Are tradeoffs transparent enough to build trust?

## 10) Heuristic Scoring Framework

Score each heuristic using:
- 0 = Missing/harmful
- 1 = Weak/ambiguous
- 2 = Good baseline
- 3 = Strong and defensible

Interpretation:
- 24 or less: foundational UX gaps; redesign recommended before scale.
- 25-40: workable baseline; prioritize top friction areas.
- 41-55: strong UX; optimize via experiments.
- 56-60: best-in-class candidate.
