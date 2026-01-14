# Usage Statistics - Implementation Roadmap

**Version:** 1.0 (Draft)
**Last Updated:** 2025-11-20
**Status:** Planning

## Overview

This roadmap outlines the step-by-step implementation of privacy-first usage statistics for Printernizer. Work is organized into phases with clear deliverables and success criteria.

---

## Phase 1: Local Collection & UI (MVP)

**Goal:** Enable local statistics collection with full transparency and user control

**Timeline:** 2-3 weeks (Sprint 1-2)

**Prerequisites:**
- ✅ Existing SQLite database infrastructure
- ✅ FastAPI backend
- ✅ Frontend UI framework

### Tasks

#### 1.1 Database Schema & Migration
- [ ] Create migration: `00XX_add_usage_statistics.py`
- [ ] Define `usage_events` table
- [ ] Define `usage_settings` table
- [ ] Add indexes for performance
- [ ] Test migration up/down
- [ ] Document schema

**Deliverable:** Migration file that can be applied to existing databases

**Estimated Time:** 2 days

---

#### 1.2 Data Models (Pydantic)
- [ ] Create `src/models/usage_statistics.py`
- [ ] Define `UsageEvent` model
- [ ] Define `AggregatedStats` model
- [ ] Define sub-models (InstallationInfo, PrinterFleetStats, etc.)
- [ ] Add validation rules
- [ ] Write model tests

**Deliverable:** Complete Pydantic models with validation

**Estimated Time:** 2 days

---

#### 1.3 Repository Layer
- [ ] Create `src/database/repositories/usage_statistics_repository.py`
- [ ] Implement `insert_event()`
- [ ] Implement `get_events(filters)`
- [ ] Implement `get_setting()` / `set_setting()`
- [ ] Implement `mark_events_submitted()`
- [ ] Implement `delete_all_events()`
- [ ] Write repository tests

**Deliverable:** Fully tested repository with CRUD operations

**Estimated Time:** 3 days

---

#### 1.4 Service Layer
- [ ] Create `src/services/usage_statistics_service.py`
- [ ] Implement `record_event()`
- [ ] Implement `is_opted_in()` / `opt_in()` / `opt_out()`
- [ ] Implement `aggregate_stats()` (basic version)
- [ ] Implement `get_local_stats()`
- [ ] Implement `export_stats()`
- [ ] Implement `delete_all_stats()`
- [ ] Write service tests
- [ ] Add comprehensive logging

**Deliverable:** Complete service layer with error handling

**Estimated Time:** 4 days

---

#### 1.5 API Endpoints
- [ ] Create `src/api/routers/usage_statistics.py`
- [ ] Implement `GET /api/v1/usage-stats/local`
- [ ] Implement `POST /api/v1/usage-stats/opt-in`
- [ ] Implement `POST /api/v1/usage-stats/opt-out`
- [ ] Implement `GET /api/v1/usage-stats/export`
- [ ] Implement `DELETE /api/v1/usage-stats/delete-all`
- [ ] Add OpenAPI documentation
- [ ] Write API tests

**Deliverable:** RESTful API with full test coverage

**Estimated Time:** 3 days

---

#### 1.6 Frontend - Settings UI
- [ ] Create privacy settings page
- [ ] Add opt-in/opt-out toggle
- [ ] Display privacy policy
- [ ] Show "What we collect" section
- [ ] Add "View Privacy Policy" link
- [ ] Style consistently with existing UI
- [ ] Add confirmation dialogs for opt-out/delete

**Deliverable:** Privacy settings page in main settings

**Estimated Time:** 3 days

---

#### 1.7 Frontend - Local Statistics Viewer
- [ ] Create local statistics dashboard
- [ ] Display installation info (anonymized)
- [ ] Show this week's summary
- [ ] Show feature usage stats
- [ ] Add "Export Data" button
- [ ] Add "Delete All Statistics" button
- [ ] Add visualizations (charts/graphs)

**Deliverable:** User-friendly statistics viewer

**Estimated Time:** 4 days

---

#### 1.8 Integration with Existing Services
- [ ] Add stats recording to `main.py` (app_start/shutdown)
- [ ] Integrate with `JobService` (job events)
- [ ] Integrate with `FileService` (file events)
- [ ] Integrate with `PrinterService` (printer events)
- [ ] Add error tracking to exception handlers
- [ ] Ensure non-blocking behavior

**Deliverable:** Statistics collection throughout application

**Estimated Time:** 3 days

---

