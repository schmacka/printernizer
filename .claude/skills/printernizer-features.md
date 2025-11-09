# Printernizer Core Features

## Job Monitoring System

- Real-time job tracking for multiple printers
- 30-second polling intervals for status updates
- Job-based database architecture using SQLite
- Layer-by-layer progress tracking
- Time estimates and completion calculations
- Business vs private job classification

## File Management (Drucker-Dateien System)

### Capabilities

- **Automatic printer detection** of saved files on Bambu Lab & Prusa
- **One-click downloads** directly from GUI
- **Combined file listing** showing local and printer files in unified view
- **Smart download organization** by printer/date with secure file naming
- **Status tracking**: Available 📁, Downloaded ✓, Local 💾
- **Filter options** by printer and download status
- **Download statistics** and cleanup management

### File Status Indicators

- 📁 **Available** - On printer, not downloaded
- ✓ **Downloaded** - Saved to local storage
- 💾 **Local** - Only on local system

## Business & Export Features

### Cost Calculations

- Material cost tracking based on job data
- Power consumption calculations (configurable rates)
- Time-based cost calculations
- Business vs private job categorization

### Export Functionality

- **Excel/CSV export** for accounting software integration
- **Material consumption tracking** based on job data
- **Business statistics** for commercial operations
- Compatible with standard German accounting software (DATEV)

### German Business Compliance

- **19% VAT calculations** with German precision
- **GDPR/DSGVO compliance** with 7-year data retention
- **EUR currency formatting** (1.234,56 €)
- **Export compatibility** with German accounting software

## Enhanced 3D Model Metadata (Phase 2)

### Six Information Categories

1. **📋 Physical Properties** - Dimensions, volume, surface area, object count
2. **⚙️ Print Settings** - Layer height, nozzle, walls, infill, supports, temperatures
3. **🧵 Material Requirements** - Weight, length, type, colors, waste
4. **💰 Cost Breakdown** - Material cost, energy cost, per gram cost, total
5. **⭐ Quality Metrics** - Complexity score, difficulty level, success probability, overhangs
6. **🖨️ Compatibility** - Compatible printers, slicer info, profile, bed type, required features

### Metadata Extraction

- Comprehensive G-code parsing (40+ metadata patterns)
- 3MF file analysis with thumbnail extraction
- STL geometric analysis
- Derived metrics calculation
- Quality assessment algorithms

## 3D Preview System (Planned)

- **Multi-format support**: STL/3MF/G-Code with automatic format detection
- **Click-to-preview** directly from print list
- **Multiple rendering backends**: Trimesh, numpy-stl, matplotlib
- **Modal view** for detailed examination
- **Intelligent caching** for performance optimization

## Auto-Download System

- Automatic detection of currently printing files
- Smart filename matching with multiple variants
- Thumbnail extraction and processing
- G-code optimization for preview rendering
- Manual trigger capability from dashboard
