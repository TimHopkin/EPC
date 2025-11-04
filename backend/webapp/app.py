#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_cors import CORS
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import folium
from folium import plugins
import json
import io
import base64
from datetime import datetime

from src.api.client import EPCClient
from src.data.database import EPCDatabase
from src.export.csv import CSVExporter
from src.export.geojson import GeoJSONExporter

app = Flask(__name__)
CORS(app)

# Initialize components
epc_client = EPCClient()
epc_db = EPCDatabase()
csv_exporter = CSVExporter()
geojson_exporter = GeoJSONExporter()

@app.route('/')
def dashboard():
    """Main dashboard with overview stats"""
    try:
        cache_stats = epc_db.get_cache_stats()
        return render_template('dashboard.html', cache_stats=cache_stats)
    except Exception as e:
        return render_template('dashboard.html', cache_stats={}, error=str(e))

@app.route('/search')
def search_page():
    """Search interface"""
    return render_template('search.html')

@app.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for searching EPC data"""
    try:
        data = request.json
        search_type = data.get('search_type')
        query = data.get('query', '').strip()
        property_type = data.get('property_type', 'domestic')
        agricultural = data.get('agricultural', False)
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Perform search based on type
        if search_type == 'postcode':
            if agricultural:
                results = epc_client.search_agricultural_buildings(postcode=query)
            else:
                results = epc_client.search_by_postcode(query, property_type)
        elif search_type == 'local_authority':
            if agricultural:
                results = epc_client.search_agricultural_buildings(local_authority=query)
            else:
                results = epc_client.search_by_local_authority(query, property_type)
        elif search_type == 'uprn':
            results = epc_client.search_by_uprn(query, property_type)
        else:
            return jsonify({'error': 'Invalid search type'}), 400
        
        if results.empty:
            return jsonify({
                'success': True,
                'count': 0,
                'data': [],
                'message': 'No records found'
            })
        
        # Cache results
        epc_db.store_certificates(results, property_type)
        
        # Convert to JSON-serializable format
        results_json = results.head(100).to_dict('records')  # Limit to 100 for display
        
        return jsonify({
            'success': True,
            'count': len(results),
            'data': results_json,
            'total_found': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['POST'])
def api_export():
    """Export search results"""
    try:
        data = request.json
        export_format = data.get('format', 'csv')
        search_data = data.get('search_data', [])
        filename = data.get('filename', f'epc_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
        if not search_data:
            return jsonify({'error': 'No data to export'}), 400
        
        df = pd.DataFrame(search_data)
        
        if export_format == 'csv':
            filepath = csv_exporter.export(df, filename)
            return jsonify({
                'success': True,
                'filepath': filepath,
                'download_url': f'/download/{Path(filepath).name}'
            })
        elif export_format == 'geojson':
            filepath = geojson_exporter.export_for_landapp(df, filename)
            return jsonify({
                'success': True,
                'filepath': filepath,
                'download_url': f'/download/{Path(filepath).name}'
            })
        else:
            return jsonify({'error': 'Invalid export format'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/map')
def map_page():
    """Interactive map page"""
    return render_template('map.html')

@app.route('/api/map_data', methods=['POST'])
def api_map_data():
    """Generate map data for visualization"""
    try:
        data = request.json
        search_results = data.get('data', [])
        
        if not search_results:
            return jsonify({'error': 'No data provided'}), 400
        
        df = pd.DataFrame(search_results)
        
        # Create map centered on UK
        m = folium.Map(
            location=[54.5, -3.0],  # UK center
            zoom_start=6,
            tiles='OpenStreetMap'
        )
        
        # Add EPC data points
        for idx, row in df.head(1000).iterrows():  # Limit to 1000 points for performance
            # Create popup content
            popup_html = f"""
            <div style="font-family: Arial; width: 250px;">
                <h4 style="color: #2c3e50; margin-bottom: 10px;">
                    {row.get('address1', 'Unknown Address')}
                </h4>
                <p><strong>Postcode:</strong> {row.get('postcode', 'N/A')}</p>
                <p><strong>Energy Rating:</strong> 
                   <span style="background-color: {get_energy_color(row.get('current-energy-rating', 'N/A'))}; 
                         color: white; padding: 2px 6px; border-radius: 3px;">
                     {row.get('current-energy-rating', 'N/A')}
                   </span>
                </p>
                <p><strong>Efficiency Score:</strong> {row.get('current-energy-efficiency', 'N/A')}</p>
                <p><strong>Property Type:</strong> {row.get('property-type', 'N/A')}</p>
                <p><strong>Floor Area:</strong> {row.get('total-floor-area', 'N/A')} m²</p>
            </div>
            """
            
            # Use postcode for rough location (would need geocoding for exact coords)
            postcode = row.get('postcode', '')
            if postcode:
                # For now, use approximate UK postcode locations
                # In production, you'd geocode these
                lat, lng = get_approximate_postcode_location(postcode)
                
                folium.CircleMarker(
                    location=[lat, lng],
                    radius=6,
                    popup=folium.Popup(popup_html, max_width=300),
                    color=get_energy_color(row.get('current-energy-rating', 'N/A')),
                    fillColor=get_energy_color(row.get('current-energy-rating', 'N/A')),
                    fillOpacity=0.7,
                    weight=2
                ).add_to(m)
        
        # Add legend
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 150px; height: 90px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p style="margin: 0;"><b>Energy Ratings</b></p>
        <p style="margin: 5px 0;"><i style="background:#2d5aa0;width:12px;height:12px;float:left;margin-right:8px;"></i>A</p>
        <p style="margin: 5px 0;"><i style="background:#2f7ed8;width:12px;height:12px;float:left;margin-right:8px;"></i>B</p>
        <p style="margin: 5px 0;"><i style="background:#0d8ecf;width:12px;height:12px;float:left;margin-right:8px;"></i>C</p>
        <p style="margin: 5px 0;"><i style="background:#2b908f;width:12px;height:12px;float:left;margin-right:8px;"></i>D</p>
        <p style="margin: 5px 0;"><i style="background:#90ed7d;width:12px;height:12px;float:left;margin-right:8px;"></i>E</p>
        <p style="margin: 5px 0;"><i style="background:#f7a35c;width:12px;height:12px;float:left;margin-right:8px;"></i>F</p>
        <p style="margin: 5px 0;"><i style="background:#8085e9;width:12px;height:12px;float:left;margin-right:8px;"></i>G</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # Convert map to HTML
        map_html = m._repr_html_()
        
        return jsonify({
            'success': True,
            'map_html': map_html,
            'point_count': len(df.head(1000))
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analytics')
def analytics_page():
    """Analytics and charts page"""
    return render_template('analytics.html')

@app.route('/api/analytics', methods=['POST'])
def api_analytics():
    """Generate analytics charts"""
    try:
        data = request.json
        search_results = data.get('data', [])
        
        if not search_results:
            return jsonify({'error': 'No data provided'}), 400
        
        df = pd.DataFrame(search_results)
        
        charts = {}
        
        # Energy Rating Distribution
        if 'current-energy-rating' in df.columns:
            rating_counts = df['current-energy-rating'].value_counts()
            charts['energy_ratings'] = {
                'data': [{
                    'x': rating_counts.index.tolist(),
                    'y': rating_counts.values.tolist(),
                    'type': 'bar',
                    'marker': {'color': [get_energy_color(rating) for rating in rating_counts.index]}
                }],
                'layout': {
                    'title': 'Energy Rating Distribution',
                    'xaxis': {'title': 'Energy Rating'},
                    'yaxis': {'title': 'Number of Properties'}
                }
            }
        
        # Property Type Distribution  
        if 'property-type' in df.columns:
            property_counts = df['property-type'].value_counts().head(10)
            charts['property_types'] = {
                'data': [{
                    'labels': property_counts.index.tolist(),
                    'values': property_counts.values.tolist(),
                    'type': 'pie'
                }],
                'layout': {'title': 'Property Type Distribution'}
            }
        
        # Energy Efficiency Histogram
        if 'current-energy-efficiency' in df.columns:
            efficiency_scores = df['current-energy-efficiency'].dropna()
            charts['efficiency_histogram'] = {
                'data': [{
                    'x': efficiency_scores.tolist(),
                    'type': 'histogram',
                    'nbinsx': 20
                }],
                'layout': {
                    'title': 'Energy Efficiency Score Distribution',
                    'xaxis': {'title': 'Efficiency Score'},
                    'yaxis': {'title': 'Frequency'}
                }
            }
        
        return jsonify({
            'success': True,
            'charts': charts,
            'data_summary': {
                'total_records': len(df),
                'avg_efficiency': df.get('current-energy-efficiency', pd.Series([0])).mean(),
                'most_common_rating': df.get('current-energy-rating', pd.Series(['N/A'])).mode().iloc[0] if not df.empty else 'N/A'
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download exported files"""
    try:
        export_path = Path('exports')
        filepath = export_path / filename
        
        if filepath.exists():
            return send_file(filepath, as_attachment=True)
        else:
            return "File not found", 404
            
    except Exception as e:
        return f"Download error: {str(e)}", 500

def get_energy_color(rating):
    """Get color for energy rating"""
    colors = {
        'A': '#2d5aa0',
        'B': '#2f7ed8', 
        'C': '#0d8ecf',
        'D': '#2b908f',
        'E': '#90ed7d',
        'F': '#f7a35c',
        'G': '#8085e9'
    }
    return colors.get(rating, '#cccccc')

def get_approximate_postcode_location(postcode):
    """Get approximate location for UK postcode"""
    # This is a simplified mapping - in production you'd use proper geocoding
    postcode_areas = {
        'GU1': (51.2362, -0.5704),  # Guildford
        'GU2': (51.2483, -0.5915),
        'M1': (53.4808, -2.2426),   # Manchester
        'SW1': (51.4994, -0.1319),  # Westminster
        'EC1': (51.5186, -0.1067),  # City of London
        'W1': (51.5154, -0.1410),   # West End
    }
    
    # Extract postcode area
    area = postcode.split()[0] if ' ' in postcode else postcode[:2]
    return postcode_areas.get(area, (54.5, -3.0))  # Default to UK center

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0', threaded=True)