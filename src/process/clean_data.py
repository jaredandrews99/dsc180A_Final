import json
import pandas as pd
import numpy as np
import copy
import os
import geopandas as gpd
import tables
from shapely.ops import unary_union
from itertools import combinations
from shapely.geometry import Point


# ---------------------------------------------------------------------
# Pre-Ripa Data Cleaning Helper Functions
# ---------------------------------------------------------------------

# if age is less than 15 or greater than 99, set age to nan
def clean_pr_age(val):
    if type(val) == float:
        return np.nan
    if val.isdigit():
        i_val = int(val)
        if (i_val > 14) and (i_val < 100):
            return i_val
    return np.nan

def clean_pr_arrested(val):
    arrested_mapper = {'n':'N','y':'Y',' ':np.nan,'b':np.nan,'M':np.nan}
    if val in arrested_mapper.keys():
        return arrested_mapper[val]
    return val

def clean_pr_searched(val):
    searched_mapper = {'n':'N','y':'Y',' ':np.nan,'b':np.nan,'\\':np.nan}
    if val in searched_mapper.keys():
        return searched_mapper[val]
    return val

# map stop cause to one of: 'moving violation','equiptment violation','other' or nan
def clean_pr_stop_cause(val):

    stop_cause_not_marked = [np.nan,'No Cause Specified on a Card',
    'NOT CHECKED','NOT SPECIFIED','not marked  not marked', 'NOTHING MARKED',
    'not marked','none listed', 'not noted', 'not listed', 'not secified',
    'NOT MARKED', 'no cause listed']
    moving_violation = ['Moving Violation','&Moving Violation']
    equiptment_violation = ['Equipment Violation','&Equipment Violation']

    if val in stop_cause_not_marked:
        return np.nan

    elif val in moving_violation:
        return 'Moving Violation'

    elif val in equiptment_violation:
        return 'Equiptment Violation'

    else:
        return 'Other'

# map race to one of: 'white','black','hispanic','asian', or 'other'
def clean_pr_race(val):

    race_mapper = {'WHITE':'White','HISPANIC':'Hispanic','BLACK':'Black',
                       'OTHER':'Other','OTHER ASIAN':'Asian','FILIPINO':'Asian',
                       'VIETNAMESE':'Asian','CHINESE':'Asian','INDIAN':'Asian',
                       'KOREAN':'Asian','JAPANESE':'Asian','PACIFIC ISLANDER':'Other',
                       'LAOTIAN':'Asian','ASIAN INDIAN':'Asian',
                       'SAMOAN':'Other','CAMBODIAN':'Asian','GUAMANIAN':'Other',
                       'HAWAIIAN':'Other'}

    m_race = race_mapper[val] if val in race_mapper.keys() else np.nan

    return m_race

# ---------------------------------------------------------------------
# Ripa Data Cleaning Helper Functions
# ---------------------------------------------------------------------

# if age is less than 15 or greater than 99, set age to nan
def clean_r_age(val):

    if (val > 14) and (val < 100):
        return val
    return np.nan

def create_r_property_seized(val):
    if val == 'Property was seized':
        return 'Y'
    return 'N'

def create_r_searched(val):
    if 'searched' in val.lower():
        return 'Y'
    return 'N'

def create_r_arrested(val):
    if 'arrest' in val.lower():
        return 'Y'
    return 'N'

def create_r_citation(val):
    if ('citation' in val.lower()) or ('cite' in val.lower()):
        return 'Y'
    return 'N'

# map race to one of: 'white','black','hispanic','asian','Pacific Islander','Middle Eastern or South Asian' or 'other'
def clean_r_race(val):

    # Races that need mapping, some races already properly formatted
    race_mapper = {'Black/African American':'Black','Hispanic/Latino/a':'Hispanic',
                'Native American':'Other','Pacific Islander':'Other',
                'Middle Eastern or South Asian':'Asian'}

    m_race = race_mapper[val] if val in race_mapper.keys() else val
    return m_race

