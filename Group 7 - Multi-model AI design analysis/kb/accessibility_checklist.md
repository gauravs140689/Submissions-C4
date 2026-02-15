# Accessibility Checklist for AI SaaS Landing and Prompt-First Interfaces

This checklist is WCAG-oriented and adapted for modern AI web experiences.

## 1) Contrast and Color Semantics

### Standards
- Body text contrast meets at least 4.5:1.
- Large text and essential UI labels meet at least 3:1.
- Focus indicators are clearly visible against all backgrounds.
- Meaning is never conveyed by color alone.

### AI SaaS-specific checks
- Syntax-highlighted code blocks remain readable in both light and dark themes.
- "Success/error/warning" states in prompt results include icon/text cues beyond color.

## 2) Typography and Readability

### Standards
- Base font size supports comfortable reading across devices.
- Line length and line height support scanning and comprehension.
- Headings follow logical hierarchy without skipping levels.

### AI SaaS-specific checks
- Prompt outputs with dense text include spacing, headings, or chunking.
- Long model responses avoid wall-of-text formatting.

## 3) Keyboard Navigation and Focus Management

### Standards
- All actionable controls are keyboard reachable.
- Tab order follows visual and logical order.
- No keyboard traps in modals, menus, or command palettes.
- Focus remains visible and persistent during navigation.

### AI SaaS-specific checks
- Prompt composer, template selector, and output actions are fully keyboard operable.
- Copy/download/share controls in response blocks are keyboard accessible.

## 4) Forms, Inputs, and Validation

### Standards
- Every input has an associated visible label.
- Instructions and constraints are available before submission.
- Validation errors are specific, nearby, and programmatically associated.
- Recovery path is obvious (how to fix and resubmit).

### AI SaaS-specific checks
- Prompt input constraints (token/context/file limits) are explained clearly.
- File upload interactions include accepted formats and error recovery guidance.

## 5) Semantics and Landmarks

### Standards
- Use semantic structure for navigation, main content, and footer.
- Buttons and links reflect true interaction type.
- Dynamic content updates are announced where appropriate.

### AI SaaS-specific checks
- Streaming or incrementally rendered AI output is announced accessibly.
- Tabbed "Examples/Results/Docs" interfaces expose proper ARIA roles and states.

## 6) Media, Motion, and Animation Safety

### Standards
- Motion does not trigger discomfort or disorientation.
- Users can pause/stop non-essential animation.
- No essential information is conveyed only through animation.

### AI SaaS-specific checks
- Typing animations and auto-scroll in generated outputs can be reduced or disabled.
- Demo videos include captions and do not autoplay with sound.

## 7) Touch Targets and Mobile Accessibility

### Standards
- Interactive targets are easy to tap on mobile.
- Spacing prevents accidental taps.
- Orientation and zoom do not break core functionality.

### AI SaaS-specific checks
- Prompt input, submit CTA, and result actions remain usable one-handed.
- Sticky toolbars do not occlude essential content at 200% zoom.

## 8) Content Clarity and Cognitive Accessibility

### Standards
- Critical instructions are plain language.
- Jargon is minimized or explained.
- Important actions include consequence clarity.

### AI SaaS-specific checks
- AI limitations and verification guidance are written in plain, non-legalistic language.
- Hallucination risk disclaimers are helpful and actionable, not fear-based.

## 9) Error and Empty State Accessibility

### Standards
- Error messages explain cause and next action.
- Empty states provide clear first step.
- Timeout/rate-limit states include retry guidance.

### AI SaaS-specific checks
- Prompt failure states (quota/model unavailable) present alternatives.
- "No result" states suggest rewritten prompt patterns.

## 10) Compliance-Ready Audit Checklist

Pass criteria for release readiness:
- No known blocker-level contrast failures in primary flows.
- Keyboard-only user can complete first conversion flow.
- Screen-reader user can understand structure and execute core actions.
- Critical legal and trust information is reachable and readable.
- Mobile accessibility remains functional at high zoom.

Severity guidance:
- Blocker: prevents key flow completion.
- High: severe friction with major user impact.
- Medium: notable friction, workaround exists.
- Low: polish/quality issue with limited impact.
