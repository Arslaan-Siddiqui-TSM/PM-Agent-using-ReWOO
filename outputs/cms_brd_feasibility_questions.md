## Feasibility Questions for the Tech Lead

1.  **Integration with Data Fiduciaries:** How will Data Fiduciaries and Processors integrate their existing systems with our Consent Management System to collect consent, validate it in real-time, and receive notifications about changes? What technical effort is anticipated for these integrations on both sides?

        Answer — recommended integration patterns and effort estimate:

        - API-first: Provide a small, versioned REST/JSON API (and gRPC optionally) that supports the core operations: SubmitConsent, GetConsentStatus, RevokeConsent, and SubscribeToConsentEvents. Use OAuth2 client credentials for service-to-service auth and JWTs for end-user flows.
        - SDK & Adapter: Supply lightweight SDKs (TypeScript, Python, Java) and an adapter reference implementation for common platforms so DF/Processors can integrate quickly. Offer a webhook-based event delivery path as an alternative to polling.
        - Real-time validation: Implement a synchronous validation endpoint (GetConsentStatus or ValidateConsentToken) for low-latency checks, plus an asynchronous event stream (webhooks / Kafka / Pub/Sub) for background propagation.
        - Effort estimate:
        	- For a modern web backend with REST support: 2–5 developer days to call APIs and register webhooks; 1–2 days to wire SDK. For legacy systems without JSON parsing, expect 2–4 weeks when building an adapter layer.
        	- On our side: provide API docs, client libraries, onboarding guide and a sandbox environment — ~2–3 sprints to finish polished SDKs and sandbox if not already available.

        - Acceptance criteria: authenticated calls, end-to-end test in sandbox, idempotent webhook delivery with retry logic and dead-letter queue.

2.  **Data Storage and Immutability:** Given the strict requirements for auditability, versioning, and compliance with data retention policies, what database technology and architectural patterns are proposed to store consent records securely and immutably?

        Answer — storage architecture and choices:

        - Canonical approach: Use an append-only event store / audit log plus a materialized view for fast reads. Store raw events (consent created, updated, revoked) immutably with cryptographic hashes; build the current state via projections.
        - Candidate technologies:
        	- Postgres (with WAL + logical replication) or a dedicated event store (e.g., EventStoreDB, Kafka + compacted topics) for the immutable log; use PostgreSQL or a strongly-consistent document store (e.g., CockroachDB, Cloud Spanner) for the materialized state.
        	- For long-term tamper-evidence, store signed hashes of daily snapshots in an external notarization (e.g., object storage with write-once configuration, or an optional blockchain anchoring service) to aid audits.
        - Data model & patterns:
        	- Each consent event: {id, subject_id, fiduciary_id, policy_id, action, timestamp, previous_hash, signature, metadata}
        	- Ensure events are write-once; prohibit in-place updates. Use soft-deletes for views only; actual deletion follows retention workflows.
        - Encryption & key management: AES-256 at rest for DB/storage and envelope encryption with KMS (AWS KMS / GCP KMS / Azure Key Vault). Use HSM for signing if required by regulation.
        - Versioning & auditability: Add event version field and maintain immutable audit index. Provide APIs to query history and export for compliance.

        - Acceptance criteria: immutable event log, reproducible materialized state, tamper-evidence artifacts, and documented retention workflow.

3.  **Scalability and Performance:** What is the anticipated peak load for consent requests and validations, and what architectural design and infrastructure choices will ensure the system can scale to meet these performance demands reliably?

        Answer — design for scale:

        - Baseline architecture: stateless API tier behind autoscaling load balancers, distributed cache (Redis/Elasticache) for hot lookups, an event/message bus (Kafka/RabbitMQ/Cloud pubsub) for async propagation, and horizontally-scalable data stores.
        - Read/write patterns & caching:
        	- Expect reads >> writes for validation. Use a TTL-based cache for GetConsentStatus (cache key: subject+fiduciary+purpose) with atomic invalidation on events.
        	- Offer a short-lived signed consent token (JWT) issued on consent creation to avoid synchronous DB hits for every authorization check.
        - Throughput targets & capacity planning (examples):
        	- If 10k validations/sec peak: horizontally scale API nodes behind LB, use 3–5 Redis shards, and partition event topics. For >100k/sec consider edge caching/CDN + local caches in services.
        - Resilience & throttling: implement circuit-breakers, back-pressure on event ingestion, rate limits per fiduciary and global per-tenant quotas; provide graceful degradation (serve last-known consent when validation service is transiently unavailable) with clear audit traces.
        - Observability: metrics (latency, error rate), distributed tracing for validation paths, and SLOs for validation latency (e.g., P95 < 100ms for cached, < 250ms for cold).

        - Acceptance criteria: documented capacity plan, autoscaling rules, cache hit targets, and load-test evidence for anticipated peaks.

