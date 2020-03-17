import json
import pandas as pd
import numpy as np
import copy
import os
import geopandas as gpd


def get_pre_ripa_data(cols_cfgs, **cfgs):

    base_url, description_url, race_url = [
      "http://seshat.datasd.org/pd/vehicle_stops_2014_datasd_v1.csv",
      "http://seshat.datasd.org/pd/vehicle_stops_search_details_2014_datasd.csv",
      "http://seshat.datasd.org/pd/vehicle_stops_race_codes.csv"
    ]

    years, races, cols, outdir = copy.deepcopy(cfgs['years']), cfgs['races'], cfgs['pre-RIPA_cols'], cfgs['outdir']
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    stop_df = pd.DataFrame()

    # if years includes only 2019, no pre-ripa data needed
    if min(years) > 2018:
        return

    # 2018 data is located in the 2017 csv file, handle case when 2017 is not in years but 2018 is
    if 2018 in years:
        years.remove(2018)
        if 2017 not in years:
            years.append(2017)

    if 2019 in years:
        years.remove(2019)

    # map how race is indicated in config file to how it is indicated in dataset (e.g., white -> W)
    race_mapper = {'white':'W','black':'B','hispanic':'H'}
    if races[0] == 'all':
        race_filter = []
    else:
        race_filter = [race_mapper[r] for r in races]

    # indicate which columns belong to the basic details dataset, and which belong to search details dataset
    main_cols = list(set(cols_cfgs['pre-ripa'].keys()).intersection(set(cols)))
    detail_cols = list(set(cols_cfgs['pre-ripa_details'].keys()).intersection(set(cols)))

    for year in set(years):

        # Get urls for stop data from year
        url = base_url.replace('2014',str(year))
        description_url_c = description_url.replace('2014',str(year))
        df = pd.read_csv(url,usecols = main_cols)

        default_date = '{}-12-31 23:39:00'.format(year)
        df['date_time'].fillna(default_date)

        # handle case when either 2017 or 2018 is in dataset, but not both
        if year == 2017:
            if 2017 not in cfgs['years']:
                df = df[df['date_time'].apply(lambda x: pd.to_datetime(x).year) == 2018]
            elif 2018 not in cfgs['years']:
                df = df[df['date_time'].apply(lambda x: pd.to_datetime(x).year) == 2017]

        # if race is to be included and not all races are needed, filter by neede races
        # join race description to basic details dataset
        if 'subject_race' in df.columns:
            if races[0] != 'all':
                df = df[df.subject_race.isin(race_filter)]
            df_race = pd.read_csv(race_url)
            df = df.merge(df_race,left_on = 'subject_race',right_on='Race Code')

        # handle when no columns from details dataset are specified in config file
        if len(detail_cols) > 1:
            df_details = pd.read_csv(description_url_c,usecols=detail_cols)
            df = df.merge(df_details,on='stop_id')
        stop_df = pd.concat([stop_df,df])

    stop_df.reset_index(inplace=True,drop=True)
    file_path = os.path.join(outdir,'pre_ripa.csv')
    stop_df.to_csv(file_path,index=False)


def get_ripa_data(cols_cfgs, **cfgs):

    years, races, r_cols, outdir = copy.deepcopy(cfgs['years']), cfgs['races'], cfgs['RIPA_cols'], cfgs['outdir']
    stop_df = pd.DataFrame()

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # If no data from 2018 or 2019 is needed, no data from ripa datasets are needed
    if max(years) < 2018:
        return

    filter_years = list(set(years).intersection(set([2018,2019])))

    RIPA_urls = [
     "http://seshat.datasd.org/pd/ripa_stops_datasd_v1.csv",
     "http://seshat.datasd.org/pd/ripa_actions_taken_datasd.csv",
     "http://seshat.datasd.org/pd/ripa_contraband_evid_datasd.csv",
     "http://seshat.datasd.org/pd/ripa_prop_seize_type_datasd.csv",
     "http://seshat.datasd.org/pd/ripa_race_datasd.csv",
     "http://seshat.datasd.org/pd/ripa_stop_reason_datasd.csv",
     "http://seshat.datasd.org/pd/ripa_stop_result_datasd.csv"
    ]

    # map how race is indicated in config file to how it is indicated in dataset (e.g., white -> W)
    race_mapper = {'white':'White','black':'Black/African American',
    'hispanic':'Hispanic/Latino/a','other':['Native American','Pacific Islander'],
    'asian':['Middle Eastern or South Asian','Asian']}
    # create list of races to filter by
    race_filter = []
    if races[0] != 'all':
        for r in races:
            if r in ['asian','other']:
                race_filter.append(race_mapper[r.lower()][0])
                race_filter.append(race_mapper[r.lower()][1])
            else:
                race_filter.append(race_mapper[r.lower()])

    for url, cols in zip(RIPA_urls,cols_cfgs.items()):
        # specify which cols are needed from each dataset
        usecols  = list(set(r_cols).intersection(set(cols[1].keys())))
        df = pd.read_csv(url,usecols=usecols)
        # If years don't include both 2018 and 2019, filter out unneeded year
        if ('date_stop' in df.columns) and (len(filter_years) != 2):
            df = df[df.date_stop.apply(lambda x: pd.to_datetime(x).year).isin(filter_years)]
        # filter out unneeded races
        if 'race' in df.columns:
            if races[0] != 'all':
                df = df[df.race.isin(race_filter)]
        if stop_df.empty:
            stop_df = df.copy()
        else:
            stop_df = stop_df.merge(df,on=['stop_id','pid'])

    stop_df.reset_index(inplace=True,drop=True)

    file_path = os.path.join(outdir,'ripa.csv')

    stop_df.to_csv(file_path,index=False)

# Read in service area data and write to file
def get_service_area_info(**cfgs):

    pd_beats_url = 'http://seshat.datasd.org/sde/pd/pd_beats_datasd.geojson'
    sa = gpd.read_file(pd_beats_url)
    outdir = cfgs['outdir']
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    file_path = os.path.join(outdir,'service_area.geojson')
    sa.to_file(file_path,driver="GeoJSON")

def get_stops_data(cols_cfgs, **cfgs):
    get_pre_ripa_data(cols_cfgs, **cfgs)
    get_ripa_data(cols_cfgs, **cfgs)
    get_service_area_info(**cfgs)
