# Enhanced 3D Model Metadata Display

**Feature ID:** METADATA-001  
**Priority:** High  
**Status:** Planned  
**Version Target:** v1.2.0  
**Estimated Effort:** Medium (2-3 sprints)

## Overview

Enhance Printernizer's file information display by extracting and presenting comprehensive metadata from 3D model files (3MF, G-code, STL). This feature will provide users with detailed information about print requirements, costs, compatibility, and technical specifications before starting a print job.

## Problem Statement

Currently, Printernizer displays limited metadata for 3D files:
- Filename, size, and file type
- Basic layer count and print time (when available)
- Limited filament information

Users need more comprehensive information to make informed decisions about:
- Print cost estimation
- Time planning
- Material requirements
- Printer compatibility
- Quality expectations

## Goals

### Primary Goals
- **Enhanced Decision Making**: Provide comprehensive print information upfront
- **Cost Transparency**: Clear breakdown of material and energy costs
- **Time Management**: Accurate print time estimates with breakdown
- **Resource Planning**: Detailed material requirements and compatibility

### Secondary Goals
- **Quality Prediction**: Indicators for print quality and success probability
- **Optimization Suggestions**: Recommendations for faster/cheaper/higher quality prints
- **Historical Tracking**: Track actual vs estimated values for continuous improvement

## User Stories

### As a Maker
- **US-001**: I want to see the physical dimensions of a model so I can verify it fits my printer bed
- **US-002**: I want to know the total material cost before printing so I can budget appropriately
- **US-003**: I want to see printer compatibility information so I know if I can print this file
- **US-004**: I want detailed layer and quality information so I can assess print difficulty

### As a Service Provider
- **US-005**: I want comprehensive cost breakdowns so I can provide accurate quotes to customers
- **US-006**: I want to see optimal printer selection recommendations for each file
- **US-007**: I want quality predictions so I can set appropriate customer expectations

## Feature Specification

### 1. Model Information Section

#### Physical Properties
- **Dimensions**: Width × Depth × Height (mm)
- **Bounding Box**: Min/Max coordinates
- **Volume**: Model volume in cm³
- **Surface Area**: Total surface area in cm²
- **Object Count**: Number of separate objects/parts
- **Scale Factor**: If model was scaled during slicing

#### Geometric Analysis
- **Complexity Score**: Based on feature density and geometry
- **Overhang Areas**: Percentage and critical angles
- **Bridge Detection**: Number and length of bridges
- **Support Requirements**: Estimated support volume

### 2. Print Settings Section

#### Layer Configuration
- **Layer Height**: Primary layer height in mm
- **First Layer Height**: Initial layer thickness
- **Total Layers**: Complete layer count
- **Variable Layer Heights**: If adaptive layers used

#### Extrusion Settings
- **Nozzle Diameter**: Required nozzle size
- **Line Width**: Extrusion width settings
- **Wall Count**: Number of perimeters
- **Wall Thickness**: Total wall thickness in mm

#### Infill Configuration
- **Infill Density**: Percentage and pattern type
- **Infill Pattern**: Gyroid, cubic, honeycomb, etc.
- **Top/Bottom Layers**: Shell thickness settings
- **Solid Layer Count**: Number of solid top/bottom layers

### 3. Material Requirements Section

#### Filament Usage
- **Total Weight**: Combined weight of all materials (grams)
- **Weight by Color**: Breakdown for multi-color prints
- **Filament Length**: Total length in meters
- **Length by Extruder**: Per-material breakdown

#### Material Properties
- **Material Types**: PLA, PETG, ABS, etc.
- **Material Brands**: Specific filament brands if available
- **Color Information**: Color names/codes
- **Special Properties**: Engineering materials, supports, etc.

#### Cost Analysis
- **Material Cost**: Based on filament prices
- **Waste Material**: Support, brim, purge tower weight
- **Energy Cost**: Estimated electricity consumption
- **Total Cost**: Complete cost breakdown

### 4. Time & Performance Section

#### Time Estimates
- **Print Time**: Primary printing duration
- **Preparation Time**: Heating, calibration, etc.
- **Post-Processing**: Estimated cleanup time
- **Total Time**: Complete job duration

