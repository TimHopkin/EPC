# EPC Data Integration Tool

A comprehensive Python tool for accessing, analyzing, and exporting UK Energy Performance Certificate (EPC) data. Designed to integrate seamlessly with LandApp and other Digital Land Solutions products.

## 🎯 Features

- **Unlimited API Access**: Bypass rate limits with authentication-based access
- **Spatial Queries**: Search by postcode, local authority, or UPRN
- **Smart Caching**: SQLite-based local storage to minimize API calls
- **Multiple Export Formats**: CSV and GeoJSON exports optimized for different use cases
- **Agricultural Focus**: Specialized searches for rural and agricultural properties
- **Supply Chain Reports**: Generate reports for retail supply chain analysis
- **Command Line Interface**: Simple, powerful CLI for all operations

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the tool
cd epc-tool

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 2. Configure API Access

Edit `.env` file with your EPC API credentials:

```env
EPC_API_USERNAME=your_username_here
EPC_API_PASSWORD=your_password_here
```

### 3. Test Connection

```bash
./epc-tool test
```

### 4. Basic Usage

```bash
# Search Surrey agricultural buildings
./epc-tool search --local-authority "Surrey" --agricultural --export geojson

# Get all properties in a postcode
./epc-tool search --postcode "GU5 0AA" --export csv

# Generate supply chain report
./epc-tool report --template supply-chain --uprns suppliers.csv
```

## 📋 Commands Reference

### Search Commands

#### Basic Search
```bash
./epc-tool search [OPTIONS]
```

**Options:**
- `--postcode TEXT`: Search by postcode (e.g., "GU5 0AA")
- `--local-authority TEXT`: Search by local authority (e.g., "Surrey")
- `--property-type [domestic|non-domestic]`: Property type (default: domestic)
- `--agricultural`: Search agricultural buildings only
- `--export [csv|geojson]`: Export format (default: csv)
- `--filename TEXT`: Custom output filename
- `--use-cache`: Use cached data when available (default: true)

**Examples:**
```bash
# Find all domestic properties in Guildford
./epc-tool search --local-authority "Guildford" --property-type domestic

# Export Surrey agricultural buildings as GeoJSON for LandApp
./epc-tool search --local-authority "Surrey" --agricultural --export geojson

# Search specific postcode with custom filename
./epc-tool search --postcode "SW1A 0AA" --filename "downing_street" --export csv
```

#### Trends Analysis
```bash
./epc-tool trends [OPTIONS]
```

**Options:**
- `--postcode TEXT`: Area for analysis
- `--local-authority TEXT`: Local authority for analysis
- `--from-year INTEGER`: Start year (default: 2020)
- `--to-year INTEGER`: End year (default: current year)

**Example:**
```bash
# Analyze energy efficiency trends in Surrey from 2020-2024
./epc-tool trends --local-authority "Surrey" --from-year 2020 --to-year 2024
```

### Report Generation

#### Specialized Reports
```bash
./epc-tool report [OPTIONS]
```

**Options:**
- `--template [supply-chain|agricultural]`: Report template (required)
- `--uprns TEXT`: Path to CSV file with UPRNs
- `--area TEXT`: Area name for report

**Examples:**
```bash
# Generate Waitrose supply chain report
./epc-tool report --template supply-chain --uprns waitrose_suppliers.csv --area "Waitrose_Network"

# Create agricultural buildings report
./epc-tool report --template agricultural --uprns farm_buildings.csv --area "Surrey_Farms"
```

### Cache Management

#### View Cache Statistics
```bash
./epc-tool cache stats
```

#### Clean Old Data
```bash
./epc-tool cache cleanup --max-age 30
```

## 📁 Output Formats

### CSV Exports
Standard CSV files with configurable columns. Specialized exports include:

- **Agricultural Summary**: Optimized for rural property analysis
- **Supply Chain Reports**: Formatted for retail supplier analysis
- **Energy Trends**: Time-series analysis data

### GeoJSON Exports
LandApp-compatible GeoJSON with:
- WGS84 coordinate system (EPSG:4326)
- Full property attributes as feature properties
- Optimized for direct import into mapping applications

## 🏗️ Project Structure

