# AI Inbox and Scheduling Operator MVP Build Spec (Updated)
  
## 1. Product Definition

The MVP is a focused AI inbox and scheduling operator. It reads incoming email, classifies urgency, drafts replies, suggests scheduling options based on user preferences, creates internal tasks, and only notifies the user when something truly needs attention.

The product is not a general-purpose AI employee in version 1. The first release is intentionally narrow: email triage, scheduling support, task extraction, and criticality-based alerts.

The long-term product vision remains a personal AI operator that learns how a user works over time and adapts to their communication style, scheduling habits, follow-up behavior, and execution preferences. The MVP does not deliver the full vision yet, but it should visibly begin that learning process through lightweight personalization and feedback loops.

## 2. Core Use Case

Main use case: read through the entire inbox email and help with scheduling using a user profile and preference layer.

- Monitor inbox continuously in the background.
- Classify messages into urgency and action categories.
- Detect scheduling-related emails and propose meeting slots.
- Draft replies for common inbound requests.
- Convert emails into internal tasks when follow-up is needed.
- Escalate only high-criticality items with immediate notifications.

The assistant should not only execute actions, but gradually improve suggestions based on how the user responds, edits, approves, delays, and prioritizes work.

## 3. MVP Scope

The MVP should include only the smallest set of features that creates real daily value for solo operators and founders

- Gmail or Outlook integration, with Gmail first for simplicity.
- Google Calendar integration.
- Inbox triage: urgent, important, low priority, FYI, scheduling, newsletter/spam.
- User profile and preferences: work hours, meeting length, buffer time, timezone, VIP senders, communication tone, escalation rules.
- Reply draft generation for common emails.
- Scheduling suggestions based on free/busy availability and preferences.
- Internal task extraction from emails.
- Priority alerts for emails that need action right away.
- Approval workflow before sending external replies or booking meetings.
- Daily summary of handled emails, pending items, and next actions.

Lightweight personalization is part of the MVP scope. The system should start with explicit user setup, then adapt based on repeated behavior, such as accepted meeting windows, draft edits, approval decisions, and recurring override patterns.

## 4. User Interface

The interface should be highly efficient and operational, not chat-heavy. The layout should feel like an execution dashboard.

- Mail view: grouped by urgency and action type, not only by time.
- Calendar view: meeting requests, proposed slots, conflicts, and schedule suggestions.
- Tasks panel: internal tasks extracted from communications.
- Priority alerts panel: items that need user action immediately.
- Profile/settings: tone, work hours, scheduling rules, sender rules, escalation thresholds.
- Activity log: what the assistant read, classified, drafted, and escalated.

The UI should also expose why the assistant made certain suggestions and what it has learned so far, for example preferred meeting times, common reply tone patterns, frequent VIP contacts, and alerting tendencies. This helps build trust and makes personalization visible rather than hidden.

## 5. Automation Design

Automation should run mostly in the background. n8n is a practical option for the MVP because it speeds up workflow automation and reduces engineering effort.

- Workflow 1: Email and calendar ingestion.
- Workflow 2: Classification and criticality scoring.
- Workflow 3: Drafting, scheduling suggestions, and task creation.
- Workflow 4: Alerting and daily briefing.
- Workflow 5: Human approval before sensitive actions.

A lightweight feedback workflow should be included. User actions such as approve, edit, reject, snooze, reschedule, and manual rewrite should be logged and used as structured signals for future personalization.

## 6. Criticality Assessment

Criticality assessment is a core differentiator. The assistant should decide what can be handled silently, what can be proposed for approval, and what requires immediate attention.

- Urgency signals: deadlines, explicit urgency language, sender priority, meeting timing, unresolved threads.
- Business importance: VIP contacts, strategic meetings, customer-facing messages.
- Action confidence: whether the assistant can respond safely without ambiguity.
- Escalation rule: send a notification only when there is a strong need for user intervention.

Over time, criticality scoring should become more personalized. If a user consistently treats certain senders, situations, or subjects as high priority, the system should reflect that pattern in future scoring.

## 7. Tech Stack

- Frontend: Next.js, TypeScript, Tailwind CSS.
- Backend/API: Next.js API routes or FastAPI.
- Database: Postgres with Prisma.
- Memory/retrieval: pgvector or a simple relational memory layer first.
- Automation: n8n, ideally self-hosted for cost control.
- AI layer: OpenAI or Anthropic API for classification, summarization, drafting, and scheduling logic.
- Auth: NextAuth or Clerk.
- Notifications: email, Slack, or Telegram.
- Hosting: Vercel for frontend and a simple cloud host for backend, database, and n8n.