#### Performance Metrics
- **Print Speed**: Average and maximum speeds
- **Acceleration Settings**: Movement acceleration values
- **Temperature Profile**: Nozzle and bed temperature ranges
- **Cooling Settings**: Fan speed and layer time thresholds

### 5. Compatibility Section

#### Printer Requirements
- **Compatible Models**: List of supported printers
- **Bed Size Requirements**: Minimum bed dimensions
- **Build Volume**: Required print volume
- **Special Features**: Heated bed, enclosure, multi-material

#### Technical Requirements
- **Slicer Information**: Software name and version
- **Profile Used**: Print profile/quality setting
- **Firmware Requirements**: Minimum firmware versions
- **Capabilities Needed**: Auto-leveling, filament sensors, etc.

### 6. Quality Indicators Section

#### Printability Assessment
- **Success Probability**: Estimated print success rate
- **Difficulty Level**: Beginner, Intermediate, Advanced
- **Quality Score**: Expected surface finish quality
- **Risk Factors**: Potential failure points identified

#### Optimization Suggestions
- **Speed Optimizations**: Suggestions for faster printing
- **Quality Improvements**: Settings for better results
- **Cost Reductions**: Material or energy saving options
- **Alternative Configurations**: Different printer/material combinations

## Technical Implementation

### Data Sources

#### 3MF Files
- **Model XML**: Physical dimensions, object count, scale
- **Project Settings**: Print configuration and slicer settings
- **Process Settings**: Detailed print parameters
- **Slice Info**: Layer count, prediction data, filament usage
- **Plate JSON**: Bed layout and material assignments

#### G-code Files
- **Header Comments**: Bambu/Prusa slicer metadata
- **Configuration Blocks**: All print settings and parameters
- **Layer Comments**: Progress tracking and validation
- **Filament Tracking**: Usage calculations and estimates

#### STL Files
- **Geometric Analysis**: Calculate dimensions and volume
- **Mesh Analysis**: Surface area, complexity metrics
- **Default Estimates**: Apply standard print settings

### Database Schema Extensions

#### Files Table Additions
```sql
-- Physical Properties
ALTER TABLE files ADD COLUMN model_width DECIMAL(8,3);
ALTER TABLE files ADD COLUMN model_depth DECIMAL(8,3);
ALTER TABLE files ADD COLUMN model_height DECIMAL(8,3);
ALTER TABLE files ADD COLUMN model_volume DECIMAL(10,3);
ALTER TABLE files ADD COLUMN surface_area DECIMAL(10,3);
ALTER TABLE files ADD COLUMN object_count INTEGER DEFAULT 1;

-- Print Settings
ALTER TABLE files ADD COLUMN nozzle_diameter DECIMAL(3,2);
ALTER TABLE files ADD COLUMN wall_count INTEGER;
ALTER TABLE files ADD COLUMN wall_thickness DECIMAL(4,2);
ALTER TABLE files ADD COLUMN infill_pattern VARCHAR(50);
ALTER TABLE files ADD COLUMN first_layer_height DECIMAL(4,3);

-- Material Analysis
ALTER TABLE files ADD COLUMN total_filament_weight DECIMAL(8,3);
ALTER TABLE files ADD COLUMN filament_length DECIMAL(10,2);
ALTER TABLE files ADD COLUMN waste_weight DECIMAL(8,3);
ALTER TABLE files ADD COLUMN energy_estimate DECIMAL(6,3);

-- Quality Metrics
ALTER TABLE files ADD COLUMN complexity_score INTEGER;
ALTER TABLE files ADD COLUMN success_probability DECIMAL(3,2);
ALTER TABLE files ADD COLUMN difficulty_level VARCHAR(20);
ALTER TABLE files ADD COLUMN overhang_percentage DECIMAL(5,2);

-- Compatibility
ALTER TABLE files ADD COLUMN compatible_printers TEXT; -- JSON array
ALTER TABLE files ADD COLUMN slicer_name VARCHAR(100);
ALTER TABLE files ADD COLUMN slicer_version VARCHAR(50);
ALTER TABLE files ADD COLUMN profile_name VARCHAR(100);
```

