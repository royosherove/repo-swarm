version=1
You are a backend messaging and event-driven architecture expert. Analyze all asynchronous communication patterns in this service.

**Special Instruction**: If no event/messaging patterns found, return "no event-driven patterns". Only document messaging systems that are ACTUALLY implemented in the codebase. Do NOT list message brokers, queues, or event systems that are not present.

## Message Brokers & Queues

1. **Message Queue Systems:**
   - Queue providers (RabbitMQ, SQS, Azure Service Bus)
   - Queue configurations
   - Dead letter queues
   - Message TTL and retention

2. **Event Streaming:**
   - Streaming platforms (Kafka, Kinesis, EventHub)
   - Topics and partitions
   - Consumer groups
   - Offset management

3. **Pub/Sub Patterns:**
   - Event bus implementation
   - Topic subscriptions
   - Fan-out patterns
   - Event routing

## Event Patterns

1. **Event Types:**
   - Domain events
   - Integration events
   - Command events
   - System events

2. **Event Structure:**
   For each event type:
   - Event name/identifier
   - Payload schema
   - Event metadata (timestamp, correlation ID, source)
   - Event versioning

3. **Event Producers:**
   - Triggering conditions
   - Event publishing logic
   - Transactional outbox pattern
   - Event ordering guarantees

4. **Event Consumers:**
   - Consumer handlers
   - Processing logic
   - Idempotency mechanisms
   - Error handling and retries

## Messaging Patterns

1. **Communication Patterns:**
   - Request-Reply
   - Fire-and-Forget
   - Publish-Subscribe
   - Competing Consumers

2. **Message Processing:**
   - Batch processing
   - Message aggregation
   - Message transformation
   - Content-based routing

3. **Reliability Patterns:**
   - At-least-once delivery
   - Exactly-once processing
   - Message deduplication
   - Acknowledgment strategies

## Background Jobs

1. **Job Scheduling:**
   - Schedulers (cron, scheduled tasks, whenever gem)
   - Job queues (Celery for Python, Sidekiq/Resque/DelayedJob for Rails)
   - Delayed jobs (celery.apply_async, perform_later)
   - Recurring jobs (celery beat, whenever, sidekiq-cron)

2. **Job Processing:**
   - Worker pools
   - Job priorities
   - Job dependencies
   - Progress tracking

## Event Store & Sourcing

1. **Event Storage:**
   - Event store implementation
   - Event serialization
   - Event replay capabilities
   - Snapshot strategies

2. **CQRS Implementation:**
   - Command handlers
   - Query handlers
   - Read model projections
   - Eventual consistency handling

Format the output clearly using markdown

---

## Repository Structure and Files

{repo_structure}
