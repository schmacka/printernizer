# Printer Autodiscovery Implementation Plan

**Status**: Planning Phase
**Branch**: `claude/printer-autodiscovery-011CUVsgos1zvF1ACLMEhUs4`
**Created**: 2025-10-26
**Target**: Printernizer v2.1.0+

## Executive Summary

Implement network-based autodiscovery for Bambu Lab and Prusa 3D printers to simplify initial setup and ongoing printer management. The system will automatically detect printers on the local network, identify their type, and pre-fill configuration forms while maintaining security through manual credential entry.

## Current State Analysis

### Existing Configuration Methods
1. **JSON Configuration File** (`/config/printers.json`)
   - Manual file editing required
   - Contains IP, credentials, printer type
   - Auto-created with examples if missing

2. **Environment Variables**
   - Format: `PRINTERNIZER_PRINTER_{ID}_{FIELD}`
   - Suitable for Docker/HA deployment
   - No discovery capability

3. **Web UI Form** (`frontend/js/printer-form.js`)
   - Manual entry of all fields
   - Type-specific field validation
   - No autodiscovery button

### Pain Points
- Users must manually determine printer IP addresses
- No validation of network connectivity before saving
- Risk of typos in IP addresses and credentials
- No way to detect new printers on network
- Difficult to troubleshoot connection issues

## Proposed Solution: Hybrid Autodiscovery

### Discovery Capabilities

#### Automatic Detection
- **Network Scanning**: Probe local subnet for printers
- **mDNS/Bonjour**: Service discovery protocol
- **Type Identification**: Automatically detect Bambu Lab vs Prusa
- **IP Address Extraction**: Automatically capture network location
- **Model Detection**: Identify specific printer models where possible

#### Manual Security Layer
- **Credentials Required**: User must provide access codes/API keys
- **Validation Before Save**: Test connection before adding to config
- **Secure Storage**: Existing credential storage unchanged
- **No Automatic Credentials**: Never attempt to guess/brute-force

### User Experience Flow

```
1. User clicks "Discover Printers" button
2. System scans network (5-30 seconds)
3. Display list of discovered printers with:
   - Detected IP address
   - Printer type (Bambu Lab / Prusa)
   - Model name (if available)
   - Current status (configured / new / offline)
4. User selects printer from list
5. Form pre-filled with discovered data
6. User enters required credentials
7. System validates connection
8. Printer added to configuration
```

## Technical Implementation

### Discovery Methods by Manufacturer

#### Bambu Lab Discovery

**Primary Method: mDNS/Bonjour**
- Service type: `_device-info._tcp.local.`
- Port: 8883 (MQTT over TLS)
- Instance name format: `{printer_model}._{serial_number}`
- TXT records may contain: model, firmware version, serial

**Secondary Method: Network Scanning**
- Scan local subnet (192.168.x.x/24, 10.x.x.x/24)
- Probe TCP port 8883 (MQTT)
- Send MQTT CONNECT probe
- Parse CONNACK response for device info

**Tertiary Method: Broadcast Discovery**
- UDP broadcast on port 2021 (if supported)
- Bambu Studio uses this for discovery
- May provide serial number and model

**Still Required from User:**
- Access Code (8 characters from printer screen)
- Serial Number (if not auto-detected)

#### Prusa Discovery

**Primary Method: mDNS/Bonjour**
- Service type: `_http._tcp.local.` or `_prusalink._tcp.local.`
- Port: 80 or 8080
- Instance name: Printer hostname
- TXT records: version, api_version, model

**Secondary Method: HTTP API Scanning**
- Scan local subnet for HTTP servers
- Probe: `http://{ip}/api/version` (no auth required)
- Response contains: `"api": "2.0.0", "server": "PrusaLink"`
- Identifies Prusa printers specifically

**Tertiary Method: Port Scanning**
- Look for port 80/8080 responses
- Check HTTP headers for PrusaLink signature
- Parse HTML for PrusaLink branding

**Still Required from User:**
- API Key (generated in PrusaLink settings)

### Architecture Components