#### Metadata Table (Flexible Storage)
```sql
CREATE TABLE file_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    key VARCHAR(100) NOT NULL,
    value TEXT,
    data_type VARCHAR(20) DEFAULT 'string',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES files(id),
    UNIQUE(file_id, category, key)
);
```

### Parser Enhancements

#### BambuParser Extensions
```python
class EnhancedBambuParser(BambuParser):
    # Additional metadata patterns
    ADVANCED_PATTERNS = {
        'model_width': re.compile(r'; model_width = ([\d.]+)', re.IGNORECASE),
        'model_depth': re.compile(r'; model_depth = ([\d.]+)', re.IGNORECASE),
        'model_height': re.compile(r'; model_height = ([\d.]+)', re.IGNORECASE),
        'nozzle_diameter': re.compile(r'; nozzle_diameter = ([\d.]+)', re.IGNORECASE),
        'wall_loops': re.compile(r'; wall_loops = (\d+)', re.IGNORECASE),
        'infill_pattern': re.compile(r'; sparse_infill_pattern = (.+)', re.IGNORECASE),
        'compatible_printers': re.compile(r'; compatible_printers = (.+)', re.IGNORECASE),
        'slicer_version': re.compile(r'; (.+) ([\d.]+)', re.IGNORECASE),
    }
    
    def extract_advanced_metadata(self, content: str) -> Dict[str, Any]:
        """Extract comprehensive metadata from file content."""
        # Implementation details...
```

#### 3MF Analysis Engine
```python
class ThreeMFAnalyzer:
    def analyze_plate_json(self, plate_data: dict) -> Dict[str, Any]:
        """Analyze plate JSON for object layout and material usage."""
        
    def calculate_print_costs(self, metadata: dict) -> Dict[str, float]:
        """Calculate comprehensive cost breakdown."""
        
    def assess_print_quality(self, settings: dict) -> Dict[str, Any]:
        """Assess printability and quality predictions."""
```

### API Enhancements

#### New Endpoints
```python
@router.get("/files/{file_id}/metadata/detailed")
async def get_detailed_metadata(file_id: str) -> DetailedMetadataResponse:
    """Get comprehensive metadata for a file."""

@router.get("/files/{file_id}/analysis")
async def get_file_analysis(file_id: str) -> FileAnalysisResponse:
    """Get advanced analysis including recommendations."""

@router.get("/files/{file_id}/compatibility")
async def check_compatibility(file_id: str, printer_id: str = None) -> CompatibilityResponse:
    """Check file compatibility with available printers."""
```

#### Response Models
```python
class DetailedMetadataResponse(BaseModel):
    physical_properties: PhysicalPropertiesResponse
    print_settings: PrintSettingsResponse
    material_requirements: MaterialRequirementsResponse
    time_estimates: TimeEstimatesResponse
    compatibility: CompatibilityResponse
    quality_indicators: QualityIndicatorsResponse

class PhysicalPropertiesResponse(BaseModel):
    dimensions: Tuple[float, float, float]  # width, depth, height
    volume: float
    surface_area: Optional[float]
    object_count: int
    bounding_box: Optional[Dict[str, float]]

# Additional response models...
```

### Frontend Implementation

#### Component Structure
```
components/
├── FileMetadata/
│   ├── MetadataOverview.js          # Main metadata display
│   ├── PhysicalProperties.js        # Dimensions and geometry
│   ├── PrintSettings.js             # Layer and extrusion settings
│   ├── MaterialRequirements.js      # Filament and cost info
│   ├── TimeEstimates.js             # Duration and performance
│   ├── CompatibilityInfo.js         # Printer compatibility
│   ├── QualityIndicators.js         # Quality and recommendations
│   └── MetadataCards.js             # Reusable info cards
```

