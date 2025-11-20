# Usage Statistics - Master Plan

**Status:** Planning
**Created:** 2025-11-20
**Owner:** Development Team
**Approach:** Option 1 - Local SQLite + Aggregation Service

## Executive Summary

Implement privacy-first, opt-in usage statistics for Printernizer to understand:
- How users deploy the application (HA add-on, Docker, Pi, standalone)
- Which features are most valuable
- Common pain points and error patterns
- Printer fleet composition (Bambu Lab vs Prusa)

**Core Principles:**
1. **Privacy First** - No personal data, no tracking without consent
2. **Transparency** - Users can see exactly what we collect
3. **Local First** - All data stored locally, submitted only if opted in
4. **Minimal Impact** - Lightweight, no performance degradation
5. **User Control** - Easy opt-in/opt-out, data deletion

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Printernizer Instance                      │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Usage Statistics Service                              │  │
│  │  - Record events locally                               │  │
│  │  - Aggregate weekly stats                              │  │
│  │  - Respect opt-in/opt-out                             │  │
│  └───────────────┬────────────────────────────────────────┘  │
│                  │                                            │
│  ┌───────────────▼────────────────────────────────────────┐  │
│  │  Local SQLite Database                                 │  │
│  │  - usage_events table (raw events)                     │  │
│  │  - usage_settings table (opt-in status, install ID)    │  │
│  │  - usage_aggregates table (pre-computed stats)         │  │
│  └───────────────┬────────────────────────────────────────┘  │
│                  │                                            │
└──────────────────┼────────────────────────────────────────────┘
                   │ HTTPS POST (if opted in)
                   │
         ┌─────────▼──────────────────────────────────────┐
         │  Aggregation Service (stats.printernizer.com)  │
         │  - FastAPI endpoint                            │
         │  - Rate limiting                               │
         │  - Validation                                  │
         └─────────┬──────────────────────────────────────┘
                   │
         ┌─────────▼──────────────────────────────────────┐
         │  SQL Server (Your Existing Infrastructure)     │
         │  - installations table                         │
         │  - daily_stats table                           │
         │  - events_summary table                        │
         └────────────────────────────────────────────────┘
```

## What We Collect (Privacy-Friendly)

### ✅ Anonymous Aggregated Data

| Metric | Example Value | Purpose |
|--------|--------------|---------|
| `installation_id` | `uuid4()` random | Distinguish unique installs (anonymous) |
| `app_version` | `"2.7.0"` | Track version adoption |
| `deployment_mode` | `"homeassistant"` | Understand deployment preferences |
| `printer_types` | `["bambu_lab", "prusa"]` | Hardware ecosystem understanding |
| `printer_count` | `3` | Fleet size distribution |
| `job_count_weekly` | `15` | Usage intensity |
| `feature_usage` | `{"library": true, "timelapse": false}` | Feature adoption |
| `uptime_days` | `7` | Stability metrics |
| `error_types` | `{"connection_timeout": 2}` | Anonymous error patterns |
| `country_code` | `"DE"` | Regional distribution (from timezone) |
| `python_version` | `"3.11.0"` | Runtime environment |
| `platform` | `"linux"` | OS distribution |

### ❌ What We DON'T Collect

- ❌ IP addresses (except temporary for rate limiting, not stored)
- ❌ User names or email addresses
- ❌ File names or content
- ❌ Printer serial numbers or network info
- ❌ API keys or credentials
- ❌ Precise timestamps (aggregated to day/week)
- ❌ URLs or network paths
- ❌ Individual printer status data

## Implementation Phases

### Phase 1: Local Collection (MVP) 🎯
**Goal:** Collect statistics locally, build opt-in UI
**Timeline:** Sprint 1-2
**Deliverables:**
- Database schema for local storage
- `UsageStatisticsService` implementation
- Settings UI with opt-in checkbox
- Privacy transparency dashboard
- Local statistics viewer

### Phase 2: Aggregation Service 🚀
**Goal:** Build backend to receive anonymous stats
**Timeline:** Sprint 3-4
**Deliverables:**
- FastAPI aggregation endpoint
- SQL Server schema
- Rate limiting and validation
- Automated submission (weekly cron)
- Error handling and retry logic

### Phase 3: Analytics Dashboard 📊
**Goal:** Visualize trends for development insights
**Timeline:** Sprint 5-6
**Deliverables:**
- Grafana/Metabase dashboard
- Key metrics visualization
- Trend analysis
- Anomaly detection

### Phase 4: Feedback Loop 🔄
**Goal:** Use insights to improve Printernizer
**Timeline:** Ongoing
**Deliverables:**
- Feature prioritization based on usage
- Error pattern analysis
- Deployment mode optimization
- User experience improvements

## User Experience

### Settings UI Mockup

```
┌─────────────────────────────────────────────────────────────┐
│ Settings > Privacy & Usage Statistics                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Help Improve Printernizer                                   │
│  ────────────────────────────                                │
│                                                               │
│  ☐ Share anonymous usage statistics                          │
│                                                               │
│  By opting in, you help us understand how Printernizer is    │
│  used and prioritize features that matter most to you.       │
│                                                               │
│  What we collect:                                            │
│  • Deployment mode (Docker, Home Assistant, etc.)            │
│  • Number and types of printers                              │
│  • Feature usage (library, timelapse, etc.)                  │
│  • Anonymous error reports                                   │
│  • App version and platform                                  │
│                                                               │
│  What we DON'T collect:                                      │
│  • IP addresses or location data                             │
│  • File names or print job details                           │
│  • Personal information                                      │
│  • Printer serial numbers                                    │
│                                                               │
│  [View Privacy Policy] [View My Local Statistics]            │
│  [Export My Data] [Delete All Statistics]                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Local Statistics Viewer

