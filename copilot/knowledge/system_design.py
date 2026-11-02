"""System design mental models: the interview framework and components."""

FRAMEWORK = [
    {"step": "Requirements", "minutes": 5,
     "do": "Functional: the 3-4 core actions. Non-functional: scale, "
           "latency, availability vs consistency, durability.",
     "say": "Before drawing anything, let me pin down what we must support "
            "and what we're optimising for."},
    {"step": "Estimates", "minutes": 3,
     "do": "Users, QPS (read vs write), storage per year, peak vs average. "
           "Round hard; you want orders of magnitude.",
     "say": "Rough numbers tell me whether this is one box or a fleet."},
    {"step": "API", "minutes": 4,
     "do": "Name each endpoint or event with inputs and outputs. "
           "Idempotency keys on anything that writes.",
     "say": "Here's the contract the client sees."},
    {"step": "Data model", "minutes": 5,
     "do": "Entities, keys, access patterns. Choose storage per access "
           "pattern, not per fashion.",
     "say": "The access pattern decides the store: here's how we read it."},
    {"step": "High-level design", "minutes": 10,
     "do": "Client to edge to services to data. Every box earns its place "
           "with a reason.",
     "say": "Walking a request end to end..."},
    {"step": "Deep dives", "minutes": 12,
     "do": "Pick the 2 hardest parts: hot keys, fan-out, consistency, "
           "ordering, exactly-once. Offer options and choose.",
     "say": "The interesting part is X. Two ways to do it, and here's the "
            "one I'd pick and why."},
    {"step": "Failure and trade-offs", "minutes": 6,
     "do": "What breaks first at 10x, what happens when each dependency is "
           "down, what you'd monitor and alert on.",
     "say": "Here's what fails first and how we'd notice."},
]