#### 1.9 Documentation
- [ ] Update `CLAUDE.md` with usage stats info
- [ ] Create user-facing privacy policy
- [ ] Document configuration options
- [ ] Add FAQ section
- [ ] Create developer guide for adding events
- [ ] Update `README.md` with privacy info

**Deliverable:** Complete documentation

**Estimated Time:** 2 days

---

#### 1.10 Testing & Quality Assurance
- [ ] Write unit tests (target: 90% coverage)
- [ ] Write integration tests
- [ ] Test opt-in/opt-out flows
- [ ] Test data export/deletion
- [ ] Test in all deployment modes (HA, Docker, Pi, standalone)
- [ ] Performance testing (ensure < 1% overhead)
- [ ] Privacy audit (verify no PII leaks)

**Deliverable:** Comprehensive test suite, verified privacy

**Estimated Time:** 4 days

---

### Phase 1 Success Criteria

- ✅ Statistics collected locally in SQLite
- ✅ User can opt-in/opt-out via UI
- ✅ User can view all collected data
- ✅ User can export data as JSON
- ✅ User can delete all statistics
- ✅ No performance degradation (< 1% overhead)
- ✅ No PII collected (verified by tests)
- ✅ Works in all deployment modes
- ✅ 90%+ test coverage

**Phase 1 Total Estimated Time:** ~3 weeks (26 days)

---

## Phase 2: Aggregation Service

**Goal:** Build backend service to receive and store aggregated statistics

**Timeline:** 2-3 weeks (Sprint 3-4)

**Prerequisites:**
- ✅ Phase 1 complete
- ✅ SQL Server available
- ✅ Domain for aggregation service (e.g., stats.printernizer.com)
- ✅ SSL certificate

### Tasks

#### 2.1 Aggregation Service Setup
- [ ] Create new FastAPI application for aggregation service
- [ ] Set up project structure
- [ ] Configure SQL Server connection
- [ ] Set up logging and monitoring
- [ ] Configure deployment (Docker)

**Deliverable:** Basic aggregation service skeleton

**Estimated Time:** 2 days

---

#### 2.2 Database Schema (SQL Server)
- [ ] Design `installations` table
- [ ] Design `daily_stats` table
- [ ] Design `events_summary` table
- [ ] Create migration scripts
- [ ] Add indexes and constraints
- [ ] Set up data retention policies (2 years)

**Deliverable:** SQL Server schema

**Estimated Time:** 2 days

---

#### 2.3 Submission Endpoint
- [ ] Implement `POST /submit` endpoint
- [ ] Add request validation (Pydantic)
- [ ] Add rate limiting (1 req/hour per installation)
- [ ] Add authentication (API key or signed JWT)
- [ ] Implement data storage
- [ ] Add error handling
- [ ] Write endpoint tests

**Deliverable:** Secure submission endpoint

**Estimated Time:** 4 days

---

#### 2.4 Client-Side Submission Logic
- [ ] Update `UsageStatisticsService.submit_stats()`
- [ ] Add retry logic with exponential backoff
- [ ] Add submission scheduling (weekly)
- [ ] Handle network errors gracefully
- [ ] Add submission status tracking
- [ ] Test submission flow end-to-end

**Deliverable:** Reliable client-side submission

**Estimated Time:** 3 days

---

#### 2.5 Background Tasks
- [ ] Create periodic submission scheduler
- [ ] Add submission at app startup (if > 7 days)
- [ ] Add submission on opt-in (historical data)
- [ ] Ensure submissions don't block app
- [ ] Add task monitoring and logging

**Deliverable:** Automated background submission

**Estimated Time:** 2 days

---

