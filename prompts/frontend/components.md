version=1
Act as a frontend component architect. Analyze the component structure and design patterns in this frontend application.

**Special Instruction**: Only document components and design patterns that are ACTUALLY implemented in the codebase. Do NOT list component libraries, frameworks, or patterns that are not present.

Please analyze:

1. **Component Organization:**
   - Directory structure for components
   - Component naming conventions
   - Atomic design levels (atoms, molecules, organisms, templates, pages)

2. **Core Components:**
   List and describe the main reusable components:
   - Layout components (Header, Footer, Sidebar, Navigation)
   - Form components (Input, Select, Checkbox, etc.)
   - Display components (Card, Modal, Table, List)
   - Feedback components (Alert, Toast, Loading, Error)

3. **Component Patterns:**
   - Presentational vs Container components
   - Higher-Order Components (HOCs)
   - Render props patterns
   - Custom hooks (for React) or composables (for Vue)
   - Component composition strategies

4. **Props & Data Flow:**
   - Props validation/typing approach
   - Event handling patterns
   - Data flow between components
   - Context providers or injection patterns

5. **Styling Patterns:**
   - CSS-in-JS implementation
   - Style encapsulation methods
   - Theme provider usage
   - Responsive design approach

6. **Component Testing:**
   - Unit test coverage for components
   - Testing utilities and patterns
   - Snapshot testing
   - Visual regression testing

7. **Design System Integration:**
   - Use of component libraries (Material-UI, Ant Design, etc.)
   - Custom design tokens
   - Accessibility standards (ARIA, WCAG)

8. **Performance Patterns:**
   - Memoization strategies
   - Virtual scrolling
   - Lazy loading components
   - Code splitting boundaries

For each major component, include:
- Purpose and responsibility
- Props interface
- State management approach
- Reusability level

Format the output clearly using markdown

---

## Repository Structure and Files

{repo_structure}