COMPONENTS = {
    "dns": {
        "name": "DNS", "model": "A phone book everyone photocopies and keeps "
        "for as long as the TTL says.",
        "use_when": ["Geo or latency routing", "Weighted rollouts",
                     "Coarse regional failover (minutes)"],
        "not_when": ["Fast failover: caches outlive the TTL",
                     "Per-request routing decisions"],
        "tradeoff": "Short TTL = fast change, more lookups. Long TTL = cheap "
                    "and resilient, but mistakes last hours.",
        "question": "Primary region is down. How fast can DNS move traffic?",
        "mistakes": ["Claiming DNS failover is instant",
                     "Round-robin DNS as the load-balancing story"]},
    "cdn": {
        "name": "CDN", "model": "Put a copy of popular content physically "
        "closer to the user.",
        "use_when": ["Static assets", "Read-heavy shared content",
                     "Global audiences", "Absorbing spikes and DDoS"],
        "not_when": ["Per-user personalised responses", "Writes",
                     "Strict freshness without reliable invalidation"],
        "tradeoff": "Long TTL = high hit ratio, stale risk. Short TTL = fresh, "
                    "more origin load.",
        "question": "Would you put a CDN in front of this service?",
        "mistakes": ["Caching per-user APIs",
                     "No cache key or invalidation story"]},
    "load_balancer": {
        "name": "Load Balancer", "model": "A receptionist who knows which "
        "desks are staffed.",
        "use_when": ["More than one instance of anything",
                     "Zero-downtime deploys", "TLS termination"],
        "not_when": ["Regional failover", "Queue-style work distribution"],
        "tradeoff": "L7 routes on path/header with retries but costs CPU; L4 "
                    "is fast but blind to requests.",
        "question": "A backend returns 500s on 30% of calls but passes health "
                    "checks. What happens?",
        "mistakes": ["Shallow health checks", "Unbounded retries everywhere"]},
    "api_gateway": {
        "name": "API Gateway", "model": "A bouncer with a rulebook: who you "
        "are, how often you've asked, which door.",
        "use_when": ["One public API over many services", "Per-client quotas",
                     "Auth and validation at the edge"],
        "not_when": ["Service-to-service calls", "Business logic"],
        "tradeoff": "Central policy and one surface vs a shared bottleneck "
                    "and blast radius.",
        "question": "Where do you enforce rate limits?",
        "mistakes": ["Treating it as free on the critical path",
                     "Fine-grained authz without business context"]},
    "cache": {
        "name": "Cache (Redis/Memcached)", "model": "Keep the answer you just "
        "computed where the next asker can grab it in under a millisecond.",
        "use_when": ["Read-heavy hot data", "Expensive computed results",
                     "Sessions, rate-limit counters, leaderboards"],
        "not_when": ["Source of truth for data you can't lose",
                     "Low hit ratio data"],
        "tradeoff": "Cache-aside is simple but can serve stale; write-through "
                    "is fresh but slows writes.",
        "question": "A hot key gets 100k reads/s. What do you do?",
        "mistakes": ["No TTL or invalidation plan",
                     "Thundering herd on expiry: use jitter or "
                     "request coalescing"]},
    "relational_db": {
        "name": "Relational DB (Postgres/MySQL)", "model": "A ledger with "
        "rules: constraints and transactions keep it honest.",
        "use_when": ["Relationships and joins", "Multi-row transactions",
                     "Money, inventory, anything needing ACID"],
        "not_when": ["Unbounded write scale on one node",
                     "Schemaless blobs"],
        "tradeoff": "Strong consistency and flexible queries vs harder "
                    "horizontal scaling.",
        "question": "Writes outgrow one primary. What are your options?",
        "mistakes": ["Sharding before trying read replicas and indexes",
                     "Missing indexes on access-pattern columns"]},
    "nosql": {
        "name": "Key-value / wide-column (DynamoDB/Cassandra)",
        "model": "A giant hash map partitioned across machines: fast when "
                 "you know the key.",
        "use_when": ["Known access patterns at huge scale",
                     "Single-digit ms reads by key",
                     "Event and time-series data"],
        "not_when": ["Ad-hoc queries and joins",
                     "Access patterns that keep changing"],
        "tradeoff": "Predictable scale vs designing tables around queries "
                    "up front.",
        "question": "How do you avoid a hot partition?",
        "mistakes": ["Low-cardinality partition keys",
                     "Scans in the request path"]},
    "queue": {
        "name": "Queue (SQS/RabbitMQ)", "model": "An inbox between producer "
        "and worker so neither waits on the other.",
        "use_when": ["Work longer than a request", "Smoothing spikes",
                     "Retries with backoff and dead-letter queues"],
        "not_when": ["The caller needs the answer now",
                     "Strict global ordering at scale"],
        "tradeoff": "Decoupling and resilience vs eventual results and "
                    "at-least-once duplicates.",
        "question": "A message is processed twice. Is that a bug?",
        "mistakes": ["Non-idempotent consumers",
                     "No dead-letter queue or poison-message plan"]},
    "event_stream": {
        "name": "Event stream / bus (Kafka/EventBridge)",
        "model": "A shared, replayable log many consumers read at their own "
                 "pace.",
        "use_when": ["Fan-out to many consumers", "Event-driven services",
                     "Replay and audit"],
        "not_when": ["Simple point-to-point jobs", "Request/response"],
        "tradeoff": "Loose coupling and replay vs ordering per partition only "
                    "and harder debugging.",
        "question": "How do you guarantee per-user ordering?",
        "mistakes": ["Assuming global ordering",
                     "No schema versioning for events"]},
    "object_storage": {
        "name": "Object storage (S3/GCS)", "model": "An infinite, cheap, "
        "durable filing cabinet addressed by key.",
        "use_when": ["Files, media, backups", "Data lake",
                     "Large payloads referenced from a DB"],
        "not_when": ["Low-latency small random writes",
                     "Anything needing transactions"],
        "tradeoff": "Cheap and durable vs higher latency per request.",
        "question": "How do users upload a 2 GB video?",
        "mistakes": ["Proxying uploads through app servers instead of "
                     "presigned URLs"]},
    "search_index": {
        "name": "Search index (Elasticsearch/OpenSearch)",
        "model": "A book's index: maps words to where they appear.",
        "use_when": ["Full-text and fuzzy search", "Faceted filtering"],
        "not_when": ["Source of truth", "Strongly consistent reads"],
        "tradeoff": "Rich queries vs a second copy that lags the primary.",
        "question": "How do you keep the index in sync with the DB?",
        "mistakes": ["Dual writes from the app (use CDC or an outbox)"]},
    "rate_limiting": {
        "name": "Rate limiting", "model": "A bucket of tokens that refills at "
        "a fixed rate; each request spends one.",
        "use_when": ["Protecting shared resources", "Fairness between "
                     "tenants", "Paid quotas"],
        "not_when": ["As the only overload protection"],
        "tradeoff": "Token bucket allows bursts; sliding window is precise "
                    "but costlier.",
        "question": "Limiter's Redis is down. Fail open or closed?",
        "mistakes": ["Per-node counters for a global limit"]},
    "sharding": {
        "name": "Sharding and replication", "model": "Split data by key "
        "across machines; copy each piece for safety and reads.",
        "use_when": ["Data or writes exceed one node",
                     "Read scaling and failover"],
        "not_when": ["Before indexes, caching and replicas run out"],
        "tradeoff": "Hash sharding spreads load but kills range scans; range "
                    "sharding keeps ranges but risks hot spots.",
        "question": "How do you reshard with no downtime?",
        "mistakes": ["Cross-shard transactions everywhere",
                     "Ignoring replica lag on read-after-write"]},
    "idempotency": {
        "name": "Idempotency and exactly-once effects",
        "model": "Make doing it twice the same as doing it once.",
        "use_when": ["Any retried write", "At-least-once delivery",
                     "Payments and side effects"],
        "not_when": ["Never skip it for writes behind retries"],
        "tradeoff": "Idempotency keys cost a lookup per write but remove a "
                    "whole class of duplicates.",
        "question": "The client times out and retries a payment. What "
                    "happens?",
        "mistakes": ["Believing the network delivers exactly once"]},
}

ALIASES = {
    "redis": "cache", "memcached": "cache", "postgres": "relational_db",
    "mysql": "relational_db", "sql": "relational_db",
    "dynamodb": "nosql", "cassandra": "nosql", "sqs": "queue",
    "kafka": "event_stream", "eventbridge": "event_stream",
    "s3": "object_storage", "elasticsearch": "search_index",
    "lb": "load_balancer", "gateway": "api_gateway",
    "shard": "sharding", "replication": "sharding",
}
