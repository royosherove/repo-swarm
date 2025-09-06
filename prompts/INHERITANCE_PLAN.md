# Prompts Inheritance Implementation Plan

## Overview
Implement a base prompts inheritance system where all domain-specific prompts.json files inherit from a common base_prompts.json, ensuring consistency across all project types.

## Key Principles
1. All base prompts come from the `shared/` folder
2. No domain-specific overrides for base prompts
3. Domains only add their specific analysis prompts
4. Order determined by array sequence, not order fields
5. Generic domain only inherits base, adds nothing

## Implementation Status

### Phase 1: Move Generic Prompts to Shared
- [x] Move `generic/hl_overview.md` → `shared/hl_overview.md`
- [x] Move `generic/module_deep_dive.md` → `shared/module_deep_dive.md`
- [x] Move `generic/db.md` → `shared/db.md`
- [x] Move `generic/apis.md` → `shared/apis.md`
- [x] Move `generic/events.md` → `shared/events.md`

### Phase 2: Delete Domain-Specific Duplicates
- [x] Delete `backend/hl_overview.md`
- [x] Delete `backend/apis.md`
- [x] Delete `frontend/hl_overview.md`
- [x] Delete `mobile/hl_overview.md`
- [x] Delete `libraries/hl_overview.md`
- [x] Delete `infra-as-code/hl_overview.md`

### Phase 3: Create Base Configuration
- [x] Create `base_prompts.json` with all 12 shared prompts

### Phase 4: Update Domain Configurations
- [x] Update `generic/prompts.json` - only extends base
- [x] Update `backend/prompts.json` - adds data_layer, events_and_messaging
- [x] Update `frontend/prompts.json` - adds components, state_and_data
- [x] Update `mobile/prompts.json` - adds ui_and_navigation, api_and_network, device_features, data_and_persistence
- [x] Update `libraries/prompts.json` - adds api_surface, internals
- [x] Update `infra-as-code/prompts.json` - adds resources, environments

### Phase 5: Update Loading Logic
- [x] Check and update prompt loading code to support inheritance
- [x] Updated FileManager.read_prompts_config() to handle "extends" and "additional_prompts"
- [x] Removed order field sorting in investigate_activities.py (order now determined by array sequence)
- [x] Test that all prompts load correctly with new structure - All tests passing!

## Base Prompts Structure (12 prompts)
```json
{
  "processing_order": [
    {"name": "hl_overview", "file": "shared/hl_overview.md", "description": "High level overview of the codebase"},
    {"name": "module_deep_dive", "file": "shared/module_deep_dive.md", "description": "Deep dive into modules", "context": [{"type": "step", "val": "hl_overview"}]},
    {"name": "dependencies", "file": "shared/dependencies.md", "description": "Analyze dependencies and external libraries", "context": [{"type": "step", "val": "hl_overview"}]},
    {"name": "core_entities", "file": "shared/core_entities.md", "description": "Core entities and their relationships"},
    {"name": "DBs", "file": "shared/db.md", "description": "databases analysis"},
    {"name": "APIs", "file": "shared/apis.md", "description": "APIs analysis"},
    {"name": "events", "file": "shared/events.md", "description": "events analysis"},
    {"name": "service_dependencies", "file": "shared/service_dependencies.md", "description": "Analyze service dependencies", "context": [{"type": "step", "val": "hl_overview"}, {"type": "step", "val": "APIs"}, {"type": "step", "val": "events"}]},
    {"name": "authentication", "file": "shared/authentication.md", "description": "Authentication mechanisms analysis"},
    {"name": "authorization", "file": "shared/authorization.md", "description": "Authorization and access control analysis"},
    {"name": "data_mapping", "file": "shared/data_mapping.md", "description": "Data flow and personal information mapping"},
    {"name": "security_check", "file": "shared/security_check.md", "description": "Top 10 security vulnerabilities assessment"}
  ]
}
```

## Domain-Specific Additions

### Backend (2 additional)
- data_layer.md - Data persistence and access patterns
- events_and_messaging.md - Asynchronous communication and event patterns

### Frontend (2 additional)
- components.md - Component architecture and design patterns
- state_and_data.md - State management and data flow patterns

### Mobile (4 additional)
- ui_and_navigation.md - UI architecture and navigation patterns
- api_and_network.md - API integration and network communication
- device_features.md - Native device features and capabilities
- data_and_persistence.md - Data persistence and state management

### Libraries (2 additional)
- api_surface.md - Public API analysis and design patterns
- internals.md - Internal architecture and implementation

### Infra-as-code (2 additional)
- resources.md - Detailed analysis of infrastructure resources
- environments.md - Environment management and deployment strategies

## Expected Results
- Generic: 12 prompts (base only)
- Backend: 14 prompts (12 base + 2 domain)
- Frontend: 14 prompts (12 base + 2 domain)
- Mobile: 16 prompts (12 base + 4 domain)
- Libraries: 14 prompts (12 base + 2 domain)
- Infra-as-code: 14 prompts (12 base + 2 domain)

## Benefits
1. **Consistency**: All domains get same comprehensive base analysis
2. **Maintainability**: Single source of truth for shared prompts
3. **DRY Principle**: No duplication across domain configurations
4. **Simplicity**: Clean inheritance model without overrides
5. **Completeness**: All projects get security, auth, monitoring analysis
