# Usage Statistics - Privacy Policy

**Version:** 1.0 (Draft)
**Last Updated:** 2025-11-20
**Status:** Draft for Review

## Overview

This document defines the privacy policy for Printernizer's usage statistics feature. It outlines what data we collect, how we use it, and how we protect user privacy.

## Core Privacy Principles

### 1. **Opt-In by Default**
- Usage statistics collection is **OFF by default**
- Users must explicitly enable it
- Clear explanation provided before enabling
- Easy opt-out at any time

### 2. **Transparency**
- Full disclosure of collected data
- Users can view their local statistics
- Users can export their data as JSON
- No hidden tracking

### 3. **Data Minimization**
- Collect only what's necessary
- Aggregate data where possible
- No personally identifiable information (PII)
- No tracking across devices

### 4. **Local-First Architecture**
- All statistics stored locally first
- Submission only if user opts in
- Works fully offline
- User retains full control

### 5. **Right to Deletion**
- Users can delete all local statistics
- Submitted data removed within 24 hours of opt-out request
- No data remnants after deletion

## What We Collect

### System Information (Non-Personal)

```json
{
  "installation_id": "550e8400-e29b-41d4-a716-446655440000",  // Random UUID
  "app_version": "2.7.0",
  "python_version": "3.11.0",
  "platform": "linux",
  "deployment_mode": "homeassistant",
  "country_code": "DE"  // Derived from timezone setting, not IP
}
```

**Purpose:** Understand technical environment and deployment patterns

### Printer Fleet Information (Anonymous)

```json
{
  "printer_count": 3,
  "printer_types": ["bambu_lab", "prusa"],
  "printer_type_counts": {
    "bambu_lab": 2,
    "prusa": 1
  }
}
```

**Purpose:** Understand hardware ecosystem and multi-printer setups

**What we DON'T collect:**
- ❌ Printer serial numbers
- ❌ Printer names or labels
- ❌ Network addresses or hostnames
- ❌ Printer credentials

### Usage Patterns (Aggregated)

```json
{
  "period": "2024-11-14T00:00:00Z",  // Week start, no precise timestamps
  "job_count": 23,
  "file_count": 18,
  "upload_count": 5,
  "uptime_hours": 168,
  "feature_usage": {
    "library_enabled": true,
    "timelapse_enabled": false,
    "auto_job_creation_enabled": true,
    "german_compliance_enabled": false
  }
}
```

**Purpose:** Understand usage intensity and feature adoption

**What we DON'T collect:**
- ❌ File names or content
- ❌ Print job details (model names, materials, etc.)
- ❌ Exact timestamps (aggregated to day/week)
- ❌ User interactions or click tracking

### Error Information (Anonymous)

```json
{
  "period": "2024-11-14T00:00:00Z",
  "error_summary": {
    "connection_timeout": 2,
    "file_download_failed": 1,
    "unknown_error": 0
  },
  "error_contexts": [
    {
      "error_type": "connection_timeout",
      "component": "printer_service",
      "count": 2
      // NO stack traces, NO file paths, NO personal info
    }
  ]
}
```

**Purpose:** Identify common issues to improve stability

**What we DON'T collect:**
- ❌ Full stack traces
- ❌ File paths or system information
- ❌ User input or configuration values
- ❌ Network details

## What We DON'T Collect (Strict Rules)

### Personal Information
- ❌ Names, email addresses, or contact information
- ❌ Home Assistant usernames or credentials
- ❌ API keys or access tokens
- ❌ IP addresses (except temporary for rate limiting, not stored)

### Location Data
- ❌ GPS coordinates
- ❌ IP-based geolocation
- ✅ Only country code derived from timezone setting (user-configured)

### Behavioral Tracking
- ❌ Click tracking or UI interactions
- ❌ Time spent in different screens
- ❌ Mouse movements or keyboard input
- ❌ Session recordings

### File or Print Data
- ❌ File names or paths
- ❌ File contents or previews
- ❌ Model names or descriptions
- ❌ Print settings or slicing parameters
- ❌ Thumbnails or images

### Network Information
- ❌ Printer IP addresses or hostnames
- ❌ Network topology
- ❌ MAC addresses
- ❌ WiFi SSIDs

### Device Identifiers
- ❌ Printer serial numbers
- ❌ Raspberry Pi serial numbers
- ❌ Home Assistant installation IDs
- ✅ Only randomly generated installation_id (not tied to hardware)

## How We Use Collected Data

### Development Insights
- **Feature Prioritization:** Focus on features users actually use
- **Platform Support:** Prioritize deployment modes (Docker vs HA vs Pi)
- **Bug Fixes:** Identify common error patterns
- **Performance Optimization:** Focus on bottlenecks that affect most users

### Examples of Insights

**Good (Privacy-Friendly):**
- "60% of users run Printernizer as a Home Assistant add-on"
- "Timelapse feature is enabled by only 15% of users"
- "Connection timeouts occur most frequently on version 2.6.x"
- "Users with 3+ printers use the library feature 90% of the time"

**Bad (Would Violate Privacy):**
- "User John Doe printed model 'Secret_Project.3mf' 5 times"
- "Installation abc123 is located at 192.168.1.100"
- "User clicked 'Settings' button 47 times last week"
- "Printer serial XYZ123 is running firmware 1.2.3"