```
epc-tool/
├── src/
│   ├── api/
│   │   ├── client.py         # Main API client
│   │   ├── auth.py          # Authentication
│   │   └── pagination.py    # Pagination handling
│   ├── data/
│   │   ├── database.py      # SQLite caching
│   │   └── geocoder.py      # Address geocoding
│   ├── export/
│   │   ├── csv.py           # CSV exports
│   │   └── geojson.py       # GeoJSON exports
│   └── cli/
│       └── commands.py       # CLI interface
├── config/
│   └── settings.py           # Configuration
├── exports/                  # Output directory
├── data/                     # Cache directory
└── epc-tool                  # Executable script
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `EPC_API_USERNAME` | EPC API username | Required |
| `EPC_API_PASSWORD` | EPC API password | Required |
| `EPC_API_BASE_URL` | API base URL | https://epc.opendatacommunities.org/api/v1 |
| `OS_PLACES_API_KEY` | OS Places API key (optional) | None |
| `DATABASE_PATH` | Cache database path | data/epc_cache.db |
| `DEFAULT_EXPORT_PATH` | Default export directory | exports/ |
| `LOG_LEVEL` | Logging level | INFO |

### Cache Settings

The tool automatically caches API responses to minimize requests:

- **Default cache age**: 24 hours
- **Storage**: SQLite database
- **Auto-cleanup**: Configurable retention period
- **Smart invalidation**: Tracks data freshness

## 🌾 Agricultural Buildings

The tool includes specialized features for agricultural properties:

```bash
# Find all agricultural buildings in Surrey
./epc-tool search --local-authority "Surrey" --agricultural

# Export for grant eligibility analysis
./epc-tool search --postcode "GU5" --agricultural --export csv --filename "grant_eligible_farms"
```

Agricultural searches automatically:
- Filter for relevant property types
- Include building form and fuel type data
- Calculate energy improvement potential
- Format for grant application reports

## 🏪 Supply Chain Integration

Generate reports for retail supply chain analysis:

### UPRN List Format
Create a CSV file with supplier UPRNs:

```csv
uprn,supplier_name,location
12345678901,Farm Shop A,Surrey
12345678902,Farm Shop B,Hampshire
```

### Generate Report
```bash
./epc-tool report --template supply-chain --uprns suppliers.csv --area "Waitrose_Surrey"
```

Output includes:
- Energy ratings and efficiency scores
- CO2 emissions data
- Heating and lighting costs
- Floor area and property details
- Compliance tracking data

## 🗺️ LandApp Integration

GeoJSON exports are optimized for LandApp:

1. **Coordinate System**: WGS84 (EPSG:4326) - standard for web mapping
2. **Feature Properties**: All EPC attributes included
3. **Address Handling**: Full address strings for display
4. **Data Validation**: Coordinates verified before export

### Import to LandApp
1. Export data: `./epc-tool search --local-authority "Surrey" --export geojson`
2. Open LandApp
3. Import GeoJSON file
4. Layer will appear with full EPC attributes

## 📊 Performance

### Pagination
- **Method**: Search-after pagination (not offset-based)
- **Page Size**: 5,000 records per request
- **Rate Limiting**: Built-in retry logic with backoff
- **Progress Tracking**: Real-time progress indicators

### Geocoding
- **Primary**: OS Places API (if key provided)
- **Fallback**: Nominatim (OpenStreetMap)
- **Caching**: Coordinates cached with certificates
- **Batch Processing**: Optimized for large datasets

## 🔍 Use Cases

### Planning Applications
```bash
# Get energy data for planning area
./epc-tool search --postcode "RH1" --export geojson
```

### Grant Eligibility
```bash
# Find eligible agricultural buildings
./epc-tool search --local-authority "Surrey" --agricultural --export csv
```

### Supply Chain Auditing
```bash
# Generate supplier energy report
./epc-tool report --template supply-chain --uprns supplier_list.csv
```

### Energy Strategy
```bash
# Analyze improvement trends
./epc-tool trends --local-authority "Surrey" --from-year 2020
```

## 🔒 Security & Privacy

- **Credentials**: Stored in environment variables only
- **Local Data**: SQLite database for caching (GDPR compliant)
- **API Access**: Uses official government API endpoints
- **No Tracking**: Tool operates locally, no external analytics

## 🆘 Troubleshooting

### Connection Issues
```bash
# Test API credentials
./epc-tool test

# Check cache status
./epc-tool cache stats
```

### Common Solutions
1. **Authentication Failed**: Check `.env` credentials
2. **No Results**: Verify search parameters (postcode format, authority names)
3. **Geocoding Issues**: Ensure OS Places API key is set for best results
4. **Export Errors**: Check write permissions in export directory

## 🚀 Roadmap

### Phase 2 (Next Release)
- [ ] Web dashboard interface
- [ ] Advanced filtering options
- [ ] Bulk UPRN processing
- [ ] Land Registry integration
- [ ] Energy improvement calculators

### Phase 3 (Future)
- [ ] Real-time data monitoring
- [ ] API endpoints for integration
- [ ] Machine learning insights
- [ ] Mobile app companion

---

## 📞 Support

For issues, feature requests, or questions about integration with Digital Land Solutions products, please contact the development team.

**Trim Tab Philosophy**: Maximum leverage from existing infrastructure - this tool amplifies your ability to work with energy data efficiently and effectively.