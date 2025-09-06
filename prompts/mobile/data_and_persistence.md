version=1
You are a mobile data architecture expert. Analyze all data persistence, caching strategies, and state management patterns in this mobile application.

**Special Instruction**: Only document data persistence mechanisms and storage solutions that are ACTUALLY implemented in the codebase. Do NOT list databases, caching systems, or storage frameworks that are not present.

## Local Database

1. **Database Technology:**
   - Database type (SQLite, Realm, Core Data, Room, ObjectBox)
   - Database version and configuration
   - Database encryption setup
   - Migration strategies

2. **Data Models:**
   - Entity definitions
   - Relationships (1:1, 1:N, N:N)
   - Primary keys and indexes
   - Data types and constraints

3. **Database Operations:**
   - CRUD operations implementation
   - Query patterns and optimization
   - Transaction management
   - Batch operations
   - Database observers/listeners

4. **ORM/Data Access Layer:**
   - ORM framework (Core Data, Room, SQLDelight)
   - DAO patterns
   - Repository pattern implementation
   - Query builders

## Key-Value Storage

1. **Preferences/Settings:**
   - UserDefaults/SharedPreferences usage
   - Encrypted preferences
   - Settings synchronization
   - Default values management

2. **Secure Storage:**
   - Keychain (iOS) / Keystore (Android) usage
   - Biometric-protected storage
   - Token storage
   - Sensitive data encryption

3. **Cache Storage:**
   - Memory cache implementation
   - Disk cache strategies
   - Cache size limits
   - Cache invalidation policies

## File System

1. **File Management:**
   - Document directory usage
   - Cache directory management
   - Temporary files handling
   - File naming conventions

2. **Binary Data:**
   - Image storage and caching
   - Video/audio file management
   - Download management
   - File compression

3. **Data Export/Import:**
   - Backup strategies
   - Data export formats (JSON, CSV)
   - Data import validation
   - File sharing capabilities

## State Management

1. **Application State:**
   - Global state architecture
   - State persistence between sessions
   - State restoration after app kill
   - Deep link state handling

2. **UI State:**
   - Form state persistence
   - Navigation state saving
   - Scroll position restoration
   - Tab/screen state management

3. **Reactive State:**
   - Observable patterns (RxSwift, LiveData, Combine)
   - State streams
   - State synchronization
   - Conflict resolution

## Data Synchronization

1. **Sync Strategy:**
   - Sync triggers (manual, automatic, scheduled)
   - Bi-directional sync
   - Conflict resolution policies
   - Delta sync implementation

2. **Offline-First Architecture:**
   - Local-first data strategy
   - Queue for pending changes
   - Optimistic updates
   - Sync status tracking

3. **Background Sync:**
   - Background fetch implementation
   - Silent push triggers
   - Scheduled sync jobs
   - Network-triggered sync

## Caching Strategies

1. **Network Response Caching:**
   - HTTP cache headers respect
   - Response caching policies
   - Cache-first vs network-first
   - Stale-while-revalidate

2. **Image Caching:**
   - Memory cache configuration
   - Disk cache limits
   - Progressive image loading
   - Thumbnail generation

3. **Data Caching:**
   - API response caching
   - Computed data caching
   - User session caching
   - Temporary data storage

## Data Security

1. **Encryption:**
   - At-rest encryption
   - Field-level encryption
   - Database encryption (SQLCipher)
   - File encryption

2. **Data Privacy:**
   - PII handling
   - Data anonymization
   - GDPR compliance (right to delete)
   - Data retention policies

3. **Access Control:**
   - User-based data isolation
   - Role-based access
   - Data sharing permissions
   - Multi-user support

## Memory Management

1. **Data Loading:**
   - Lazy loading patterns
   - Pagination implementation
   - Cursor-based loading
   - Infinite scroll data management

2. **Memory Optimization:**
   - Large dataset handling
   - Memory warnings response
   - Data pruning strategies
   - Weak reference usage

3. **Lifecycle Management:**
   - Data cleanup on logout
   - Memory release patterns
   - Observer lifecycle binding
   - Subscription management

## Cloud Storage Integration

1. **Cloud Providers:**
   - iCloud integration (iOS)
   - Google Drive integration
   - Firebase Storage
   - AWS S3 integration

2. **Sync with Cloud:**
   - Document sync
   - Photo backup
   - Settings sync
   - Cross-device sync

## Data Migration

1. **Schema Migrations:**
   - Version management
   - Migration scripts
   - Backward compatibility
   - Data transformation

2. **App Updates:**
   - Data format changes
   - Legacy data handling
   - Migration testing
   - Rollback strategies

## Performance Optimization

1. **Query Optimization:**
   - Index usage
   - Query planning
   - Batch fetching
   - Lazy relationships

2. **Write Optimization:**
   - Batch inserts
   - Write-ahead logging
   - Async writes
   - Write coalescing

3. **Read Optimization:**
   - Prepared statements
   - Result caching
   - Projection optimization
   - Join optimization

Format the output clearly using markdown

---

## Repository Structure and Files

{repo_structure}
