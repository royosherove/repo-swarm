version=2
You are a frontend state management expert. Analyze how this application manages state and handles data flow.

**Special Instruction**: If no state management is found, return "no state management pattern detected". Only document state management libraries and patterns that are ACTUALLY implemented in the codebase. Do NOT list state management tools or frameworks that are not present.

Please analyze:

## State Management

1. **Global State:**
   - State management library/pattern used
   - Store structure and organization
   - Actions, mutations, or reducers
   - State persistence mechanisms

2. **Local Component State:**
   - useState/reactive patterns
   - Form state management
   - UI state (modals, tabs, accordions)

3. **Server State:**
   - Data fetching libraries (React Query, SWR, Apollo Client)
   - Caching strategies
   - Optimistic updates
   - Real-time data subscriptions

## Data Flow

1. **API Integration:**
   - HTTP client configuration (Axios, Fetch, etc.)
   - API endpoint organization
   - Request/response interceptors
   - Error handling patterns

2. **Data Transformations:**
   - Serialization/deserialization
   - Data normalization patterns
   - Computed/derived state

3. **Authentication & Authorization:**
   - Auth state management
   - Token storage and refresh
   - Protected routes implementation
   - Permission-based rendering

4. **Form Management:**
   - Form libraries (Formik, React Hook Form, VeeValidate)
   - Validation strategies
   - Error handling and display
   - Multi-step form patterns

5. **Real-time Features:**
   - WebSocket connections
   - Server-Sent Events
   - Polling strategies
   - Optimistic UI updates

6. **Performance Optimizations:**
   - Memoization of expensive computations
   - Debouncing/throttling
   - Pagination/infinite scroll
   - Data prefetching

For each pattern, include:
- Implementation approach
- Key files/modules
- Data flow diagram (if complex)
- Performance implications

Format the output clearly using markdown

---

## Repository Structure and Files

{repo_structure}

---

## Dependencies

{repo_deps}

