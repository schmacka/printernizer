# Setup Wizard - Design Document

> **Purpose**: Document design decisions for a first-run setup wizard in Printernizer
> **Status**: Brainstorming (not yet implemented)
> **Date**: 2025-12-16

---

## Overview

A guided setup wizard to help new users configure Printernizer on first run. The wizard should be:
- **Welcoming**: Make first-time setup feel approachable
- **Skippable**: Users can skip individual steps or the entire wizard
- **Re-accessible**: Can be run again from settings at any time

---

## Trigger Conditions

The wizard should appear when ANY of these conditions are met:

| Condition | Detection Method |
|-----------|------------------|
| No printers configured | `printer_service.get_all_printers()` returns empty |
| Fresh database | Check for `setup_wizard_completed` flag in settings table |
| User requests | "Run Setup Wizard" button in Settings page |

**Implementation Note**: Add `setup_wizard_completed` boolean to database settings table.

---

## Wizard Steps

### Step 1: Welcome Screen
**Purpose**: Introduce Printernizer and explain what the wizard will configure

**Content**:
- Brief welcome message
- What will be configured (bullet list)
- Two buttons: "Start Setup" / "Skip Wizard (Configure Manually)"

**Skip Behavior**: Skipping here skips the entire wizard

---

### Step 2: Add Your First Printer
**Purpose**: Get at least one printer connected

**Content**:
- Printer type selection (Bambu Lab / Prusa Core One)
- Network discovery integration ("Scan Network" button)
- Manual entry form with type-specific fields:
  - **Bambu Lab**: IP, Access Code (8 digits), Serial Number
  - **Prusa Core**: IP, API Key
- Connection test with feedback
- Printer name input

**Skip Behavior**: "Skip - I'll add printers later" button
- Wizard continues to next step
- User can add printers from Printers page anytime

**Reuse**: Leverage existing `PrinterFormHandler` and discovery logic

---

### Step 3: Configure Paths
**Purpose**: Set up storage locations for downloads and library

**Content**:
- **Downloads Path**: Where to save downloaded G-code files
  - Show current default
  - Browse/input field
  - Validate path exists and is writable
- **Library Path**: Where to organize your file library
  - Show current default
  - Browse/input field
  - Checkbox: "Enable Library feature"

**Environment-Aware Defaults**:
| Environment | Downloads Default | Library Default |
|-------------|-------------------|-----------------|
| Python/Dev | `./data/downloads` | `./data/library` |
| Docker | `/data/downloads` | `/data/library` |
| Home Assistant | `/data/downloads` | `/data/library` |
| Raspberry Pi | `~/printernizer/downloads` | `~/printernizer/library` |

**Skip Behavior**: "Use Defaults" button keeps current settings

---

### Step 4: Optional Features
**Purpose**: Enable/disable optional functionality

**Content**: Toggles with brief descriptions for:

| Feature | Default | Description |
|---------|---------|-------------|
| **Timelapse** | Off | Auto-generate timelapse videos from print photos |
| **Watch Folders** | Off | Monitor folders for new files to import |
| **MQTT Integration** | Off | Connect to Home Assistant via MQTT |

**Conditional Sub-Config**:
- If Timelapse enabled: Show source/output folder inputs
- If Watch Folders enabled: Add first watch folder path
- If MQTT enabled: Host, port, credentials

**Skip Behavior**: "Skip - Keep all defaults" leaves everything disabled

---

### Step 5: Summary & Finish
**Purpose**: Review configuration before applying

**Content**:
- Summary cards showing what was configured:
  - Printer(s) added (or "None - will configure later")
  - Paths configured
  - Features enabled
- "Finish Setup" button
- "Back" button to modify

**On Finish**:
1. Apply all settings
2. Set `setup_wizard_completed = true`
3. Redirect to Dashboard
4. Show success toast: "Setup complete! Welcome to Printernizer"

---

## UI/UX Design

### Layout
```
┌─────────────────────────────────────────────────────┐
│  [Logo]  Setup Wizard                    Step 2/5   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ● ● ○ ○ ○   (progress dots)                       │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │                                             │   │
│  │         Step Content Area                   │   │
│  │                                             │   │
│  │                                             │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  [← Back]              [Skip Step]    [Continue →] │
└─────────────────────────────────────────────────────┘
```

### Navigation
- **Back**: Go to previous step (disabled on step 1)
- **Skip Step**: Skip current step, use defaults
- **Continue**: Validate and proceed to next step
- **Progress Dots**: Visual indicator, clickable to jump back (not forward)

### Styling
- Reuse existing modal patterns from `components.css`
- Full-screen overlay (not modal) for immersive experience
- Match existing design system (colors, typography, spacing)
- German language throughout (consistent with app)

---

## Technical Implementation

### New Files
```
frontend/
  js/
    setup-wizard.js          # SetupWizardManager class
  css/
    setup-wizard.css         # Wizard-specific styles

src/
  api/routers/
    setup.py                 # Setup wizard API endpoints
```

### Modified Files
```
frontend/
  index.html                 # Add wizard HTML structure
  js/main.js                 # Add wizard trigger logic

src/
  main.py                    # Check wizard status on startup
  models/settings.py         # Add setup_wizard_completed field

database/
  migrations/
    0XX_add_setup_wizard_flag.sql
```

### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/setup/status` | Check if wizard should show |
| POST | `/api/v1/setup/complete` | Mark wizard as completed |
| POST | `/api/v1/setup/reset` | Reset wizard (for re-running) |

### State Management
- Wizard state lives only in memory (JavaScript)
- No persistence mid-wizard (restart on refresh/close)
- Final state applied atomically on "Finish"

---

## Edge Cases & Considerations

### What if printer connection fails during wizard?
- Show error message with retry option
- Allow user to continue anyway ("I'll fix this later")
- Don't block wizard progress

### What if path validation fails?
- Show clear error: "Path does not exist" or "Path is not writable"
- Offer to create directory if it doesn't exist
- Don't allow proceeding with invalid paths

### Home Assistant Add-on specifics
- Some paths may be restricted (HA sandbox)
- MQTT settings may auto-detect from HA Supervisor
- Consider pre-filling known HA defaults

### Re-running the wizard
- Warn user: "This will guide you through setup again. Existing settings will be shown as defaults."
- Pre-fill all fields with current values
- Allow modification without full reset

---

## Future Enhancements (Out of Scope for v1)

- [ ] Import settings from backup/export
- [ ] Multi-printer setup in single step
- [ ] Theme selection (light/dark)
- [ ] Language selection (when i18n is added)
- [ ] Quick-start templates ("Home User" / "Business" / "Print Farm")

---

## Design Decisions

| Question | Decision |
|----------|----------|
| **Wizard blocking** | Allow closing - show banner "Setup incomplete - [Resume Setup]" |
| **Mobile responsiveness** | Yes, follow existing responsive patterns |
| **Animations** | Not needed for v1 (can add later) |

---

## Summary

A 5-step setup wizard:
1. **Welcome** - Intro + skip entire option
2. **Printer** - Add first printer with discovery
3. **Paths** - Downloads + library locations
4. **Features** - Optional: Timelapse, Watch Folders, MQTT
5. **Summary** - Review and finish

Key principles:
- Every step is skippable
- No progress persistence (restarts on close)
- Same wizard for all deployment methods
- Re-accessible from settings anytime
