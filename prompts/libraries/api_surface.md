version=1
Act as a library API designer. Analyze the public API surface and interface design of this library.

**Special Instruction**: Only document API components and design patterns that are ACTUALLY implemented in the codebase. Do NOT list API design patterns, frameworks, or tools that are not present.

## Public API Analysis

1. **Entry Points:**
   - Main export(s)
   - Named exports
   - Default exports
   - Namespace organization

2. **Core Functions/Methods:**
   For each major function/method:
   - **Signature:** Name, parameters, return type
   - **Purpose:** What it does
   - **Usage Example:** Basic code snippet
   - **Options/Configuration:** Parameter objects, optional arguments
   - **Error Handling:** Exceptions thrown, error codes

3. **Classes/Constructors:**
   - Class hierarchy
   - Constructor parameters
   - Public methods
   - Static methods
   - Properties/getters/setters
   - Inheritance patterns

4. **Types & Interfaces:**
   - Type definitions
   - Generic types
   - Interface contracts
   - Enums and constants
   - Type guards/predicates

5. **Configuration Objects:**
   - Global configuration
   - Instance configuration
   - Default values
   - Validation rules

## API Design Patterns

1. **Method Chaining:**
   - Fluent interfaces
   - Builder patterns
   - Pipeline operations

2. **Async Patterns:**
   - Promises vs callbacks
   - Async/await support
   - Stream interfaces
   - Event emitters

3. **Error Handling:**
   - Error types/classes
   - Error recovery
   - Validation errors
   - Debug information

4. **Extensibility:**
   - Plugin system
   - Middleware support
   - Hooks/lifecycle methods
   - Custom implementations

## Developer Experience

1. **Type Safety:**
   - TypeScript definitions
   - JSDoc annotations
   - Runtime type checking
   - Type inference support

2. **Discoverability:**
   - Intuitive naming
   - Consistent patterns
   - IntelliSense support
   - Code completion hints

3. **Debugging Support:**
   - Debug modes
   - Logging capabilities
   - Source maps
   - Development vs production builds

4. **Performance Considerations:**
   - Lazy loading
   - Tree shaking support
   - Bundle size impact
   - Memory management

## API Stability

1. **Stable APIs:**
   - Core functionality
   - Long-term support
   - Backward compatibility

2. **Experimental APIs:**
   - Beta features
   - Unstable interfaces
   - Feature flags

3. **Deprecated APIs:**
   - Deprecated methods
   - Migration paths
   - Removal timeline

Format the output clearly using markdown

---

## Repository Structure and Files

{repo_structure}