# map stop cause to one of: 'moving violation','equiptment violation','other' or nan
def clean_r_stop_cause(val):

    if val == 'Moving Violation':
        return 'Moving Violation'
    elif val == 'Equiptment Violation':
        return 'Equiptment Violation'
    if type(val) == float:
        return np.nan
    return 'Other'

# ---------------------------------------------------------------------
# Service Area and Population Cleaning Functions
# ---------------------------------------------------------------------

def clean_service_area_data(**cfgs):

    indir= cfgs['indir']

    data_file = os.path.join(indir,'service_area.geojson')
    df = gpd.read_file(data_file, driver='GeoJSON')[['serv','geometry']]
    crs = df.crs
    service_area = []
    geometry = []
    # consolidate all blocks into one service area and take union of blocks geometries
    for serv in df['serv'].unique():
        polygons = df[df['serv'] == serv]['geometry']
        service_area.append(serv)
        geometry.append(unary_union(polygons))
    output = gpd.GeoSeries(data=geometry,crs=crs,index = service_area).sort_index()

    # remove any intersections between different service areas
    for s1,s2 in combinations(output.index,2):
        s1_g, s2_g = output[s1], output[s2]
        if s1_g.intersects(s2_g):
            intersection_ = s1_g.intersection(s2_g)
            s1_n, s2_n = s1_g - intersection_, s2_g - intersection_
            output[s1],output[s2]  = s1_n, s2_n

    geometry = list(output.values)
    # change from geopandas series to geopandas dataframe
    output_df = gpd.GeoDataFrame(data= output.index,crs = crs, geometry = geometry,columns=['service_area'])

    return output_df

def clean_census_data(**cfgs):

    indir_census, outdir = "data/census", "data/cleaned"

    # read in and filter census data so that only san diego county is included
    population_file = os.path.join(indir_census,'population_data.csv')
    blocks = pd.read_csv(population_file)
    race_map = {'White':['H72003','H7Z011'],'Black':['H72004','H7Z012'],
                'Asian' : ['H72006','H7Z014'],'Other':['H72005','H72007','H72008','H7Z013','H7Z015','H7Z016'],
                'Hispanic': ['H7Z011','H7Z012','H7Z014','H7Z013','H7Z015','H7Z016']}

    stops_data_path = os.path.join(outdir,'cleaned_stops.csv')
    races = pd.read_csv(stops_data_path)['subject_race'].unique()
    blocks_columns = set(['COUNTY','GISJOIN'])
    for race in races:
        cols = race_map[race]
        for c in cols:
            blocks_columns.add(c)
    blocks = blocks[list(blocks_columns)]
    san_diego_blocks = blocks[blocks['COUNTY'] == 'San Diego County']

    # Read in shape file and take center of block point as geometry
    shp_file = os.path.join(indir_census,'CA_block_2010.shp')
    shp_2010 = gpd.read_file(shp_file)

    geometry = [Point(xy) for xy in zip(shp_2010['INTPTLON10'].apply(float),shp_2010['INTPTLAT10'].apply(float))]
    crs = {'init':'epsg:4326'}
    shp_final = gpd.GeoDataFrame(shp_2010[['GISJOIN']],crs=crs,geometry=geometry)

    pop_blocks = shp_final.merge(san_diego_blocks,on='GISJOIN')

    if 'White' in races:
        pop_blocks['White'] = pop_blocks['H72003'] - pop_blocks['H7Z011']
    if 'Black' in races:
        pop_blocks['Black'] = pop_blocks['H72004'] - pop_blocks['H7Z012']
    if 'Asian' in races:
        pop_blocks['Asian'] = pop_blocks['H72006'] - pop_blocks['H7Z014']
    if 'Other' in races:
        pop_blocks['Other'] = pop_blocks['H72005'] + pop_blocks['H72007'] + pop_blocks['H72008'] - pop_blocks['H7Z013'] - pop_blocks['H7Z015'] - pop_blocks['H7Z016']
    if 'Hispanic' in races:
        pop_blocks['Hispanic'] = pop_blocks['H7Z011'] + pop_blocks['H7Z012'] + pop_blocks['H7Z014'] + pop_blocks['H7Z013'] +  pop_blocks['H7Z015'] + pop_blocks['H7Z016']

    final_pop = pop_blocks[list(races) + ['geometry']]

    return final_pop