#### 1. Discovery Service (New)
**File**: `printernizer/src/services/printer_discovery_service.py`

```python
class PrinterDiscoveryService:
    """
    Handles network-based printer discovery
    """

    async def discover_printers() -> List[DiscoveredPrinter]
    async def scan_network(subnet: str) -> List[DiscoveredPrinter]
    async def scan_mdns() -> List[DiscoveredPrinter]
    async def validate_credentials(printer: DiscoveredPrinter, credentials: dict) -> bool
    async def get_discovery_status() -> DiscoveryStatus
    def start_discovery_task() -> str  # Returns task_id
    def cancel_discovery_task(task_id: str)
```

**Discovery Methods:**
- `_discover_bambu_mdns()` - mDNS scan for Bambu Lab
- `_discover_prusa_mdns()` - mDNS scan for Prusa
- `_scan_subnet_bambu()` - Network probe for Bambu MQTT
- `_scan_subnet_prusa()` - Network probe for PrusaLink
- `_validate_bambu_connection()` - Test MQTT with credentials
- `_validate_prusa_connection()` - Test HTTP API with key

#### 2. Discovery Models (New)
**File**: `printernizer/src/models/printer_discovery.py`

```python
@dataclass
class DiscoveredPrinter:
    ip_address: str
    printer_type: PrinterType
    model_name: Optional[str]
    serial_number: Optional[str]
    hostname: Optional[str]
    discovery_method: str  # "mdns", "http_scan", "mqtt_scan"
    discovered_at: datetime
    is_configured: bool  # Already in config?

@dataclass
class DiscoveryStatus:
    task_id: str
    status: str  # "running", "completed", "failed"
    progress: int  # 0-100
    found_count: int
    started_at: datetime
    completed_at: Optional[datetime]
```

#### 3. Database Schema Changes
**File**: `printernizer/src/database/database.py`

**Add columns to `printers` table:**
```sql
ALTER TABLE printers ADD COLUMN discovery_method TEXT DEFAULT 'manual';
ALTER TABLE printers ADD COLUMN discovered_at TIMESTAMP;
ALTER TABLE printers ADD COLUMN last_discovery_check TIMESTAMP;
ALTER TABLE printers ADD COLUMN credential_validated_at TIMESTAMP;
```

**New table: `discovered_printers` (temporary storage)**
```sql
CREATE TABLE discovered_printers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,
    printer_type TEXT NOT NULL,
    model_name TEXT,
    serial_number TEXT,
    hostname TEXT,
    discovery_method TEXT NOT NULL,
    discovered_at TIMESTAMP NOT NULL,
    is_configured BOOLEAN DEFAULT 0,
    expires_at TIMESTAMP NOT NULL,
    UNIQUE(ip_address)
);
```

#### 4. API Router Changes
**File**: `printernizer/src/api/routers/printers.py`

**New endpoints:**
```python
POST   /api/printers/discover             # Start discovery scan
GET    /api/printers/discover/{task_id}   # Get discovery status
GET    /api/printers/discovered           # List discovered printers
POST   /api/printers/validate             # Validate credentials
DELETE /api/printers/discovered/{ip}      # Remove from discovery cache
POST   /api/printers/from-discovered      # Convert discovered to configured
```

**Endpoint Details:**

```python
@router.post("/discover")
async def start_discovery(
    subnet: Optional[str] = None,
    methods: List[str] = ["mdns", "network_scan"]
) -> DiscoveryTaskResponse

@router.get("/discovered")
async def list_discovered(
    include_configured: bool = False,
    type_filter: Optional[PrinterType] = None
) -> List[DiscoveredPrinter]

@router.post("/validate")
async def validate_printer_credentials(
    validation_request: PrinterValidationRequest
) -> ValidationResult

@router.post("/from-discovered")
async def add_from_discovered(
    discovered_printer: DiscoveredPrinter,
    credentials: PrinterCredentials
) -> Printer
```

#### 5. Frontend Components

**New File**: `frontend/js/printer-discovery.js`

Features:
- Discovery initiation button
- Progress indicator with status updates
- Real-time discovered printer list
- Quick-add functionality
- Credential input modals
- Validation status indicators

