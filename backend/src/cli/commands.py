import click
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.api.client import EPCClient
from src.data.database import EPCDatabase
from src.export.csv import CSVExporter
from config.settings import Config

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL, 'INFO'))
logger = logging.getLogger(__name__)

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """EPC Data Integration Tool - Access UK Energy Performance Certificate data"""
    pass

@cli.command()
def test():
    """Test API connection and credentials"""
    try:
        client = EPCClient()
        if client.test_connection():
            click.echo("✅ API connection successful")
        else:
            click.echo("❌ API connection failed - check credentials")
            sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Connection test failed: {str(e)}")
        sys.exit(1)

@cli.command()
@click.option('--postcode', help='Postcode to search (e.g., GU5 0AA)')
@click.option('--local-authority', help='Local authority name (e.g., Surrey)')
@click.option('--property-type', type=click.Choice(['domestic', 'non-domestic']), default='domestic')
@click.option('--agricultural', is_flag=True, help='Search for agricultural buildings only')
@click.option('--export', type=click.Choice(['csv', 'geojson']), default='csv')
@click.option('--filename', help='Output filename (without extension)')
@click.option('--use-cache', is_flag=True, default=True, help='Use cached data when available')
def search(postcode, local_authority, property_type, agricultural, export, filename, use_cache):
    """Search for EPC certificates"""
    
    if not postcode and not local_authority:
        click.echo("❌ Either --postcode or --local-authority is required")
        sys.exit(1)
    
    try:
        client = EPCClient()
        db = EPCDatabase()
        
        if agricultural:
            if property_type == 'domestic':
                property_type = 'non-domestic'
            data = client.search_agricultural_buildings(
                local_authority=local_authority,
                postcode=postcode
            )
        elif postcode:
            data = client.search_by_postcode(postcode, property_type)
        elif local_authority:
            data = client.search_by_local_authority(local_authority, property_type)
        
        if data.empty:
            click.echo("❌ No records found")
            return
        
        if use_cache:
            db.store_certificates(data, property_type)
        
        click.echo(f"✅ Found {len(data)} records")
        
        if export == 'csv':
            exporter = CSVExporter()
            
            if not filename:
                if agricultural:
                    area_name = local_authority or postcode or "unknown"
                    filepath = exporter.export_agricultural_summary(data, area_name)
                else:
                    filename = f"epc_search_{property_type}"
                    filepath = exporter.export(data, filename)
            else:
                filepath = exporter.export(data, filename)
            
            if filepath:
                click.echo(f"📄 Exported to: {filepath}")
        
        elif export == 'geojson':
            from src.export.geojson import GeoJSONExporter
            
            exporter = GeoJSONExporter()
            
            if not filename:
                if agricultural:
                    area_name = local_authority or postcode or "unknown"
                    filepath = exporter.export_agricultural_geojson(data, area_name)
                else:
                    filename = f"epc_search_{property_type}"
                    filepath = exporter.export_for_landapp(data, filename)
            else:
                filepath = exporter.export_for_landapp(data, filename)
            
            if filepath:
                click.echo(f"🗺️  Exported to: {filepath}")
    
    except Exception as e:
        click.echo(f"❌ Search failed: {str(e)}")
        sys.exit(1)

@cli.command()
@click.option('--postcode', help='Postcode for trend analysis')
@click.option('--local-authority', help='Local authority for trend analysis')
@click.option('--from-year', type=int, default=2020, help='Start year for analysis')
@click.option('--to-year', type=int, help='End year for analysis (default: current year)')
def trends(postcode, local_authority, from_year, to_year):
    """Analyze energy efficiency trends over time"""
    
    if not postcode and not local_authority:
        click.echo("❌ Either --postcode or --local-authority is required")
        sys.exit(1)
    
    try:
        client = EPCClient()
        
        filters = {}
        if from_year:
            filters['from-year'] = from_year
        if to_year:
            filters['to-year'] = to_year
        
        if postcode:
            data = client.search_by_postcode(postcode, additional_filters=filters)
            area_name = postcode
        else:
            data = client.search_by_local_authority(local_authority, additional_filters=filters)
            area_name = local_authority
        
        if data.empty:
            click.echo("❌ No records found for trend analysis")
            return
        
        exporter = CSVExporter()
        filepath = exporter.export_energy_trends(data, area_name)
        
        if filepath:
            click.echo(f"✅ Trends analysis exported to: {filepath}")
        
    except Exception as e:
        click.echo(f"❌ Trends analysis failed: {str(e)}")
        sys.exit(1)

@cli.command()
@click.option('--template', type=click.Choice(['supply-chain', 'agricultural']), required=True)
@click.option('--uprns', help='Path to CSV file containing UPRNs')
@click.option('--area', help='Area name for the report')
def report(template, uprns, area):
    """Generate specialized reports"""
    
    try:
        client = EPCClient()
        
        if uprns:
            import pandas as pd
            uprn_df = pd.read_csv(uprns)
            
            if 'uprn' not in uprn_df.columns:
                click.echo("❌ UPRN CSV must contain 'uprn' column")
                sys.exit(1)
            
            all_data = []
            for uprn in uprn_df['uprn']:
                data = client.search_by_uprn(str(uprn))
                if not data.empty:
                    all_data.append(data)
            
            if all_data:
                combined_data = pd.concat(all_data, ignore_index=True)
            else:
                click.echo("❌ No data found for provided UPRNs")
                return
        else:
            click.echo("❌ --uprns is required for reports")
            sys.exit(1)
        
        exporter = CSVExporter()
        area_name = area or "report"
        
        if template == 'supply-chain':
            filepath = exporter.export_supply_chain_report(combined_data, area_name)
        elif template == 'agricultural':
            filepath = exporter.export_agricultural_summary(combined_data, area_name)
        
        if filepath:
            click.echo(f"✅ {template} report exported to: {filepath}")
        
    except Exception as e:
        click.echo(f"❌ Report generation failed: {str(e)}")
        sys.exit(1)

@cli.group()
def cache():
    """Cache management commands"""
    pass

@cache.command()
def stats():
    """Show cache statistics"""
    try:
        db = EPCDatabase()
        stats = db.get_cache_stats()
        
        click.echo("📊 Cache Statistics:")
        click.echo(f"Total certificates: {stats['total_certificates']}")
        click.echo(f"Recent (24h): {stats['recent_certificates']}")
        click.echo("By property type:")
        for prop_type, count in stats['by_property_type'].items():
            click.echo(f"  {prop_type}: {count}")
        click.echo(f"Database: {stats['database_path']}")
        
    except Exception as e:
        click.echo(f"❌ Failed to get cache stats: {str(e)}")

@cache.command()
@click.option('--max-age', default=30, help='Maximum age in days for data to keep')
def cleanup(max_age):
    """Clean up old cached data"""
    try:
        db = EPCDatabase()
        db.cleanup_old_data(max_age)
        click.echo(f"✅ Cleaned up data older than {max_age} days")
        
    except Exception as e:
        click.echo(f"❌ Cache cleanup failed: {str(e)}")

if __name__ == '__main__':
    cli()