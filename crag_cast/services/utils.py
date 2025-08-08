import pandas as pd
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

CRAG_DATA_PATH = 'crag_cast/db/crag_df.csv'
WEATHER_DATA_PATH = 'crag_cast/db/cleaned_weather_df.csv'
crag_df = pd.read_csv(CRAG_DATA_PATH)
weather_df = pd.read_csv(WEATHER_DATA_PATH)

crag_df['latlon'] = crag_df[['latitude', 'longitude']].round(4).astype(str).agg('_'.join, axis=1)
weather_df['latlon'] = weather_df[['latitude', 'longitude']].round(4).astype(str).agg('_'.join, axis=1)