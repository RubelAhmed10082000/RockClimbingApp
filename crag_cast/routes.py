import pandas as pd
from flask import Flask, render_template, request
from flask_paginate import Pagination, get_page_args
from urllib.parse import urlencode
from crag_cast import app, cache
import requests
from flask import jsonify
from datetime import datetime, timedelta, timezone
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

CRAG_DATA_PATH = 'crag_cast/db/crag_df.csv'
WEATHER_DATA_PATH = 'crag_cast/db/cleaned_weather_df.csv'
crag_df = pd.read_csv(CRAG_DATA_PATH)
weather_df = pd.read_csv(WEATHER_DATA_PATH)

crag_df['latlon'] = crag_df[['latitude', 'longitude']].round(4).astype(str).agg('_'.join, axis=1)
weather_df['latlon'] = weather_df[['latitude', 'longitude']].round(4).astype(str).agg('_'.join, axis=1)

@app.route('/', methods=['GET', 'POST'])
def index():
    countries = sorted(crag_df['country'].dropna().unique())
    counties = sorted(crag_df['county'].dropna().unique())
    grade = sorted(crag_df['difficulty_grade'].dropna().unique())
    rocktypes = sorted(crag_df['rocktype'].dropna().unique())
    type = sorted(crag_df['type'].dropna().unique())

    # Get filters from request.args for GET, or request.form for POST
    search_query = request.args.get('search', '')
    selected_country = request.args.getlist('country')
    selected_rocktype = request.args.getlist('rocktype')
    selected_county = request.args.getlist('county')
    selected_type = request.args.getlist('type')
    sort_by = request.args.get('sort_by', 'crag_name')
    sort_order = request.args.get('sort_order', 'asc')
   
    try:
        page, per_page, offset = get_page_args(page_parameter = 'page', per_page_parameter='per_page')
        if not per_page:
            per_page = 10
    except Exception:
        page, per_page, offset = 1, 10, 0

    # Filter crags
    filtered = crag_df.drop_duplicates(subset='crag_id').copy()
    if search_query:
        filtered = filtered[filtered['crag_name'].str.contains(search_query, case=False, na=False)]
    if selected_country and '' not in selected_country:
        filtered = filtered[filtered['country'].isin(selected_country)]
    if selected_rocktype and '' not in selected_rocktype:
        filtered = filtered[filtered['rocktype'].isin(selected_rocktype)]
    if selected_county and '' not in selected_county:
        filtered = filtered[filtered['county'].isin(selected_county)]
    if selected_type and '' not in selected_type:
        filtered = filtered[filtered['type'].isin(selected_type)]

    # Sorting
    if sort_by in filtered.columns:
        filtered = filtered.sort_values(by=sort_by, ascending=(sort_order == 'asc'))

    total_crags = len(filtered)
    total_pages = filtered.iloc[offset:offset + per_page].copy()
    start = (page - 1) * per_page
    end = start + per_page
    page_crags = filtered.iloc[start:end].copy()

    # Dummy weather and routes_count for now
    crags = []
    for _, row in page_crags.iterrows():
        latlon_key = row['latlon']
        weather_row = weather_df[weather_df['latlon'] == latlon_key]

        if not weather_row.empty:
            weather_data = weather_row.iloc[0]
            weather = {
                'temperature': weather_data['temperature'],
                'humidity': weather_data['humidity'],
                'precipitation': weather_data['precipitation'],
                "last_rained": get_last_rained(row['latitude'], row['longitude'])
            }
        else:
            weather = None

        crags.append({
            'id': row['crag_id'],
            'crag_name': row['crag_name'],
            'country': row['country'],
            'county': row['county'],
            'latitude': row['latitude'],
            'longitude': row['longitude'],
            'rocktype': row['rocktype'],
            'routes_count': len(crag_df[crag_df['crag_id'] == row['crag_id']]),
            'weather': weather  
        })

    base_args = {
        'search': search_query,
        'sort_by': sort_by,
        'sort_order': sort_order,
        'per_page': per_page,
    }

    href_template = '/?' + urlencode(base_args, doseq=True) + '&page={0}'

    pagination = Pagination(
        page=page,
        per_page=per_page,
        total=total_crags,
        css_framework='bootstrap4',
        record_name='crags',
        format_total=True,
        format_number=True,
        href=href_template  
    )

    for val in selected_country:
        base_args.setdefault('country', []).append(val)
    for val in selected_rocktype:
        base_args.setdefault('rocktype', []).append(val)
    for val in selected_county:
        base_args.setdefault('county', []).append(val)
    for val in selected_type:
        base_args.setdefault('type', []).append(val)


    return render_template('index.html',
        countries=countries,
        counties=counties,
        rock_types=rocktypes,
        crags=crags,
        total_crags=total_crags,
        search_query=search_query,
        selected_country=selected_country,
        selected_rocktype=selected_rocktype,
        selected_county=selected_county,
        type=type,
        sort_by=sort_by,
        sort_order=sort_order,
        per_page=per_page,
        pagination=pagination,
        current_page = page,
        total_pages = (total_crags + per_page - 1) // per_page
    )

