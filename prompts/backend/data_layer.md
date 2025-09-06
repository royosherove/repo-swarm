version=2
Act as a backend data architect. Analyze the data layer, persistence mechanisms, and data access patterns in this backend service.

**Special Instruction**: Only document data layer components that are ACTUALLY present in the codebase. Do NOT list databases, ORMs, or data technologies that are not implemented.

## Database Architecture

1. **Primary Database:**
   - Type (SQL/NoSQL)
   - Purpose and domain
   - Connection configuration
   - Connection pooling settings

2. **Data Models/Entities:**
   - Core domain entities
   - Entity relationships (1:1, 1:N, M:N)
   - Database schema/collections
   - Indexes and constraints

3. **Data Access Layer:**
   - ORM/ODM usage (Django ORM, SQLAlchemy, ActiveRecord, Sequel)
   - Repository pattern implementation
   - Query builders (Django Q, SQLAlchemy Query, ActiveRecord Query Interface)
   - Raw SQL/queries usage

4. **Caching Layer:**
   - Cache providers (Redis, Memcached)
   - Caching strategies (aside, through)
   - Cache invalidation patterns
   - TTL configurations

## Data Operations

1. **CRUD Operations:**
   - Standard CRUD implementations
   - Bulk operations
   - Soft deletes
   - Audit trails

2. **Transactions:**
   - Transaction boundaries
   - Distributed transactions
   - Saga patterns
   - Compensation logic

3. **Data Validation:**
   - Schema validation
   - Business rule validation
   - Data sanitization
   - Type coercion

4. **Query Optimization:**
   - Query performance patterns
   - N+1 query prevention
   - Eager/lazy loading
   - Query result pagination

## Data Migration & Seeding

1. **Migration Strategy:**
   - Migration tools
   - Version control
   - Rollback procedures
   - Zero-downtime migrations

2. **Data Seeding:**
   - Seed data management
   - Test data generation
   - Environment-specific data

## Data Security

1. **Data Protection:**
   - Encryption at rest
   - Field-level encryption
   - PII handling
   - Data masking

2. **Access Control:**
   - Database user permissions
   - Row-level security
   - Multi-tenancy patterns
   - Data isolation

## Data Synchronization

1. **Event Sourcing:**
   - Event store implementation
   - Event replay mechanisms
   - Snapshots

2. **Change Data Capture:**
   - CDC implementation
   - Data streaming
   - Sync mechanisms

Format the output clearly using markdown

---

## Repository Structure and Files

{repo_structure}

---

## Dependencies

{repo_deps}