# ---------------------------------------------------------------------
# Main Traffic Stops Cleaning Functions
# ---------------------------------------------------------------------

def clean_pre_ripa_data(cols_cfgs,**cfgs):

    final_columns, indir = cfgs['final_columns'], cfgs['indir']

    data_file = os.path.join(indir,'pre_ripa.csv')
    df = pd.read_csv(data_file)
    if df.empty:
        return df
    # rename columns so they match with Ripa data column names
    col_name_mapper = {**cols_cfgs['pre-ripa'],**cols_cfgs['pre-ripa_details'],**cols_cfgs['pre-ripa_races']}
    df.rename(col_name_mapper,inplace=True,axis=1)
    df.drop(['stop_id','race_code','subject_race_abbr'],inplace = True, axis=1)

    # func dict to apply corresponding functions to column in dict keys
    func_dict = {'stop_cause':clean_pr_stop_cause,'service_area':(lambda x: int(x) if x != 'Unknown' else np.nan),
                'subject_gender':(lambda x: 'Male' if x == 'M' else ('Female' if x == 'F' else 'X')),
                'subject_age':clean_pr_age, 'stop_datetime':pd.to_datetime,
                'arrested':clean_pr_arrested,'searched':clean_pr_searched,
                'subject_race':clean_pr_race}

    for col,func in func_dict.items():
        df[col] = df[col].apply(func)

    if 'property_seized' in df.columns:
        if 'searched' in df.columns:
            property_seized_list = []
            for s, p in zip(df['searched'], df['property_seized']):
                # if searched is nan, set property seized to nan
                if type(s) == float:
                    property_seized_list.append(np.nan)
                # if searched is no, set property seized to no
                elif s.lower() == 'n':
                    property_seized_list.append('N')
                elif s.lower() == 'y':
                    # if searched is yes and property seized is nan, set property seized to no
                    if type(p) == float:
                        property_seized_list.append('N')
                    # if property seized is yes or no, leave as that value
                    elif p.lower() in ['y','n']:
                        property_seized_list.append(p.upper())
                    else:
                        property_seized_list.append(np.nan)
                # all other conditions, set property seized to nan
                else:
                    property_seized_list.append(np.nan)
            df['property_seized'] = property_seized_list
        # no searched column, so apply cleaning function to map any values that aren't yes or no to nan
        else:
            df['property_seized'] = df['property_seized'] .apply(clean_pr_searched)

    if 'contraband' in df.columns:
        if 'searched' in df.columns:
            contraband_list = []
            for s, c in zip(df['searched'], df['contraband']):
                # if searched is nan, set contraband to nan
                if type(s) == float:
                    contraband_list.append(np.nan)
                # if searched is no, set contraband to no
                elif s.lower() == 'n':
                    contraband_list.append('N')
                elif s.lower() == 'y':
                    # if searched is yes and contraband is nan, set contraband to no
                    if type(c) == float:
                        contraband_list.append('N')
                    # if searched is yes and contraband is yes or no, leave contraband value as is
                    elif c.lower() in ['y','n']:
                        contraband_list.append(c.upper())
                    else:
                        contraband_list.append(np.nan)
                else:
                    contraband_list.append(np.nan)
            df['contraband'] = contraband_list
        # all other conditions, set property seized to nan
        else:
            df['contraband'] = df['contraband'].apply(lambda x: np.nan if (x == ' ') or (type(x)==float) else x.upper())

    # create citation information from search details description column
    if 'search_details_description' in df.columns:
        df['citation'] = df['search_details_description'].apply(lambda x: 'Y' if x == 'Citation' else ('N' if type(x) == str else np.NaN))
        df.drop('search_details_description',inplace=True,axis=1)

    if 'searched' in df.columns and 'arrested' in df.columns and 'property_seized' in df.columns and 'contraband' in df.columns:
        df['searched'] = df.apply(lambda x: 'Y' if (x['arrested'] == 'Y') or (x['property_seized'] == 'Y') or (x['contraband'] == 'Y') or (x['searched'] == 'Y') else x['searched'],axis=1)

    if 'property_seized' in df.columns and 'contraband' in df.columns:
        df['property_seized'] = df.apply(lambda x: 'Y' if (x['property_seized'] == 'Y') or (x['contraband'] == 'Y') else x['property_seized'],axis=1)

    # get final columns so that concationation with Ripa data works properly
    final_cols = list(set(df.columns).intersection(set(final_columns)))

    return df[final_cols]


