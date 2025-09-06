version=1
You are a mobile platform integration expert. Analyze all device feature usage, native capabilities, and platform-specific integrations in this mobile application.

**Special Instruction**: If no device features are used, return "no device features integrated". Only document device features and platform integrations that are ACTUALLY implemented in the codebase. Do NOT list device capabilities or frameworks that are not present.

## Core Device Features

1. **Camera & Photos:**
   - Camera access and configuration
   - Photo library/gallery access
   - Image capture settings
   - Video recording capabilities
   - QR/Barcode scanning
   - Photo editing features
   - Live camera preview

2. **Location Services:**
   - GPS/location permissions
   - Location accuracy settings
   - Geofencing implementation
   - Background location tracking
   - Location-based notifications
   - Maps integration
   - Geocoding/reverse geocoding

3. **Sensors:**
   - Accelerometer usage
   - Gyroscope integration
   - Magnetometer/compass
   - Proximity sensor
   - Ambient light sensor
   - Barometer
   - Pedometer/motion activity

4. **Connectivity:**
   - Bluetooth/BLE integration
   - NFC capabilities
   - WiFi Direct
   - Network state monitoring
   - Airplane mode detection
   - Cellular data usage

## Platform Services

1. **Push Notifications:**
   - Push notification setup (FCM, APNs)
   - Notification channels/categories
   - Rich notifications (images, actions)
   - Silent/background notifications
   - Local notifications
   - Notification scheduling
   - Deep link handling from notifications

2. **Background Processing:**
   - Background tasks/jobs
   - Background fetch
   - Work manager/job scheduler
   - Background services
   - Foreground services
   - Wake locks
   - Background restrictions handling

3. **Storage & Files:**
   - File system access
   - Document picker
   - External storage
   - App sandbox/container
   - File sharing (share sheet)
   - Cloud storage integration (iCloud, Google Drive)
   - Database usage (SQLite, Core Data, Room, Realm)

4. **System Integration:**
   - Contacts access
   - Calendar integration
   - Reminders/tasks
   - Phone/SMS capabilities
   - Email integration
   - Browser integration
   - App-to-app communication

## Media & Audio

1. **Audio Capabilities:**
   - Audio recording
   - Audio playback
   - Audio session management
   - Background audio
   - Audio routing (speaker, headphones)
   - Voice recognition
   - Text-to-speech

2. **Media Control:**
   - Media player controls
   - Now playing info
   - Remote control events
   - Lock screen controls
   - CarPlay/Android Auto

## Security & Privacy

1. **Biometric Authentication:**
   - Face ID/Face Unlock
   - Touch ID/Fingerprint
   - Biometric prompt implementation
   - Fallback mechanisms
   - Secure enclave usage

2. **Permissions Management:**
   - Runtime permissions
   - Permission rationale
   - Permission denied handling
   - Settings redirect
   - Privacy manifest (iOS 17+)

3. **Data Protection:**
   - Keychain/Keystore usage
   - Encrypted storage
   - App transport security
   - Data protection classes
   - Secure coding practices

## Platform-Specific Features

1. **iOS Specific:**
   - HealthKit integration
   - HomeKit support
   - SiriKit/Shortcuts
   - Apple Pay
   - iMessage apps
   - Today widgets
   - App Clips

2. **Android Specific:**
   - Google Pay
   - Android widgets
   - App shortcuts
   - Instant Apps
   - Android Auto
   - Wear OS companion
   - Android TV support

3. **Cross-Platform Bridges:**
   - Native modules (React Native)
   - Platform channels (Flutter)
   - Plugin architecture
   - Method channels
   - Event channels

## App Lifecycle & State

1. **Lifecycle Management:**
   - App launch handling
   - Foreground/background transitions
   - App termination
   - State restoration
   - Deep link handling
   - URL schemes
   - Universal/App links

2. **Memory & Resources:**
   - Memory warnings handling
   - Low memory management
   - Battery optimization
   - Doze mode handling
   - App standby
   - Background limits

## Accessibility Features

1. **Screen Readers:**
   - VoiceOver support (iOS)
   - TalkBack support (Android)
   - Accessibility labels
   - Accessibility hints
   - Custom actions

2. **Visual Accommodations:**
   - Dynamic type support
   - High contrast mode
   - Color blind support
   - Reduce motion
   - Larger text

3. **Motor Accommodations:**
   - Switch control
   - Voice control
   - Assistive touch
   - Keyboard navigation

## Testing & Debugging

1. **Device Testing:**
   - Physical device testing setup
   - Simulator/emulator configuration
   - Remote debugging
   - Performance profiling
   - Memory profiling

2. **Platform-Specific Testing:**
   - UI testing frameworks
   - Unit testing setup
   - Integration testing
   - Monkey testing
   - Accessibility testing

Format the output clearly using markdown

---

## Repository Structure and Files

{repo_structure}