#### UI Layout
```html
<div class="file-metadata-enhanced">
    <div class="metadata-header">
        <h3>{{filename}}</h3>
        <div class="file-stats-summary">
            <span class="stat">📐 {{dimensions}}</span>
            <span class="stat">⏱️ {{printTime}}</span>
            <span class="stat">🧵 {{weight}}g</span>
            <span class="stat">💰 {{cost}}</span>
        </div>
    </div>
    
    <div class="metadata-sections">
        <div class="section-grid">
            <PhysicalProperties />
            <PrintSettings />
            <MaterialRequirements />
            <TimeEstimates />
            <CompatibilityInfo />
            <QualityIndicators />
        </div>
    </div>
</div>
```

## Implementation Phases

### Phase 1: Core Metadata Extraction (Sprint 1)
- **Backend**: Extend BambuParser with additional patterns
- **Database**: Add new columns to files table
- **API**: Update file endpoints to return enhanced metadata
- **Testing**: Unit tests for parser enhancements

**Deliverables:**
- Enhanced metadata extraction from G-code and 3MF files
- Database schema updates
- Updated API responses with basic additional fields

### Phase 2: Frontend Display Enhancement (Sprint 2)
- **Components**: Create new metadata display components
- **UI/UX**: Design and implement enhanced file information layout
- **Integration**: Connect frontend to new API endpoints
- **Responsive**: Ensure mobile-friendly display

**Deliverables:**
- Comprehensive metadata display in file browser
- Enhanced file preview modal
- Mobile-responsive design
- User-friendly information organization

### Phase 3: Advanced Features (Sprint 3)
- **Analysis**: Implement cost calculation and quality assessment
- **Recommendations**: Add optimization suggestions
- **Compatibility**: Printer compatibility checking
- **Performance**: Optimize for large file collections

**Deliverables:**
- Cost breakdown calculations
- Print quality predictions
- Compatibility assessments
- Performance optimizations

## Success Metrics

### User Experience Metrics
- **Information Completeness**: 90%+ of files show comprehensive metadata
- **User Engagement**: 50%+ increase in file detail view usage
- **Decision Speed**: 30% reduction in time-to-print decisions
- **Error Reduction**: 25% fewer failed prints due to compatibility issues

### Technical Metrics
- **Parsing Success Rate**: 95%+ successful metadata extraction
- **Performance**: <500ms for metadata extraction per file
- **Accuracy**: 90%+ accuracy in cost and time estimates
- **Coverage**: Support for 100% of Bambu, 80% of Prusa files

## Risks and Mitigations

### Technical Risks
- **Risk**: Parser complexity may impact performance
  - **Mitigation**: Implement caching and background processing
- **Risk**: Database schema changes may cause migration issues
  - **Mitigation**: Careful migration scripts and rollback procedures

### User Experience Risks
- **Risk**: Information overload may confuse users
  - **Mitigation**: Progressive disclosure with expandable sections
- **Risk**: Mobile display may be cluttered
  - **Mitigation**: Responsive design with priority-based information hierarchy

## Future Enhancements

### Version 1.3.0+
- **Machine Learning**: Improve predictions based on actual print outcomes
- **Cloud Integration**: Sync metadata with online slicer profiles
- **Advanced Analytics**: Print success rate tracking and optimization
- **User Customization**: Configurable metadata display preferences

### Integration Opportunities
- **Slicer Integration**: Direct integration with BambuStudio/PrusaSlicer
- **Material Database**: Integration with filament manufacturer databases
- **Print History**: Correlation with actual print outcomes
- **Community Features**: Share optimized settings and recommendations

## Dependencies

### Internal Dependencies
- Existing BambuParser system
- File management infrastructure
- Database migration system
- Frontend component library

### External Dependencies
- Continued access to 3MF and G-code specification updates
- Slicer software compatibility maintenance
- Material cost database updates

## Documentation Requirements

### User Documentation
- Updated user guide with new metadata features
- Help tooltips for technical terminology
- Tutorial for interpreting quality indicators

### Developer Documentation
- Parser extension guidelines
- Metadata schema documentation
- API endpoint documentation updates

---

**Last Updated:** October 1, 2025  
**Document Version:** 1.0  
**Author:** Feature Planning Team  
**Review Status:** Pending Review