def clean_ripa_data(cols_cfgs,**cfgs):

    final_columns, indir = cfgs['final_columns'], cfgs['indir']

    data_file = os.path.join(indir,'ripa.csv')

    # if date time information is provided, parse date_stop and time_stop into a datetime column
    try:
        df = pd.read_csv(data_file,parse_dates=[['date_stop','time_stop']])
    except:
        df = pd.read_csv(data_file)

    if df.empty:
        return df

    # rename columns so they match with Pre-Ripa data column names
    col_name_mapper = {}
    for dataset, dict_ in cols_cfgs.items():
        if 'pre' not in dataset:
            col_name_mapper.update(dict_)
    df.rename(col_name_mapper,inplace=True,axis=1)

    # func dict to apply corresponding functions to column in dict keys
    func_dict = {'subject_age':clean_r_age,'subject_gender':(lambda x: 'Male' if x == 'M' else ('Female' if x == 'F' else 'X')),
                'subject_race':clean_r_race,'contraband':lambda x: 'N' if x == 'None' else 'Y',
                'stop_cause':clean_r_stop_cause}

    for col,func in func_dict.items():
        df[col] = df[col].apply(func)

    # create service area from beat column
    if 'beat' in df.columns:
        df['service_area'] = df['beat'].apply(lambda x: (x//10)*10)

    # create searched and property seized from action column
    if 'action' in df.columns:
        df['searched'] = df['action'].apply(create_r_searched)
        df['property_seized'] = df['action'].apply(create_r_property_seized)

    # create citation and arrested from result column
    if 'result' in df.columns:
        df['citation'] = df['result'].apply(create_r_citation)
        df['arrested'] = df['result'].apply(create_r_arrested)

    if 'searched' in df.columns and 'arrested' in df.columns and 'property_seized' in df.columns and 'contraband' in df.columns:
        df['searched'] = df.apply(lambda x: 'Y' if (x['arrested'] == 'Y') or (x['property_seized'] == 'Y') or (x['contraband'] == 'Y') or (x['searched'] == 'Y') else x['searched'],axis=1)

    if 'property_seized' in df.columns and 'contraband' in df.columns:
        df['property_seized'] = df.apply(lambda x: 'Y' if (x['property_seized'] == 'Y') or (x['contraband'] == 'Y') else x['property_seized'],axis=1)

    final_cols = list(set(df.columns).intersection(set(final_columns)))

    return df[final_cols]

def population_service_area(census,service_area, **cfgs):

    outdir = cfgs['outdir']
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    pop_cols = list(census.columns)
    pop_cols.remove('geometry')
    pop_cols.append('service_area')

    pop_sa = gpd.sjoin(census,service_area,op='within')[pop_cols]
    gb_pop_sa = pop_sa.groupby('service_area').sum()
    outpath = os.path.join(outdir,'cleaned_population_data.csv')

    gb_pop_sa.to_csv(outpath)


def combined_cleaned_data(pre_ripa,ripa,**cfgs):

    outdir = cfgs['outdir']

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    outpath = os.path.join(outdir,'cleaned_stops.csv')
    combined = pd.concat([pre_ripa,ripa]).reset_index(drop=True)

    combined.to_csv(outpath,index=False)