**UI Components:**
```javascript
class PrinterDiscovery {
    startDiscovery()        // Initiate scan
    pollDiscoveryStatus()   // Check progress
    renderDiscoveredList()  // Display results
    showCredentialModal()   // Prompt for credentials
    validateAndAdd()        // Test + add printer
    refreshDiscovery()      // Re-scan network
}
```

**Modify File**: `frontend/js/printer-form.js`

Add features:
- "Auto-fill from discovered" dropdown
- Real-time credential validation
- Connection test button
- IP address suggestions based on network

**Modify File**: `frontend/html/settings.html`

Add discovery section:
```html
<div class="discovery-section">
    <button id="discover-btn">Scan Network for Printers</button>
    <div id="discovery-status" class="hidden">
        <progress id="discovery-progress"></progress>
        <span id="discovery-text"></span>
    </div>
    <div id="discovered-list"></div>
</div>
```

### Configuration Service Integration

**File**: `printernizer/src/services/config_service.py`

**New methods:**
```python
def get_discovered_printers() -> List[DiscoveredPrinter]
def add_printer_from_discovery(discovered: DiscoveredPrinter, credentials: dict) -> Printer
def mark_as_configured(ip_address: str)
def cleanup_old_discoveries(max_age_hours: int = 24)
```

**Integration points:**
- Link discovery service to config management
- Validate discovered printers before adding
- Track which discovered printers are already configured
- Periodic cleanup of old discovery cache

### Printer Service Integration

**File**: `printernizer/src/services/printer_service.py`

**Enhanced methods:**
```python
async def validate_printer_connection(printer_config: PrinterConfig) -> ValidationResult
async def test_credentials(ip: str, type: PrinterType, credentials: dict) -> bool
def get_printer_by_ip(ip_address: str) -> Optional[Printer]
```

**Background tasks:**
- Periodic rediscovery (optional, configurable)
- Automatic credential validation on startup
- Network change detection (if IP changes)

## Implementation Dependencies

### Python Libraries

**Required (New):**
```
zeroconf>=0.131.0        # mDNS/Bonjour discovery
aiomdns>=0.9.2           # Async mDNS (alternative)
netifaces>=0.11.0        # Network interface detection
ipaddress                # Built-in (subnet calculations)
```

**Already Available:**
```
aiohttp                  # HTTP scanning (Prusa)
paho-mqtt                # MQTT probing (Bambu Lab)
bambulabs-api            # Bambu Lab connection testing
asyncio                  # Async task management
```

**Update**: `requirements.txt`
```txt
zeroconf>=0.131.0
netifaces>=0.11.0
```

### Network Requirements

**Permissions:**
- mDNS multicast group (224.0.0.251)
- UDP port 5353 (mDNS)
- Subnet scanning capability
- Raw socket access (may require elevated privileges)

**Deployment Considerations:**

**Standalone Mode:**
- Full network access to local subnet
- No restrictions

**Docker Mode:**
- Network mode: `host` (recommended for discovery)
- Or: Bridge mode with subnet access
- Security consideration: mDNS across Docker networks

**Home Assistant Add-on Mode:**
- HA network segment access required
- Ingress compatibility (no impact on discovery)
- May need `host_network: true` in config.yaml

## Implementation Phases

### Phase 1: Backend Discovery Service (Week 1)
**Files to Create:**
- `printernizer/src/services/printer_discovery_service.py`
- `printernizer/src/models/printer_discovery.py`

**Tasks:**
1. Implement mDNS discovery for both printer types
2. Implement network scanning fallback
3. Add credential validation methods
4. Create discovery task management (async)
5. Add unit tests for discovery methods

**Success Criteria:**
- Can discover Bambu Lab printers via mDNS
- Can discover Prusa printers via HTTP API
- Can validate credentials before saving
- Returns structured discovery results

### Phase 2: Database & Configuration (Week 1-2)
**Files to Modify:**
- `printernizer/src/database/database.py`
- `printernizer/src/services/config_service.py`