```
┌─────────────────────────────────────────────────────────────┐
│ Your Local Usage Statistics                                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Installation ID: abc123...xyz (anonymous)                   │
│  First Used: 2024-11-01                                      │
│  Total Uptime: 45 days                                       │
│                                                               │
│  This Week:                                                  │
│  • Jobs completed: 23                                        │
│  • Files downloaded: 18                                      │
│  • Active printers: 2                                        │
│  • Errors encountered: 0                                     │
│                                                               │
│  Features You Use:                                           │
│  ✓ Library System                                            │
│  ✓ Auto Job Creation                                         │
│  ✗ Timelapse (disabled)                                      │
│  ✗ German Business Features (disabled)                       │
│                                                               │
│  [Download as JSON] [View Full History]                      │
│                                                               │
│  This data is stored locally on your device.                 │
│  Last submitted: Never (opt-in disabled)                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Technical Requirements

### Dependencies
- No new dependencies required! ✅
- Use existing: `aiosqlite`, `aiohttp`, `structlog`
- Optional: `python-dateutil` (already installed)

### Performance Requirements
- Event recording: < 1ms (non-blocking)
- Weekly aggregation: < 5 seconds
- Database size: < 10MB after 1 year
- Network submission: < 1 second (async, background)

### Privacy Requirements
- No PII (Personally Identifiable Information)
- No tracking without explicit consent
- Data deletion within 24 hours of opt-out
- Transparent data export
- GDPR/CCPA compliant

### Security Requirements
- HTTPS-only submission
- Installation ID rotation (optional yearly)
- Rate limiting on aggregation endpoint
- Input validation and sanitization
- No sensitive data in error reports

## Success Metrics

### Adoption Metrics
- Opt-in rate: Target 30-50%
- Active installations tracked
- Weekly submission rate

### Technical Metrics
- Performance impact: < 1% CPU/memory overhead
- Database size growth: < 1MB/month
- Submission success rate: > 95%
- Error rate: < 0.1%

### Insights Metrics (After Phase 2)
- Top 5 deployment modes
- Feature adoption rates
- Common error patterns
- Version upgrade patterns

## Open Questions

- [ ] Should we rotate installation IDs periodically for extra privacy?
- [ ] Weekly vs daily submissions - what's the right balance?
- [ ] Should we allow users to see aggregated stats from all users?
- [ ] Do we need a "data retention policy" setting (e.g., auto-delete after 90 days)?
- [ ] Should error reports include stack traces (anonymized)?

## Related Documents

- [Privacy Policy Draft](./usage-statistics-privacy.md)
- [Technical Specification](./usage-statistics-technical-spec.md)
- [Implementation Roadmap](./usage-statistics-roadmap.md)

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-11-20 | Initial plan created | Development Team |

---

**Next Steps:**
1. Review and approve this plan
2. Define detailed privacy policy
3. Design database schema
4. Implement Phase 1 (local collection)
