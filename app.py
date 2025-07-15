from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

CRAG_DATA_PATH = 'Working_Code/Files/crag_df.csv'
WEATHER_DATA_PATH = 'Working_Code/Files/cleaned_weather_df.csv'
crag_df = pd.read_csv(CRAG_DATA_PATH)
weather_df = pd.read_csv(WEATHER_DATA_PATH)

crag_df['latlon'] = crag_df[['latitude', 'longitude']].round(4).astype(str).agg('_'.join, axis=1)
weather_df['latlon'] = weather_df[['latitude', 'longitude']].round(4).astype(str).agg('_'.join, axis=1)

@app.route('/', methods=['GET', 'POST'])
def index():
    countries = sorted(crag_df['country'].dropna().unique())
    counties = sorted(crag_df['county'].dropna().unique())
    grades = sorted(crag_df['difficulty_grade'].dropna().unique())
    rocktypes = sorted(crag_df['rocktype'].dropna().unique())
    climbing_types = sorted(crag_df['type'].dropna().unique())

    # Get filters from request.args for GET, or request.form for POST
    search_query = request.args.get('search', '')
    selected_country = request.args.get('country', '')
    selected_rocktype = request.args.get('rocktype', '')
    selected_county = request.args.get('county', '')
    sort_by = request.args.get('sort_by', 'crag_name')
    sort_order = request.args.get('sort_order', 'asc')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    # Filter crags
    filtered = crag_df.copy()
    if search_query:
        filtered = filtered[filtered['crag_name'].str.contains(search_query, case=False, na=False)]
    if selected_country:
        filtered = filtered[filtered['country'] == selected_country]
    if selected_rocktype:
        filtered = filtered[filtered['rocktype'] == selected_rocktype]
    if selected_county:
        filtered = filtered[filtered['county'] == selected_county]

    # Sorting
    if sort_by in filtered.columns:
        filtered = filtered.sort_values(by=sort_by, ascending=(sort_order == 'asc'))

    total_crags = len(filtered)
    total_pages = max(1, (total_crags + per_page - 1) // per_page)
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
            'routes_count': row.get('routes_count', 0),
            'weather': None  # or add weather if available
        })

    return render_template('index.html',
        countries=countries,
        counties=counties,
        rock_types=rocktypes,
        crags=crags,
        total_crags=total_crags,
        current_page=page,
        total_pages=total_pages,
        search_query=search_query,
        selected_country=selected_country,
        selected_rocktype=selected_rocktype,
        selected_county=selected_county,
        sort_by=sort_by,
        sort_order=sort_order,
        per_page=per_page
    )

    return render_template('index.html',
        countries=countries,
        counties=counties,
        grades=grades,
        rocktypes=rocktypes,
        climbing_types=climbing_types)

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
    crag = crag_df[crag_df['crag_id'] == crag_id].iloc[0]
    return render_template('crag_detail.html', crag=crag)

if __name__ == '__main__':
    app.run(debug=True)
