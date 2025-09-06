version=1
You are a mobile networking and API integration expert. Analyze all API usage, network communication, and backend integration patterns in this mobile application.

**Special Instruction**: If no API/network calls are found, return "no network communication detected". Only document networking libraries and API integrations that are ACTUALLY implemented in the codebase. Do NOT list networking tools or frameworks that are not present.

## API Integration

1. **Base Configuration:**
   - Base URLs and environments (dev, staging, prod)
   - API versioning strategy
   - Timeout configurations
   - Retry policies and exponential backoff

2. **HTTP Client Setup:**
   - Network libraries used (Alamofire, Retrofit, Dio, URLSession, OkHttp, axios)
   - Request/response interceptors
   - Custom headers management
   - User agent configuration

3. **API Endpoints:**
   For each endpoint category:
   - **Endpoint:** Method and path
   - **Purpose:** Business function
   - **Request:** Headers, parameters, body structure
   - **Response:** Expected format, status codes
   - **Error handling:** Retry logic, fallback behavior

## Authentication & Authorization

1. **Auth Flow:**
   - Authentication type (OAuth, JWT, API key, Basic Auth)
   - Token management (storage, refresh, expiry)
   - Session handling
   - Biometric authentication integration
   - Social login providers (Google, Facebook, Apple Sign-In)

2. **Secure Storage:**
   - Keychain/Keystore usage
   - Encrypted preferences
   - Certificate management
   - SSL pinning implementation

3. **Authorization Headers:**
   - Bearer token injection
   - API key management
   - Request signing
   - HMAC implementation

## Network Communication Patterns

1. **Request Management:**
   - Queue management
   - Request prioritization
   - Batch requests
   - Request cancellation

2. **Data Synchronization:**
   - Sync strategies (pull, push, bidirectional)
   - Conflict resolution
   - Delta sync implementation
   - Background sync

3. **WebSocket/Real-time:**
   - WebSocket connections
   - Server-Sent Events
   - Push notifications setup
   - Long polling fallbacks

4. **GraphQL (if present):**
   - Query definitions
   - Mutations
   - Subscriptions
   - Cache management

## Offline Capabilities

1. **Caching Strategy:**
   - Cache-first vs network-first
   - Cache invalidation rules
   - TTL configurations
   - Storage limits

2. **Offline Mode:**
   - Offline detection
   - Queue for offline requests
   - Data persistence strategy
   - Sync on reconnection

3. **Local Database:**
   - Database for offline data (SQLite, Realm, Core Data, Room)
   - Data models
   - Migration strategies

## Data Handling

1. **Serialization:**
   - JSON parsing (Codable, Gson, Moshi, json_serializable)
   - Model mapping
   - Type safety
   - Null safety handling

2. **Data Validation:**
   - Input validation
   - Response validation
   - Schema validation
   - Error model handling

3. **File Transfer:**
   - Image upload/download
   - Multipart requests
   - Progress tracking
   - Background transfers

## Performance & Optimization

1. **Network Optimization:**
   - Request batching
   - Response compression (gzip)
   - Image optimization (WebP, progressive loading)
   - Pagination implementation

2. **Monitoring:**
   - Network request logging
   - Performance metrics
   - Error tracking
   - Analytics integration

3. **Resource Management:**
   - Connection pooling
   - DNS caching
   - Keep-alive settings
   - Bandwidth management

## Security Considerations

1. **Data Protection:**
   - Encryption in transit
   - Request/response encryption
   - Sensitive data masking in logs
   - PII handling

2. **API Security:**
   - Rate limiting handling
   - API abuse prevention
   - Request throttling
   - DDoS protection

3. **Compliance:**
   - GDPR data handling
   - CCPA compliance
   - Data residency
   - Audit logging

Format the output clearly using markdown

---

## Repository Structure and Files

{repo_structure}