#### 2.6 Security & Privacy
- [ ] Implement HTTPS-only
- [ ] Add request signing/verification
- [ ] Rate limiting per installation_id
- [ ] IP address handling (rate limit only, don't store)
- [ ] Input sanitization and validation
- [ ] Security audit

**Deliverable:** Secure, privacy-preserving service

**Estimated Time:** 3 days

---

#### 2.7 Monitoring & Alerting
- [ ] Add Prometheus metrics
- [ ] Set up Grafana dashboard
- [ ] Configure alerts (high error rate, etc.)
- [ ] Add health check endpoint
- [ ] Set up log aggregation

**Deliverable:** Observable aggregation service

**Estimated Time:** 2 days

---

#### 2.8 Deployment
- [ ] Deploy to production environment
- [ ] Set up CI/CD pipeline
- [ ] Configure SSL certificate
- [ ] Set up database backups
- [ ] Test from real Printernizer instances
- [ ] Document deployment process

**Deliverable:** Production-ready aggregation service

**Estimated Time:** 3 days

---

### Phase 2 Success Criteria

- ✅ Aggregation service running in production
- ✅ Statistics submitted weekly from clients
- ✅ Rate limiting prevents abuse
- ✅ Data stored securely in SQL Server
- ✅ No PII stored on server
- ✅ Monitoring and alerting in place
- ✅ 99.9% uptime

**Phase 2 Total Estimated Time:** ~3 weeks (21 days)

---

## Phase 3: Analytics Dashboard

**Goal:** Visualize collected statistics for development insights

**Timeline:** 2 weeks (Sprint 5-6)

**Status:** 🚧 IN PROGRESS (Started 2026-01-14)

**Prerequisites:**
- ✅ Phase 2 complete
- ✅ Sufficient data collected (at least 1 month)

### Tasks

#### 3.1 Dashboard Setup
- [x] Choose dashboard tool ~~(Grafana, Metabase, or Superset)~~ → Built-in dashboard in Printernizer
- [x] Set up dashboard service (AdminStatisticsManager in frontend)
- [x] Connect to aggregation service (via API key authentication)
- [x] Create basic layout (Settings > Privacy tab)
- [x] Set up user authentication (API key stored in localStorage)

**Deliverable:** Dashboard infrastructure ✅ COMPLETE

**Completed:** 2026-01-14

---

#### 3.2 Key Metrics Visualization
- [x] Total installations over time (line chart with trend data)
- [x] Active installations (7-day, 30-day) (overview cards)
- [x] Deployment mode distribution (doughnut chart)
- [x] Version adoption rate (horizontal bar chart, top 5)
- [x] Printer type distribution (included in /stats/printers endpoint)
- [ ] Feature usage rates

**Deliverable:** Core metrics dashboards ✅ MOSTLY COMPLETE

**Completed:** 2026-01-14

---

#### 3.3 Trend Analysis
- [x] Week-over-week growth (growth percentage card)
- [ ] Version migration patterns
- [ ] Feature adoption trends
- [ ] Error rate trends
- [x] Geographic distribution (horizontal bar chart, top 10 countries)

**Deliverable:** Trend analysis dashboards 🚧 PARTIAL

---

#### 3.4 Anomaly Detection
- [ ] Set up alerts for unusual patterns
- [ ] Error spike detection
- [ ] Sudden drop in active users
- [ ] Abnormal usage patterns

**Deliverable:** Anomaly detection and alerting

**Estimated Time:** 2 days

---

#### 3.5 Reporting
- [ ] Weekly summary email
- [ ] Monthly report generation
- [ ] Export capabilities
- [ ] Share dashboards with team

**Deliverable:** Automated reporting

**Estimated Time:** 2 days

---

### Phase 3 Implementation Notes (2026-01-14)

**Architecture Decision:** Built-in dashboard instead of external tool (Grafana/Metabase)
- Simpler deployment - no additional infrastructure required
- Integrated into existing Settings UI
- Uses Chart.js for visualization (CDN loaded)
- API key authentication for aggregation service access

**Files Created:**
- `services/aggregation/analytics.py` - AnalyticsService with SQL queries
- `frontend/js/admin-statistics.js` - AdminStatisticsManager class
- `frontend/css/admin-statistics.css` - Dashboard styling

**API Endpoints Added:**
- `GET /stats/overview` - Combined dashboard data
- `GET /stats/installations` - Installation metrics with trend
- `GET /stats/deployment-modes` - Deployment distribution
- `GET /stats/versions` - Version adoption rates
- `GET /stats/geography` - Geographic distribution
- `GET /stats/printers` - Printer statistics

---

### Phase 3 Success Criteria

- ✅ Dashboard accessible to team
- ✅ Key metrics visualized
- 🚧 Trends identified (partial)
- [ ] Anomalies detected automatically
- [ ] Weekly reports generated

**Phase 3 Total Estimated Time:** ~2 weeks (12 days)

---

## Phase 4: Feedback Loop & Iteration

**Goal:** Use insights to improve Printernizer

**Timeline:** Ongoing

### Tasks

#### 4.1 Feature Prioritization
- [ ] Analyze feature usage rates
- [ ] Identify underused features (improve or deprecate)
- [ ] Identify most-requested features (from errors/patterns)
- [ ] Update product roadmap based on data

**Deliverable:** Data-driven product roadmap

---

#### 4.2 Error Pattern Analysis
- [ ] Identify top error types
- [ ] Correlate errors with deployment modes/versions
- [ ] Prioritize bug fixes based on impact
- [ ] Track error rate reduction over time

**Deliverable:** Improved stability and reliability

---

#### 4.3 Deployment Optimization
- [ ] Optimize for most common deployment modes
- [ ] Improve documentation for popular setups
- [ ] Address deployment-specific issues
- [ ] Streamline installation for popular platforms

**Deliverable:** Better deployment experience

---

#### 4.4 User Experience Improvements
- [ ] Analyze feature discovery (which features are found?)
- [ ] Identify friction points (errors after specific actions)
- [ ] A/B test improvements (if implementing feature flags)
- [ ] Iterate on UI based on usage patterns

**Deliverable:** Enhanced user experience

---

#### 4.5 Community Engagement
- [ ] Share anonymized insights with community (if appropriate)
- [ ] Celebrate milestones (10,000 jobs completed, etc.)
- [ ] Use data to guide feature announcements
- [ ] Build trust through transparency

**Deliverable:** Stronger community engagement

---

### Phase 4 Success Criteria

- ✅ Feature roadmap informed by usage data
- ✅ Error rates decreasing over time
- ✅ Deployment experience improved
- ✅ User experience enhanced
- ✅ Community trusts privacy-first approach

---

## Risk Management

### Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Statistics break main app | High | Low | Non-blocking design, fail silently |
| Database migration fails | Medium | Low | Thorough testing, rollback plan |
| Performance degradation | Medium | Low | Performance tests, async operations |
| SQL Server unavailable | Medium | Medium | Client-side queueing, retry logic |

### Privacy Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| PII leakage | High | Low | Privacy tests, code review |
| User distrust | High | Low | Transparency, clear communication |
| GDPR non-compliance | High | Low | Legal review, compliance checklist |

### Adoption Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Low opt-in rate | Medium | Medium | Clear value proposition, transparency |
| User backlash | Medium | Low | Opt-in only, full transparency |
| Feature creep | Low | Medium | Stick to plan, avoid scope expansion |

---

## Milestones & Checkpoints

### Milestone 1: Phase 1 Complete ✅
- **Date:** 3 weeks from start
- **Deliverable:** Local collection working, UI complete, tested in all deployment modes
- **Decision Point:** Proceed to Phase 2 or iterate?

### Milestone 2: Phase 2 Complete ✅
- **Date:** 6 weeks from start
- **Deliverable:** Aggregation service live, clients submitting successfully
- **Decision Point:** Sufficient data quality to proceed to Phase 3?

### Milestone 3: Phase 3 Complete ✅
- **Date:** 8 weeks from start
- **Deliverable:** Dashboard live, first insights generated
- **Decision Point:** Are insights actionable? What improvements to prioritize?

### Milestone 4: First Improvement Shipped 🚀
- **Date:** 10 weeks from start
- **Deliverable:** Feature/fix shipped based on usage data
- **Success Metric:** Feedback loop validated

---

## Dependencies & Resources

### Team Resources
- **Backend Developer:** Phase 1 (service/API), Phase 2 (aggregation service)
- **Frontend Developer:** Phase 1 (UI)
- **DevOps:** Phase 2 (deployment), Phase 3 (dashboard setup)
- **QA:** Phase 1 (testing), ongoing
- **Product/PM:** All phases (prioritization, communication)

### Infrastructure
- **Phase 1:** None (uses existing SQLite)
- **Phase 2:** SQL Server, domain/SSL, compute for aggregation service
- **Phase 3:** Dashboard hosting (can be same as aggregation service)

### External Dependencies
- **None** (all built with existing stack)

---

## Communication Plan

### Internal (Team)
- **Weekly standups:** Progress updates during implementation
- **Sprint demos:** Show working features at end of each phase
- **Data reviews:** Monthly reviews of insights (after Phase 3)

### External (Users/Community)
- **Announcement blog post:** Before Phase 1 release (explain privacy approach)
- **Release notes:** Include usage stats info in changelog
- **Privacy policy:** Publish before opt-in available
- **FAQ:** Address common concerns
- **Feedback channels:** GitHub Discussions for questions

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-20 | Initial roadmap created |

---

**Next Actions:**
1. Review and approve roadmap
2. Break down Phase 1 into sprint-sized tasks
3. Assign tasks to team members
4. Begin implementation with 1.1 (Database Schema)