**Tasks:**
1. Add database migrations for new columns
2. Create `discovered_printers` table
3. Implement discovery cache management
4. Add configuration integration methods
5. Update existing printer models

**Success Criteria:**
- Database schema supports discovery tracking
- Can cache discovered printers
- Can convert discovered to configured
- Backward compatible with existing configs

### Phase 3: API Endpoints (Week 2)
**Files to Modify:**
- `printernizer/src/api/routers/printers.py`

**Tasks:**
1. Add discovery initiation endpoint
2. Add discovery status polling endpoint
3. Add discovered printers list endpoint
4. Add credential validation endpoint
5. Add conversion endpoint (discovered → configured)
6. Update OpenAPI documentation

**Success Criteria:**
- All endpoints documented and tested
- Proper error handling
- Async task management working
- Returns appropriate status codes

### Phase 4: Frontend UI (Week 2-3)
**Files to Create:**
- `frontend/js/printer-discovery.js`

**Files to Modify:**
- `frontend/html/settings.html`
- `frontend/js/printer-form.js`
- `frontend/css/styles.css`

**Tasks:**
1. Create discovery UI component
2. Add "Scan Network" button to settings
3. Implement progress tracking UI
4. Create discovered printer list view
5. Add credential input modals
6. Implement auto-fill in printer form
7. Add real-time validation indicators

**Success Criteria:**
- User can click "Scan Network"
- Progress shown during discovery
- Discovered printers displayed in list
- Can add printer with one-click + credentials
- Form validates before saving

### Phase 5: Testing & Refinement (Week 3)
**Tasks:**
1. Integration testing with real printers
2. Network scanning performance optimization
3. Error handling for edge cases
4. UI/UX refinement
5. Documentation updates

**Test Scenarios:**
- No printers on network
- Multiple printers of same type
- Mixed Bambu Lab + Prusa environment
- Invalid credentials entered
- Network timeout handling
- mDNS not available (fallback to scanning)

### Phase 6: Deployment & Documentation (Week 3-4)
**Files to Update:**
- `README.md` - Add autodiscovery section
- `CLAUDE.md` - Update features list
- `CHANGELOG.md` - Version bump and features
- `docker/README.md` - Docker network requirements
- `printernizer/DOCS.md` - HA add-on discovery guide

**Tasks:**
1. Update all deployment guides
2. Add network requirements documentation
3. Create troubleshooting guide
4. Update screenshots/demos
5. Bump version to 2.1.0
6. Test all three deployment modes

## Security Considerations

### What's Secured
1. **No Credential Storage in Discovery Cache**
   - Discovered printers don't store credentials
   - Credentials only entered during add/validation

2. **Validation Required**
   - All credentials tested before saving
   - Failed validation prevents addition

3. **Network Isolation**
   - Discovery limited to local subnet
   - No internet-based discovery

4. **Existing Security Unchanged**
   - Credential storage uses existing methods
   - No new attack surface for credential theft

### Potential Risks
1. **Network Reconnaissance**
   - Discovery reveals printer IPs to local network users
   - Mitigation: Already visible via mDNS anyway

2. **Denial of Service**
   - Rapid discovery scans could impact network
   - Mitigation: Rate limiting, configurable intervals

3. **False Positives**
   - Non-printer devices may respond to probes
   - Mitigation: Strict validation of responses

## Configuration Options

### New Settings (Optional)

Add to configuration schema:
```json
{
  "discovery": {
    "enabled": true,
    "auto_discover_on_startup": false,
    "discovery_interval_minutes": 60,
    "discovery_methods": ["mdns", "network_scan"],
    "network_subnets": ["auto"],
    "discovery_timeout_seconds": 30
  }
}
```

### Environment Variables
```bash
PRINTERNIZER_DISCOVERY_ENABLED=true
PRINTERNIZER_AUTO_DISCOVERY=false
PRINTERNIZER_DISCOVERY_INTERVAL=60
```

## Performance Considerations

### Discovery Speed
- **mDNS**: 2-5 seconds (fast)
- **Network Scan**: 15-30 seconds (slower, comprehensive)
- **Combined**: Run in parallel, return results as found

