import pandas as pd
from flask import Flask, render_template, request
from flask_paginate import Pagination, get_page_args
from urllib.parse import urlencode
from crag_cast import app


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
        crags.append({
            'id': row['crag_id'],
            'crag_name': row['crag_name'],
            'country': row['country'],
            'county': row['county'],
            'latitude': row['latitude'],
            'longitude': row['longitude'],
            'rocktype': row['rocktype'],
            'routes_count': len(crag_df[crag_df['crag_id'] == row['crag_id']]),
            'weather': None  
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
        crag_routes = crag_df[crag_df['crag_id'] == crag_id]
        if crag_routes.empty:
            return render_template('crag_detail.html', crag=crag, routes=[])

        crag = crag_routes.iloc[0][['crag_id', 'crag_name', 'country', 'county', 'latitude', 'longitude', 'rocktype']]

        routes = crag_routes[['sector_name', 'route_name', 'type', 'difficulty_grade', 'safety_grade']].dropna(subset=['route_name'])

        return render_template('crag_detail.html', crag=crag, routes=routes.to_dict(orient='records'))