### Data Sharing
- **We DO NOT sell or share data with third parties**
- **We DO NOT use data for advertising**
- **We DO NOT cross-reference with other datasets**
- Data is used internally for Printernizer development only

## Data Storage & Security

### Local Storage (User's Device)
- **Location:** SQLite database in Printernizer's data directory
- **Encryption:** Standard filesystem permissions (no special encryption needed)
- **Retention:** Indefinite, until user deletes or opts out
- **Access:** Only Printernizer application

### Remote Storage (If Opted In)
- **Location:** Your SQL server (Europe-based recommended for GDPR)
- **Encryption:** HTTPS in transit, encrypted at rest
- **Retention:** 2 years (configurable)
- **Access:** Development team only, no third parties

### Security Measures
- ✅ HTTPS-only submission
- ✅ Rate limiting (max 1 submission per hour per installation)
- ✅ Input validation and sanitization
- ✅ No sensitive data in logs
- ✅ Regular security audits

## User Rights (GDPR/CCPA Compliance)

### Right to Access
- **Local Statistics Viewer:** See all collected data in the UI
- **Export to JSON:** Download complete local statistics
- **Transparency:** Full disclosure of submission payload

### Right to Deletion
- **Delete Local Statistics:** Remove all data from local database
- **Request Deletion:** Submit opt-out request to delete remote data
- **Deletion Timeline:** Within 24 hours for remote data

### Right to Opt-Out
- **Easy Toggle:** Single checkbox in settings
- **Immediate Effect:** No more data submitted after opt-out
- **Historical Data:** Existing data can be deleted separately

### Right to Portability
- **Export Format:** Standard JSON format
- **Complete Data:** All local statistics included
- **Machine-Readable:** Easy to process or transfer

## Compliance

### GDPR (General Data Protection Regulation)
- ✅ **Lawful Basis:** Consent (opt-in)
- ✅ **Data Minimization:** Only necessary data collected
- ✅ **Purpose Limitation:** Used only for development insights
- ✅ **Transparency:** Clear privacy policy and disclosure
- ✅ **User Rights:** Access, deletion, portability, opt-out
- ✅ **Storage Limitation:** 2-year retention policy

### CCPA (California Consumer Privacy Act)
- ✅ **Right to Know:** Users can see collected data
- ✅ **Right to Delete:** Deletion available on request
- ✅ **Right to Opt-Out:** Easy opt-out mechanism
- ✅ **No Sale:** Data is never sold or shared

### Children's Privacy
- Printernizer is not directed at children under 13
- No special provisions needed (business/technical tool)

## Anonymization Techniques

### Installation ID
- **Method:** UUIDv4 (random, not derived from hardware)
- **Rotation:** Can be regenerated manually
- **Purpose:** Distinguish installations without identifying users

### Temporal Aggregation
- **Method:** Round timestamps to day/week boundaries
- **Example:** `2024-11-14T00:00:00Z` (week start) instead of precise timestamp
- **Purpose:** Prevent timing-based identification

### Geographic Aggregation
- **Method:** Country code from timezone, not IP geolocation
- **Example:** `"DE"` instead of city or coordinates
- **Purpose:** Regional trends without precise location

### Error Sanitization
- **Method:** Remove file paths, stack traces, user input
- **Example:** `"connection_timeout"` instead of `"Failed to connect to printer at 192.168.1.5"`
- **Purpose:** Useful error patterns without sensitive context

## Changes to Privacy Policy

### Notification
- Users will be notified of material changes
- Re-consent required for expanded data collection
- Changelog maintained in this document

### Version History
| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-20 | Initial draft |

## Contact & Questions

**For privacy questions or data deletion requests:**
- GitHub Issues: https://github.com/schmacka/printernizer/issues
- Label: `privacy`

**Response Time:**
- Privacy inquiries: Within 72 hours
- Deletion requests: Within 24 hours

---

## Sample Data Payload

This is an example of what gets submitted if you opt in:

```json
{
  "schema_version": "1.0",
  "submission_timestamp": "2024-11-20T12:00:00Z",
  "installation": {
    "installation_id": "550e8400-e29b-41d4-a716-446655440000",
    "first_seen": "2024-11-01T00:00:00Z",
    "app_version": "2.7.0",
    "python_version": "3.11.0",
    "platform": "linux",
    "deployment_mode": "homeassistant",
    "country_code": "DE"
  },
  "period": {
    "start": "2024-11-14T00:00:00Z",
    "end": "2024-11-21T00:00:00Z",
    "duration_days": 7
  },
  "printer_fleet": {
    "printer_count": 3,
    "printer_types": ["bambu_lab", "prusa"],
    "printer_type_counts": {
      "bambu_lab": 2,
      "prusa": 1
    }
  },
  "usage_stats": {
    "job_count": 23,
    "file_count": 18,
    "upload_count": 5,
    "uptime_hours": 168,
    "feature_usage": {
      "library_enabled": true,
      "timelapse_enabled": false,
      "auto_job_creation_enabled": true,
      "german_compliance_enabled": false,
      "watch_folders_enabled": true
    }
  },
  "error_summary": {
    "connection_timeout": 2,
    "file_download_failed": 1
  }
}
```

**Size:** ~800 bytes
**Frequency:** Once per week (if opted in)
**Anonymity:** No PII, no file names, no network info

---

**Note:** This is a draft document for internal review. Final version will be presented to users in the settings UI and on the project website.