### Optimization Strategies
1. **Async Scanning**: Use asyncio for concurrent probes
2. **Smart Subnet Detection**: Only scan likely subnets
3. **Caching**: Store results for 5-60 minutes
4. **Progressive Results**: Return printers as found (streaming)
5. **Background Tasks**: Don't block UI during discovery

### Resource Usage
- **CPU**: Minimal (async I/O bound)
- **Memory**: ~1-5MB for discovery cache
- **Network**: Burst during scan, idle otherwise

## Success Metrics

### Functional Goals
- [ ] Discovers 100% of Bambu Lab printers on network
- [ ] Discovers 100% of Prusa printers on network
- [ ] Discovery completes in < 30 seconds
- [ ] Zero false positives
- [ ] Credential validation 100% accurate

### User Experience Goals
- [ ] Setup time reduced by 80%
- [ ] Zero manual IP entry required
- [ ] Connection errors reduced by 90%
- [ ] One-click printer addition working

### Technical Goals
- [ ] No breaking changes to existing configs
- [ ] Works in all three deployment modes
- [ ] Backward compatible with manual config
- [ ] Comprehensive error handling

## Rollback Plan

If issues arise:
1. **Feature Flag**: Add `DISCOVERY_ENABLED=false` to disable
2. **Manual Override**: Existing config methods still work
3. **Database Rollback**: Discovery tables are separate
4. **UI Fallback**: Manual form still available
5. **Version Rollback**: Previous version fully functional

## Future Enhancements (Post-v2.1.0)

### Phase 2 Features
- **Automatic Rediscovery**: Periodic background scanning
- **IP Change Detection**: Alert if printer IP changes
- **QR Code Setup**: Scan QR code with credentials
- **Printer Grouping**: Auto-organize by location/type
- **Network Topology Map**: Visual network view

### Advanced Features
- **Cloud Discovery**: Bambu Lab cloud integration
- **OAuth Flow**: Simplified credential management
- **Bluetooth Discovery**: For printers with BLE
- **Printer Sharing**: Multi-user setups
- **Discovery Plugins**: Extensible for other brands

## Open Questions

1. **mDNS Library Choice**: `zeroconf` vs `aiomdns`?
   - Recommendation: `zeroconf` (more mature, better maintained)

2. **Network Scanning Ethics**: Is subnet scanning acceptable?
   - Recommendation: Yes, with user consent and rate limiting

3. **Credential Pre-fill**: Should we support credential import files?
   - Recommendation: Phase 2 feature, not MVP

4. **Home Assistant Integration**: Should discovery trigger HA automations?
   - Recommendation: Yes, emit events for HA automation use

5. **Docker Networking**: Require host mode or bridge?
   - Recommendation: Document both, recommend host mode

## References

### Bambu Lab Resources
- Bambu Lab MQTT Protocol: https://github.com/bambulab/BambuStudio/wiki
- bambulabs-api Library: https://pypi.org/project/bambulabs-api/
- Community Discovery Scripts: https://github.com/topics/bambu-lab

### Prusa Resources
- PrusaLink API Docs: https://help.prusa3d.com/article/prusalink-api_404363
- mDNS Service Types: http://www.dns-sd.org/ServiceTypes.html
- PrusaConnect Protocol: https://connect.prusa3d.com/docs

### Network Discovery
- Zeroconf Python: https://python-zeroconf.readthedocs.io/
- mDNS RFC 6762: https://tools.ietf.org/html/rfc6762
- DNS-SD RFC 6763: https://tools.ietf.org/html/rfc6763

---

## Next Steps

To begin implementation:

1. **Review this plan** with stakeholders
2. **Test network discovery** manually with printers
3. **Choose mDNS library** and test compatibility
4. **Create feature branch** (already done: `claude/printer-autodiscovery-011CUVsgos1zvF1ACLMEhUs4`)
5. **Begin Phase 1** implementation

**Estimated Total Time**: 3-4 weeks
**Priority**: High (major UX improvement)
**Risk Level**: Low (non-breaking addition)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-26
**Next Review**: Start of Phase 1 implementation