4.  **Security and Compliance:** Considering the sensitive nature of personal data and DPDP Act compliance, what specific security architecture and controls will be implemented to protect consent data, prevent unauthorized access, and ensure the integrity of audit logs?

        Answer — security controls and compliance guardrails:

        - Data protection:
        	- Encryption in transit (TLS 1.2+/1.3) and at rest (AES-256). Envelope encryption with KMS and key rotation policies.
        	- Fine-grained access control using RBAC/ABAC — least privilege for services and operators. Use short-lived credentials and OIDC for human access.
        - Authentication & authorization:
        	- OAuth2 + JWT for service & delegated user flows. Mutual TLS for high-trust integrations.
        	- Per-tenant or per-fiduciary API keys scoped to specific operations and quotas.
        - Auditability & tamper-evidence:
        	- Immutable event log with signed events and chaining (previous_hash). Store append-only logs in write-once object storage or maintain append-only DB tables with restricted operations.
        	- Forward events to SIEM (Splunk/ELK/Datadog) and enable immutable retention for audit artifacts.
        - Operational controls:
        	- Secrets management (Vault/KMS), hardened deployment pipelines, vulnerability scanning (SCA), dependency pinning and regular patching.
        	- Incident response runbook, periodic penetration testing, and breach notification procedures aligned to DPDP timelines.
        - Data minimization & PII handling:
        	- Store only the minimum required identifiers (use pseudonymization where possible), support hashing/salting of identifiers for lookup, and tokenize full identifiers when necessary.

        - Acceptance criteria: threat model, SOC2/ISO27001 mapping, encryption & key rotation proof, and pass of a security readiness checklist.

5.  **User Interface and Accessibility:** To meet the requirements for WCAG compliance and a user-friendly interface for both the main dashboard and cookie consent, what are the proposed front-end technologies and design principles, and how will we ensure a consistent user experience across different platforms?

        Answer — frontend stack and UX approach:

        - Tech stack: React + TypeScript for the main app, with a component library (Radix UI or Material UI) that supports accessibility, or a design system (Storybook) for consistency. For server-side rendering/SEO-critical pieces consider Next.js.
        - Accessibility & design principles:
        	- WCAG 2.1 AA baseline: keyboard navigation, focus management, color contrast, ARIA attributes, and screen-reader testing.
        	- Cookie/banner consent: minimal, non-blocking modal with clear choices and granular controls; store user preference in signed cookie + server record.
        	- Responsive design and progressive enhancement (functionality without JS where feasible for the cookie banner).
        - Internationalization & localization: use i18n frameworks and allow externalized strings for translators.
        - QA & validation:
        	- Include automated axe-core accessibility checks in CI, manual keyboard and screen-reader rounds, and UX testing sessions.

        - Acceptance criteria: WCAG AA checklist pass, component library with accessibility baked in, and a tested cookie consent flow across major browsers and mobile.

6.  **Notification System Reliability:** What third-party services or internal mechanisms are planned for sending user notifications and Data Fiduciary/Processor alerts (e.g., email, SMS, push), and how will we ensure the reliability, deliverability, and auditability of these critical communications?

        Answer — notifications strategy:

        - Multi-channel providers: use managed providers for scale and deliverability (SendGrid/Postmark/Mailgun for email; Twilio/MessageBird/Infobip for SMS; Firebase/APNs for push). Abstract providers behind a Notification Service that supports provider failover and retries.
        - Reliability patterns:
        	- Durable queueing (e.g., Kafka/SQS) for outgoing messages, retry policies with exponential backoff, and dead-letter queues for failed deliveries.
        	- Multi-provider strategy for critical channels (primary + secondary) to mitigate provider outages.
        - Auditability and compliance:
        	- Record each notification event in the immutable event store with status updates (queued, sent, delivered, bounced). Preserve message payload hashes for audit without storing full PII unless required.
        	- Maintain unsubscribe lists and suppression logic centrally and ensure legally-required opt-out functions are enforced.

        - Acceptance criteria: delivery SLAs, observable delivery pipeline (metrics/tracing), and successful failover tests between providers.

7.  **Data Retention and Purging Enforcement:** How will the system technically enforce configured data retention policies, including the secure and auditable purging or anonymization of consent data when it expires or is withdrawn, to ensure compliance with DPDP Act requirements?

        Answer — retention lifecycle and enforcement:

        - Policy engine: Store retention policies as first-class configuration (per fiduciary, per purpose). A scheduled retention worker evaluates expirable records and enforces actions: anonymize, archive, or delete.
        - Implementation details:
        	- Soft-delete + expiry metadata on consent events and materialized views.
        	- On expiry: run anonymization transformations (irreversible hashing, redaction, or tokenization) and record a purge event in the event log. For full deletion where legally required, delete only after recording an auditable deletion event and updating indexes.
        	- For backups/archives: retention must be applied to archived copies too. Use lifecycle policies in object storage and rotate/archive snapshots with documented retention.
        - Verification & audit:
        	- Provide a tamper-evident purge report and automated reconciliation job that verifies no expired PII remains in live views, and a periodic compliance report for auditors.

        - Acceptance criteria: automated policy enforcement, recorded purge events, and reconciliation reports for auditors.