The memory layer in the MVP does not need to be a full autonomous memory system. It can begin as a lightweight preference and behavior store that records user settings, accepted or rejected suggestions, common edits, sender importance signals, and scheduling patterns.

## 8. Data Model Needed

- Users
- Profiles and preferences
- Connected accounts
- Email threads and message metadata
- Calendar events and meeting requests
- Tasks
- Rules and escalation settings
- Draft actions and approval status
- Audit logs

Add explicit support for personalization data:

- Learned tone preferences
- Accepted vs. rejected scheduling suggestions
- Approval/edit/reject history
- Sender importance signals
- Repeated follow-up behavior
- User override patterns
- Personalization confidence scores

## 9. What Is Needed to Build the MVP

- A narrow product scope: email and calendar only in v1.
- OAuth setup for Gmail and Google Calendar.
- A user profile schema with preferences and communication rules.
- A triage engine for classification and urgency scoring.
- A workflow engine for triggers, actions, retries, and notifications.
- A human-in-the-loop approval layer.
- An audit and logging system for trust and traceability.
- A lightweight UI for inbox, tasks, approvals, and schedule suggestions.
- Basic analytics to measure time saved, triage accuracy, and action rates.

To preserve the original product vision, the MVP must also include a basic learning loop. This means storing behavioral feedback, updating recommendations from repeated user actions, and reflecting those learned patterns in drafts, scheduling, and prioritization.

## 10. MVP User Flow

- User signs up and connects Gmail and Google Calendar.
- User sets work preferences, tone, scheduling rules, and VIP contacts.
- The system monitors incoming email and calendar context.
- The assistant classifies emails, scores urgency, and detects scheduling intent.
- The assistant drafts replies, suggests slots, creates tasks, or deprioritizes messages.
- The user reviews only priority items and approvals.
- The assistant sends a daily operational summary.

After each user interaction, the system stores useful feedback signals. Over time, future drafts, meeting suggestions, and escalation decisions should become more aligned with the user's actual working style.

## 11. Build Phases

- Phase 1: Gmail ingest, classification, and priority inbox.
- Phase 2: Calendar integration and scheduling suggestions.
- Phase 3: Task extraction and notification logic.
- Phase 4: Approval workflow for sending and booking.
- Phase 5: Personalization and memory improvements based on user edits and behavior.

Personalization should not be postponed entirely until the end. Even in early phases, the product should capture behavioral data so Phase 5 improves an already functioning feedback system rather than introducing learning from scratch.

## 12. MVP Success Metrics

- Time saved per user per week.
- Inbox triage accuracy.
- Scheduling suggestion acceptance rate.
- Percentage of emails handled in background.
- Approval-to-send conversion rate.
- Reduction in manual inbox processing time.
- User trust and retention.

Include learning-specific success metrics:

- Reduction in draft editing over time.
- Increase in accepted scheduling suggestions over time.
- Reduction in unnecessary alerts.
- Improvement in personalization confidence for recurring patterns.
- Percentage of recommendations aligned with previous user behavior.

## 13. Recommended MVP Statement

An AI inbox and scheduling operator for solo operators and founders that reads incoming email, prioritizes what matters, drafts replies, suggests meeting slots from user preferences, turns messages into internal tasks, and only notifies the user when something truly needs attention.

Expanded vision statement: an AI operator that begins with inbox and scheduling, then gradually learns how the user communicates, prioritizes, schedules, and follows up so it can act more like a trusted operational assistant in the user's own tone and style.

## 14. Learning and Personalization

This section is an added layer required to show that the MVP begins learning how the user works.

The MVP includes lightweight learning based on both explicit setup and observed behavior. It should not claim full autonomous learning in version 1, but it should clearly improve based on repeated user interaction.

### What the MVP learns

- Preferred reply tone, based on edits to AI-generated drafts.
- Preferred meeting windows and buffer rules, based on accepted or rejected slot suggestions.
- Preferred escalation behavior, based on what the user opens immediately, snoozes, ignores, or marks urgent.
- Sender sensitivity, based on which contacts consistently trigger review or approval.
- Follow-up style, based on how tasks are deferred, completed, or rewritten.

### How the MVP learns

- Start with explicit onboarding preferences.
- Log approvals, edits, rejections, overrides, and scheduling outcomes.
- Extract repeatable signals from that behavior.
- Reuse those signals in future drafts, prioritization, and scheduling suggestions.
- Show the user what has been learned so they can trust, confirm, or correct it.

### Boundaries in v1

- No claim of full autonomy.
- No hidden adaptation without user visibility.
- No broad cross-channel behavioral intelligence yet.
- Learning remains focused on inbox, calendar, follow-ups, and task handling.