@app.route('/results')
def paginated_results():
    page = int(request.args.get('page', 1))
    per_page = 10

    filtered = crag_df.copy()
    start = (page - 1) * per_page
    end = start + per_page
    page_crags = filtered.iloc[start:end].copy()

    page_crags['latlon'] = page_crags[['latitude', 'longitude']].round(4).astype(str).agg('_'.join, axis=1)
    weather_subset = weather_df.copy()
    weather_subset['latlon'] = weather_subset[['latitude', 'longitude']].round(4).astype(str).agg('_'.join, axis=1)
    merged = pd.merge(page_crags, weather_subset, on='latlon', how='left')

    crags = merged.to_dict(orient='records')
    total = len(filtered)

    return render_template('results.html', crags=crags, page=page, per_page=per_page, total=total)

@app.route('/crag/<int:crag_id>')
def crag_detail(crag_id):
    crag_routes_df = crag_df[crag_df['crag_id'] == crag_id]
    if crag_routes_df.empty:
        return render_template('crag_detail.html', crag={}, weather=None)

    first_row = crag_routes_df.iloc[0]

    crag = {
        'crag_id': crag_id,
        'crag_name': first_row.get('crag_name'),
        'crag_country': first_row.get('country'),
        'crag_county': first_row.get('county'),
        'crag_latitude': first_row.get('latitude'),
        'crag_longitude': first_row.get('longitude'),
        'crag_rocktype': first_row.get('rocktype'),
        'access': first_row.get('access', ''),
        'crag_routes': []
    }

    for _, row in crag_routes_df.iterrows():
        crag['crag_routes'].append({
            'name': row.get('route_name'),
            'grade': row.get('difficulty_grade'),
            'type': row.get('type'),
        })

    return render_template('crag_detail.html', crag=crag)



@app.route('/api/weather/<lat>/<lon>')
@cache.memoize()
def get_weather(lat,lon):
    try:
        logger.info(f"Fetching weather for lat={lat}, lon-{lon}")
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current_weather=true"
            f"&hourly=temperature_2m,relative_humidity_2m,precipitation,windspeed_10m"
            f"&timezone=auto"
        )
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()

        hourly = data.get("hourly", {})
        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        hourly_times = [datetime.fromisoformat(t) for t in hourly.get ("time", [])]
        time_diffs = [abs((t - now).total_seconds()) for t in hourly_times]
        idx = time_diffs.index(min(time_diffs))

    
        result = ({
            "temperature": hourly.get("temperature_2m", [None])[idx],
            "humidity": hourly.get("relative_humidity_2m", [None])[idx],
            "precipitation": hourly.get("precipitation", [None])[idx],
            "windspeed": hourly.get("windspeed_10m", [None])[idx]
        })

        logger.info(f"Weather data fetched successfully for {lat}, {lon}: {result}")
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error fetching weather for lat={lat}, lon={lon}: {e}")
        return jsonify({"error": str(e)}), 500


"""@cache.memoize(timeout=1800)
def get_last_rained(lat,lon):
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=5)

    response = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "hourly": "precipitation",
            "timezone": "auto"
        }
    )

    data = response.json()
    times = data.get("hourly", {}).get("time",[])
    precipitation = data.get("hourly", {}).get("precipitation",[])

    if not times or not precipitation:
        logger.warning(f"No historical precipitation data for lat={lat}, lon={lon}")
        return None


    for time, value in reversed(list(zip(times, precipitation))):
        if value > 0:
            logger.info(f"Last rained at {time} for lat={lat}, lon={lon}")
            return time
    
    logger.info(f"No rain found in the past 5 days for lat={lat}, lon={lon}")
    return None

@app.template_filter('pretty_date')
def pretty_date(value):
    try:
        for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M'):
            try:
                dt = datetime.strptime(value, fmt)
                break
            except ValueError:
                continue
        else:
            return value
            
        now = datetime.now()
        delta = now - dt
        
        seconds = delta.total_seconds()
        minutes = seconds // 60
        hours = minutes // 60
        days = delta.days

        if seconds < 60:
            return "just now"
        elif minutes < 60:
            return f"{int(minutes)} minutes ago"
        elif hours < 24:
            return f"{int(hours)} hours ago"
        elif days == 1:
            return "1 day ago"
        elif days <= 5:
            return f"{days} days ago"
        elif days > 5:
            return "more than 5 days ago"
        else:
            return dt.strftime("%d %b %Y")
    
    except Exception:
        return value"""
