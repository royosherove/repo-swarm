version=1
Act as a mobile UI/UX architect. Analyze the user interface structure, navigation patterns, and screen organization in this mobile application.

**Special Instruction**: Only document UI components and navigation patterns that are ACTUALLY implemented in the codebase. Do NOT list UI frameworks, navigation libraries, or design systems that are not present.

## Screen Architecture

1. **Screen Organization:**
   - Main screens/activities/view controllers
   - Screen hierarchy and relationships
   - Screen naming conventions
   - Modular screen components

2. **Navigation Structure:**
   - Navigation type (Stack, Tab, Drawer, Bottom Navigation)
   - Navigation graph/storyboard setup
   - Deep linking configuration
   - Universal links/App links

3. **Routing:**
   - Route definitions
   - Parameter passing between screens
   - Navigation guards/middleware
   - Back navigation handling

## UI Components

1. **Component Library:**
   - Custom UI components
   - Reusable widgets/views
   - Component composition patterns
   - Atomic design implementation

2. **Platform-Specific Components:**
   - iOS: UIKit/SwiftUI components
   - Android: Views/Jetpack Compose
   - Cross-platform: React Native/Flutter widgets
   - Native module bridges

3. **Lists & Collections:**
   - List implementations (UITableView, RecyclerView, FlatList)
   - Cell/item reusability
   - Pull-to-refresh
   - Infinite scrolling
   - Section headers/footers

4. **Forms & Inputs:**
   - Input components and validation
   - Keyboard handling
   - Form state management
   - Error display patterns

## Styling & Theming

1. **Design System:**
   - Color schemes (light/dark mode)
   - Typography scales
   - Spacing system
   - Icon sets

2. **Responsive Design:**
   - Screen size adaptations
   - Tablet layouts
   - Orientation handling
   - Safe area management

3. **Animations:**
   - Transition animations
   - Gesture animations
   - Loading states
   - Micro-interactions

4. **Platform Consistency:**
   - iOS Human Interface Guidelines adherence
   - Material Design compliance
   - Platform-specific adaptations

## State & Data Binding

1. **UI State Management:**
   - View state handling
   - Loading/error/success states
   - Form state persistence
   - Navigation state

2. **Data Binding:**
   - MVVM bindings (SwiftUI, Data Binding, React hooks)
   - Observable patterns
   - Live data updates
   - Two-way binding

3. **Reactive Patterns:**
   - Reactive frameworks (RxSwift, RxJava, RxDart)
   - Stream management
   - Event buses
   - State machines

## User Interaction

1. **Gesture Handling:**
   - Touch gestures (tap, swipe, pinch, rotate)
   - Gesture recognizers
   - Custom gestures
   - Gesture conflicts resolution

2. **Feedback Mechanisms:**
   - Haptic feedback
   - Sound feedback
   - Visual feedback
   - Loading indicators

3. **Accessibility:**
   - VoiceOver/TalkBack support
   - Dynamic type support
   - Color contrast compliance
   - Semantic labels

## Media & Rich Content

1. **Image Handling:**
   - Image loading libraries (SDWebImage, Glide, Kingfisher)
   - Image caching strategies
   - Lazy loading
   - Progressive image loading

2. **Video/Audio:**
   - Media players
   - Streaming setup
   - Background playback
   - Picture-in-picture

3. **Rich Content:**
   - WebView integration
   - PDF viewers
   - Map integration
   - Charts and graphs

## Dialogs & Overlays

1. **Modal Presentations:**
   - Alert dialogs
   - Action sheets/bottom sheets
   - Custom modals
   - Popover presentations

2. **Notifications:**
   - In-app notifications/toasts
   - Snackbars
   - Banner notifications
   - Badge updates

3. **Overlays:**
   - Loading overlays
   - Tutorial overlays
   - Tooltips
   - Contextual menus

## Performance Optimization

1. **Rendering Performance:**
   - View recycling
   - Lazy rendering
   - Off-screen rendering
   - GPU optimization

2. **Memory Management:**
   - Image memory optimization
   - View lifecycle management
   - Memory leak prevention
   - Cache management

3. **Layout Performance:**
   - Constraint optimization
   - Layout caching
   - Avoid nested layouts
   - Async layout calculation

Format the output clearly using markdown

---

## Repository Structure and Files

{repo_structure}
