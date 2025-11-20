# Usage Statistics - Documentation Index

**Overview:** Privacy-first, opt-in usage statistics for Printernizer
**Approach:** Local SQLite + Optional Aggregation Service
**Status:** Planning Complete, Ready for Implementation

---

## 📚 Planning Documents

### 1. [Master Plan](./usage-statistics-plan.md)
**Purpose:** High-level overview and architecture
**Read this first:** Understand the big picture, goals, and approach

**Key Sections:**
- Executive summary
- Architecture diagram
- What we collect (and don't collect)
- Implementation phases
- User experience mockups

**Best for:** Product managers, stakeholders, new team members

---

### 2. [Privacy Policy](./usage-statistics-privacy.md)
**Purpose:** Define privacy principles and compliance
**Read this for:** Understanding privacy guarantees and legal requirements

**Key Sections:**
- Core privacy principles
- Detailed data collection catalog
- What we DON'T collect (strict rules)
- GDPR/CCPA compliance
- Sample data payload
- User rights

**Best for:** Privacy review, user communication, legal compliance

---

### 3. [Technical Specification](./usage-statistics-technical-spec.md)
**Purpose:** Implementation details and code architecture
**Read this for:** Building the system

**Key Sections:**
- System architecture
- Database schema (SQLite)
- Pydantic data models
- Service layer implementation
- API endpoints
- Integration points
- Testing strategy
- Migration scripts

**Best for:** Backend developers, code review, implementation

---

### 4. [Implementation Roadmap](./usage-statistics-roadmap.md)
**Purpose:** Step-by-step implementation plan with timelines
**Read this for:** Project management and task breakdown

**Key Sections:**
- Phase 1: Local Collection & UI (3 weeks)
- Phase 2: Aggregation Service (3 weeks)
- Phase 3: Analytics Dashboard (2 weeks)
- Phase 4: Feedback Loop (ongoing)
- Task breakdown with time estimates
- Success criteria for each phase
- Risk management

**Best for:** Project managers, sprint planning, tracking progress

---

## 🚀 Quick Start

### For Developers (Starting Implementation)

1. **Read:** [Technical Specification](./usage-statistics-technical-spec.md)
2. **Review:** Database schema and data models
3. **Start with:** Phase 1, Task 1.1 (Database migration)
4. **Reference:** [Roadmap](./usage-statistics-roadmap.md) for task details

### For Product/PM (Understanding the Feature)

1. **Read:** [Master Plan](./usage-statistics-plan.md)
2. **Review:** User experience mockups
3. **Check:** [Roadmap](./usage-statistics-roadmap.md) for timeline
4. **Reference:** [Privacy Policy](./usage-statistics-privacy.md) for user communication

### For Privacy Review

1. **Read:** [Privacy Policy](./usage-statistics-privacy.md)
2. **Review:** "What we DON'T collect" section
3. **Check:** Sample data payload (end of privacy doc)
4. **Verify:** GDPR/CCPA compliance checklist

---

## 🎯 Key Decisions Made

### Architecture
- ✅ **Local-first:** SQLite storage on user's device
- ✅ **Opt-in only:** Default OFF, user explicitly enables
- ✅ **Aggregation service:** Separate FastAPI app with SQL Server
- ✅ **Weekly submission:** Balance privacy and insights

### Privacy
- ✅ **No PII:** Strictly anonymous data only
- ✅ **Transparency:** Users can view all collected data
- ✅ **User control:** Export, delete, opt-out anytime
- ✅ **GDPR compliant:** All user rights respected

### Technical
- ✅ **No new dependencies:** Use existing stack (aiosqlite, aiohttp)
- ✅ **Non-blocking:** Never impact app performance
- ✅ **Fail-safe:** Statistics errors don't break app
- ✅ **All deployment modes:** Works in HA, Docker, Pi, standalone

---

## 📊 Quick Reference

### What We Collect

| Category | Examples | Privacy Level |
|----------|----------|---------------|
| **System Info** | App version, Python version, platform | ✅ Safe |
| **Deployment** | "homeassistant", "docker", "standalone" | ✅ Safe |
| **Printer Fleet** | Count: 3, Types: ["bambu_lab", "prusa"] | ✅ Safe |
| **Usage Stats** | Jobs: 23/week, Files: 18/week, Uptime: 7 days | ✅ Safe |
| **Feature Usage** | Library: enabled, Timelapse: disabled | ✅ Safe |
| **Error Summary** | {"connection_timeout": 2} (type only) | ✅ Safe |

### What We DON'T Collect

| Category | Why Not | Enforcement |
|----------|---------|-------------|
| **Personal Info** | User names, emails | ❌ Code validation |
| **File Data** | File names, paths, content | ❌ Code validation |
| **Network Info** | IPs, hostnames, MACs | ❌ Code validation |
| **Device IDs** | Serial numbers, hardware IDs | ❌ Code validation |
| **Location** | GPS, IP geolocation | ✅ Country from timezone only |
| **Behavioral** | Clicks, time on page, sessions | ❌ Not implemented |

---

## 🔍 Implementation Checklist

### Phase 1: Local Collection (Ready to Start)

- [ ] **Database Migration** (2 days)
  - Create `usage_events` table
  - Create `usage_settings` table
  - Add indexes
  - Test migration

- [ ] **Data Models** (2 days)
  - Pydantic models for events
  - Validation rules
  - Unit tests

- [ ] **Repository Layer** (3 days)
  - CRUD operations
  - Query methods
  - Tests

- [ ] **Service Layer** (4 days)
  - Event recording
  - Opt-in/opt-out
  - Aggregation
  - Export/delete

- [ ] **API Endpoints** (3 days)
  - 5 REST endpoints
  - OpenAPI docs
  - Tests

- [ ] **Frontend UI** (7 days)
  - Settings page
  - Statistics viewer
  - Privacy disclosure
  - Export/delete buttons

- [ ] **Integration** (3 days)
  - Hook into existing services
  - Non-blocking design
  - Error handling

- [ ] **Testing** (4 days)
  - Unit tests (90% coverage)
  - Integration tests
  - Privacy audit

**Total Phase 1:** ~3 weeks

---

## 🛠️ Developer Guidelines

### Adding New Event Types

```python
# 1. Define event type (use snake_case)
event_type = "printer_connected"

# 2. Prepare metadata (no PII!)
metadata = {
    "printer_type": "bambu_lab",  # ✅ Good
    # "printer_serial": "ABC123",  # ❌ BAD - NO device IDs
    # "printer_ip": "192.168.1.5", # ❌ BAD - NO network info
}

# 3. Record event
await stats_service.record_event(event_type, metadata)
```

### Privacy Checklist (Before Adding New Data)

- [ ] Is this data necessary?
- [ ] Can we aggregate it instead of storing raw?
- [ ] Does it contain PII? (if yes, DON'T collect)
- [ ] Does it contain file names/paths? (if yes, DON'T collect)
- [ ] Does it contain network info? (if yes, DON'T collect)
- [ ] Can users understand what this is? (transparency test)
- [ ] Would I be comfortable if this was public? (privacy test)

---

## 📈 Success Metrics

### Phase 1 Success (Local Collection)
- ✅ Statistics collected locally
- ✅ < 1% performance overhead
- ✅ 90%+ test coverage
- ✅ Works in all deployment modes
- ✅ Zero PII collected (verified by tests)

### Phase 2 Success (Aggregation)
- ✅ Aggregation service deployed
- ✅ Weekly submissions working
- ✅ 99.9% uptime
- ✅ 30-50% opt-in rate (goal)

### Phase 3 Success (Dashboard)
- ✅ Key metrics visualized
- ✅ Trends identified
- ✅ First insight actionable

### Overall Success (Feedback Loop)
- ✅ Feature roadmap informed by data
- ✅ Error rates decreasing
- ✅ User trust maintained
- ✅ Community engagement strong

---

## 🔗 Related Documents

### Existing Documentation
- [`CLAUDE.md`](../../CLAUDE.md) - Project overview and guidelines
- [`CONTRIBUTING.md`](../../CONTRIBUTING.md) - Contribution guidelines
- [`README.md`](../../README.md) - User-facing documentation

### Code References
- `src/database/database.py` - Database infrastructure
- `src/services/` - Existing service patterns
- `src/api/routers/` - API routing examples
- `src/utils/config.py` - Configuration management

---

## 💡 Open Questions & Decisions Needed

### Technical
- [ ] Should we cache aggregated stats in `usage_aggregates` table?
- [ ] Event retention: Keep forever or auto-delete old events?
- [ ] Submission retry: How many attempts? Exponential backoff?

### Privacy
- [ ] Should installation_id rotate periodically (e.g., yearly)?
- [ ] Allow users to view aggregated stats from all users?
- [ ] Include sanitized stack traces in error reports?

### Product
- [ ] What's our target opt-in rate? (30%? 50%?)
- [ ] Should we incentivize opt-in? (if so, how?)
- [ ] Public stats dashboard for community?

---

## 📞 Contacts & Resources

**For Questions:**
- **Technical:** Review [Technical Spec](./usage-statistics-technical-spec.md)
- **Privacy:** Review [Privacy Policy](./usage-statistics-privacy.md)
- **Planning:** Review [Roadmap](./usage-statistics-roadmap.md)
- **General:** Review [Master Plan](./usage-statistics-plan.md)

**GitHub:**
- Issues: https://github.com/schmacka/printernizer/issues
- Discussions: https://github.com/schmacka/printernizer/discussions
- Label: `usage-statistics` (for related issues/PRs)

---

## 🔄 Version History

| Version | Date | Changes | Documents Updated |
|---------|------|---------|-------------------|
| 1.0 | 2025-11-20 | Initial planning complete | All 4 docs created |

---

## ✅ Next Steps

1. **Review:** All planning documents with team
2. **Approve:** Architecture and privacy approach
3. **Prioritize:** Phase 1 in next sprint
4. **Assign:** Tasks from roadmap to team members
5. **Start:** Task 1.1 - Database migration

---

**Ready to start implementation? Begin with [Task 1.1 in the Roadmap](./usage-statistics-roadmap.md#11-database-schema--migration)**