8.  **Grievance Redressal Workflow:** What technical approach or workflow management solution is proposed for the Grievance Redressal Mechanism to ensure efficient logging, tracking, and resolution of complaints, while maintaining a complete and auditable history of each case?

        Answer — grievance workflow design:

        - Workflow engine: Integrate a lightweight workflow/task management system (e.g., temporal.io, Camunda, or a managed ticketing integration like Zendesk/JIRA with an audit bridge) to capture lifecycle states and SLAs.
        - Data and audit trail:
        	- Each complaint is an entity with immutable events (created, assigned, responded, escalated, resolved). Link complaints to consent records where applicable.
        	- Maintain attachments, correspondence snapshots, and redaction metadata; store audit trail in the event store and mirror necessary views for operator UI.
        - Automation & SLAs:
        	- Automated assignment rules, escalation timers, and templated responses. Support manual overrides with recorded justification.
        - Acceptance criteria: auditable case histories, SLA metrics, and ability to export full case history for regulators.

9.  **Deployment and Infrastructure Strategy:** What is the proposed deployment environment (e.g., cloud provider, on-premise) and architectural strategy to ensure the system is highly available, resilient to failures, and easily maintainable for ongoing operations?

        Answer — deployment and infra recommendations:

        - Cloud-first recommended (AWS/GCP/Azure) for managed services, but design to be cloud-portable (IaC + Terraform). On-premise is supported via Kubernetes and managed message/event layers for organizations with data residency needs.
        - High availability patterns:
        	- Multi-AZ, multi-region backups for critical systems, active/passive cross-region failover for stateful services, and leader-election for single-writer components.
        	- Use Kubernetes for orchestrating stateless services with HorizontalPodAutoscaler and stateful sets where needed; use managed DB services for automated backups and replicas.
        - Observability & operations:
        	- Centralized logging, metrics, tracing, and automated health checks. CI/CD with gated deployments, automated canary rollouts, and rollbacks.
        - Cost/ops tradeoffs: prefer managed PaaS for lower ops overhead; if strict data residency or audit controls are required, combine dedicated VPCs and customer-managed encryption keys.

        - Acceptance criteria: IaC templates, runbooks, DR plan, and automated smoke-tests post-deploy.

10. **Third-Party Dependencies and Risks:** Are there any critical third-party services, libraries, or open-source components identified as essential for the system's core functionality, and what are the associated risks regarding licensing, support, security vulnerabilities, and long-term maintenance?

        Answer — dependency inventory & risk mitigation:

        - Typical critical dependencies:
        	- Cloud provider managed services (DB, KMS, messaging), identity providers (Auth0/Keycloak), email/SMS providers, event store or Kafka, and frontend component libraries.
        	- Open-source libraries for crypto, serialization, and SDKs.
        - Risks:
        	- Licensing: ensure all OSS dependencies are compatible with the project's license and commercial usage. Watch for copyleft licenses if redistributing binaries.
        	- Security vulnerabilities: use SCA tooling (Dependabot/Snyk) and regular dependency audits; pin versions and apply emergency patches for critical CVEs.
        	- Vendor lock-in: mitigate by abstracting provider APIs via an internal adapter layer and preferring portable primitives (Kubernetes, Postgres) where feasible.
        	- Operational support: ensure SLAs with managed providers for critical services; keep runbooks to swap providers where feasible.
        - Mitigations:
        	- Maintain a dependency inventory, perform periodic risk reviews, and implement multi-provider strategies for high-impact services.

        - Acceptance criteria: dependency list, license review, vulnerability baseline, and fallback plan for critical provider outages.

---

Assumptions:

- The product must support per-fiduciary multi-tenancy and per-purpose retention policies.
- Integrations will primarily be with web-enabled backends; mobile SDK needs are higher effort but similar in pattern.

Next steps for Tech Lead:

1. Confirm expected peak load and SLAs for validations and notifications so capacity planning can be finalized.
2. Approve storage approach (Postgres event log + materialized views vs EventStore/Kafka) and KMS strategy.
3. Prioritize provider choices for email/SMS and identify any existing org constraints (e.g., mandated IDPs or key management systems).
4. Kick off a 2–3 week security & threat-modeling spike, plus a 1-week integration sandbox for early adopter Data Fiduciaries.

Contact: include links to API spec, onboarding sandbox, and SDK repos in the onboarding packet once approved.
