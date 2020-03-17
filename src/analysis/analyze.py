import pandas as pd
import numpy as np
import os
from itertools import combinations
from scipy import stats
from datetime import time

def stop_rates_by_service_area(stops,race_census,outdir,p_val):

    races = list(stops['subject_race'].unique())
    valid_stops = stops[stops['stop_cause'].isin(['Moving Violation','Equiptment Violation'])]
    stop_counts = valid_stops.groupby(['subject_race','service_area']).count().max(axis=1)

    race_census_dict = {}
    for num,row  in race_census.iterrows():
        service_area = row.iloc[0]
        serv_area_dict = {}
        for race, count in row.iloc[1:].iteritems():
            serv_area_dict[race] = count
        race_census_dict[service_area] = serv_area_dict

    stop_rates_df = pd.DataFrame(columns = race_census['service_area'],index=races)
    for (race,service_area),count in stop_counts.iteritems():
        if service_area in race_census_dict.keys():
            stop_rate =  count / race_census_dict[service_area][race]
            stop_rates_df.set_value(race, service_area,stop_rate)

    num_years = len(stops.stop_datetime.dropna().apply(lambda x: x.year).unique())
    stop_rates = (stop_rates_df / num_years).dropna(axis=1)

    stop_rates_outpath = os.path.join(outdir,'stop_rates_by_service_area.csv')
    stop_rates.to_csv(stop_rates_outpath)

    stop_rates_analysis_outpath = os.path.join(outdir,'stop_rates_by_service_area_analysis.txt')

    with open(stop_rates_analysis_outpath,'w+') as f:
        for r1, r2 in combinations(stop_rates.index,2):
            greater_p_val = round(stats.ks_2samp(stop_rates.loc[r1],stop_rates.loc[r2],alternative='greater')[1],3)
            lesser_p_val = round(stats.ks_2samp(stop_rates.loc[r1],stop_rates.loc[r2],alternative='less')[1],3)
            two_sided_p_val = round(stats.ks_2samp(stop_rates.loc[r1],stop_rates.loc[r2])[1],3)
            if greater_p_val < p_val:
                line1 = 'The p-value of the one-sided greater than KS test between stop rates of drivers classified as {} and the stop rates of drivers classified as {} is: {} when calculated across service areas. '.format(r1,r2,greater_p_val)
                line2 = 'This p-value is statistically significant at a 95% confidence level. '
                line3 = 'There is evidence that drivers classified as {} have higher stop rates than drivers classified as {} when calculated across service areas. \n'.format(r2,r1)
            elif lesser_p_val < p_val:
                line1 = 'The p-value of the one-sided greater than KS test between stop rates of drivers classified as {} and the stop rates of drivers classified as {} is: {} when calculated across service areas. '.format(r2,r1,lesser_p_val)
                line2 = 'This p-value is statistically significant at a 95% confidence level. '
                line3 = 'There is evidence that drivers classified as {} have higher stop rates than drivers classified as {} when calculated across service areas. \n'.format(r1,r2)
            else:
                line1 = 'The p-value of the two-sided KS test between stop rates of drivers classified as {} and the stop rates of drivers classified as {} is: {} when calculated across service areas. '.format(r1,r2,two_sided_p_val)
                line2 = 'This p-value is statistically significant at a 95% confidence level. '
                line3 = 'There is no evidence drivers classified as {} and drivers classified as {} have different stop rates when calculated across service areas. \n'.format(r1,r2)
            lines = [line1,line2,line3]
            f.writelines(lines)

    f.close()

def stop_rates_by_stop_cause(stops,race_census,outdir,p_val):

    races = list(stops['subject_race'].unique())
    race_census_dict = {}
    for num,row  in race_census.iterrows():
        service_area = row.iloc[0]
        serv_area_dict = {}
        for race, count in row.iloc[1:].iteritems():
            serv_area_dict[race] = count
        race_census_dict[service_area] = serv_area_dict
    stop_causes = list(stops.stop_cause.dropna().unique())
    m_index = pd.MultiIndex.from_product([races,stop_causes])

    stop_counts = stops.groupby(['subject_race','stop_cause','service_area']).count().max(axis=1)
    stop_rates_df = pd.DataFrame(columns = race_census['service_area'],index=m_index)
    for (race,violation,service_area),count in stop_counts.iteritems():
        if service_area in race_census_dict.keys():
            stop_rate =  count / race_census_dict[service_area][race]
            stop_rates_df.loc[race,violation][service_area] = stop_rate

    stop_rates_violation = stop_rates_df.dropna(axis=1,how='all').fillna(0)

    stop_rates_violation_outpath = os.path.join(outdir,'stop_rates_by_service_area_violation.csv')
    stop_rates_violation.to_csv(stop_rates_violation_outpath)

    stop_rates_violation_analysis_outpath = os.path.join(outdir,'stop_rates_by_service_area_violation_analysis.txt')

    with open(stop_rates_violation_analysis_outpath,'w+') as f:
        for s1,s2 in combinations(stop_rates_violation.index,2):
            r1, r2 = list(s1), list(s2)
            if r1[1] == r2[1]:
                greater_p_val = round(stats.ks_2samp(stop_rates_violation.loc[s1],stop_rates_violation.loc[s2],alternative='greater')[1],3)
                lesser_p_val = round(stats.ks_2samp(stop_rates_violation.loc[s1],stop_rates_violation.loc[s2],alternative='less')[1],3)
                two_sided_p_val = round(stats.ks_2samp(stop_rates_violation.loc[s1],stop_rates_violation.loc[s2])[1],3)
                if r1[1] == 'Other':
                    r1[1] = 'Other Violation'
                if r2[1] == 'Other':
                    r2[1] = 'Other Violation'
                if greater_p_val < p_val:
                    line1 = 'The p-value of the one-sided greater than KS test between stop rates of drivers classified as {} for {}s and the stop rates of drivers classified as {} for {}s is: {} when calculated across service areas. '.format(r1[0],r1[1],r2[0],r2[1],greater_p_val)
                    line2 = 'This p-value is statistically significant at a 95% confidence level. '
                    line3 = 'There is evidence that drivers classified as {} have higher stop rates for {}s than drivers classified as {} when calculated across service areas. \n'.format(r2[0],r2[1],r1[0])
                elif lesser_p_val < p_val:
                    line1 = 'The p-value of the one-sided greater than KS test between stop rates of drivers classified as {} for {}s and the stop rates of drivers classified as {} for {}s is: {} when calculated across service areas. '.format(r2[0],r2[1],r1[0],r2[1],lesser_p_val)
                    line2 = 'This p-value is statistically significant at a 95% confidence level. '
                    line3 = 'There is evidence that drivers classified as {} have higher stop rates for {}s than drivers classified as {} when calculated across service areas. \n'.format(r1[0],r1[0],r2[1])
                else:
                    line1 = 'The p-value of the two-sided KS test between stop rates of drivers classified as {} for {}s and the stop rates of drivers classified as {} for {} is: {} when calculated across service areas. '.format(r1[0],r1[1],r2[0],r2[1],two_sided_p_val)
                    line2 = 'This p-value is statistically significant at a 95% confidence level. '
                    line3 = 'There is no evidence drivers classified as {} and drivers classified as {} have different stop rates for {}s when calculated across service areas. \n'.format(r1[0],r2[0],r1[1])

                lines = [line1,line2,line3]
                f.writelines(lines)
    f.close()

def stop_rates_by_service_area_year(stops,race_census,outdir,p_val):

    races = list(stops['subject_race'].unique())
    stops['year'] = stops['stop_datetime'].apply(lambda x:x.year if type(x)!= float else x)
    valid_stops = stops[stops['stop_cause'].isin(['Moving Violation','Equiptment Violation'])]
    stop_counts = valid_stops.groupby(['subject_race','service_area','year']).count().max(axis=1)

    race_census_dict = {}
    for num,row  in race_census.iterrows():
        service_area = row.iloc[0]
        serv_area_dict = {}
        for race, count in row.iloc[1:].iteritems():
            serv_area_dict[race] = count
        race_census_dict[service_area] = serv_area_dict

    years = stops['year'].dropna().unique()
    m_index = pd.MultiIndex.from_product([races,years])

    stop_rates_df = pd.DataFrame(columns = race_census['service_area'],index=m_index)
    for (race,service_area,year),count in stop_counts.iteritems():
        if service_area in race_census_dict.keys():
            stop_rate =  count / race_census_dict[service_area][race]
            stop_rates_df.loc[race,year][service_area] = stop_rate

    num_years = len(years)
    stop_rates = (stop_rates_df / num_years).dropna(axis=1)

    stop_rates_outpath = os.path.join(outdir,'stop_rates_by_service_area_year.csv')
    stop_rates.to_csv(stop_rates_outpath)

    stop_rates_analysis_outpath = os.path.join(outdir,'stop_rates_by_service_area_year_analysis.txt')

    with open(stop_rates_analysis_outpath,'w+') as f:
        for r1, r2 in combinations(stop_rates.index,2):
            if r1[1] == r2[1]:
                greater_p_val = round(stats.ks_2samp(stop_rates.loc[r1],stop_rates.loc[r2],alternative='greater')[1],3)
                lesser_p_val = round(stats.ks_2samp(stop_rates.loc[r1],stop_rates.loc[r2],alternative='less')[1],3)
                two_sided_p_val = round(stats.ks_2samp(stop_rates.loc[r1],stop_rates.loc[r2])[1],3)
                if greater_p_val < p_val:
                    line1 = 'The p-value of the one-sided greater than KS test between stop rates of drivers classified as {} for {} and the stop rates of drivers classified as {} for {} is: {} when calculated across service areas. '.format(r1[0],r1[1],r2[0],r2[1],greater_p_val)
                    line2 = 'This p-value is statistically significant at a 95% confidence level. '
                    line3 = 'There is evidence that drivers classified as {} have higher stop rates for {} than drivers classified as {} when calculated across service areas and stop cause. \n'.format(r2[0],r2[1],r1[0])
                elif lesser_p_val < p_val:
                    line1 = 'The p-value of the one-sided greater than KS test between stop rates of drivers classified as {} for {} and the stop rates of drivers classified as {} for {} is: {} when calculated across service areas. '.format(r2[0],r2[1],r1[0],r2[1],lesser_p_val)
                    line2 = 'This p-value is statistically significant at a 95% confidence level. '
                    line3 = 'There is evidence that drivers classified as {} have higher stop rates for {} than drivers classified as {} when calculated across service areas. \n'.format(r1[0],r1[0],r2[1])
                else:
                    line1 = 'The p-value of the two-sided KS test between stop rates of drivers classified as {} for {} and the stop rates of drivers classified as {} for {} is: {} when calculated across service areas. '.format(r1[0],r1[1],r2[0],r2[1],two_sided_p_val)
                    line2 = 'This p-value is statistically significant at a 95% confidence level. '
                    line3 = 'There is no evidence drivers classified as {} and drivers classified as {} have different stop rates for {} when calculated across service areas. \n'.format(r1[0],r2[0],r1[1])

                lines = [line1,line2,line3]
                f.writelines(lines)
    f.close()



def stop_rate_analysis(**cfgs):

    indir, outdir, confidence = cfgs.values()

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    p_val = (100 - int(confidence.strip('%'))) / 100

    stops_file = os.path.join(indir,'cleaned_stops.csv')
    census_file = os.path.join(indir,'cleaned_population_data.csv')

    try:
        stops = pd.read_csv(stops_file,parse_dates=['stop_datetime'])
    except:
        stops = pd.read_csv(stops_file)

    census = pd.read_csv(census_file)
    races = list(stops['subject_race'].unique())
    race_census = census[['service_area'] + races]

    stop_rates_by_service_area(stops,race_census,outdir,p_val)
    stop_rates_by_stop_cause(stops,race_census,outdir,p_val)
    stop_rates_by_service_area_year(stops,race_census,outdir,p_val)

def permutation_analysis_arrest_rates(valid_stops, post_stop_analysis_outpath):

    stops = valid_stops[['subject_race','arrested']]

    actual_val = valid_stops[valid_stops['subject_race'] == 'Black']['arrested'].value_counts(normalize=True)['Y']

    greater_than = 0

    num_trials = 100

    for _ in range(num_trials):

        stops_c = stops.copy()

        stops_c['subject_race'] = stops_c['subject_race'].sample(frac=1)

        val = stops_c[stops_c['subject_race'] == 'Black']['arrested'].value_counts(normalize=True)['Y']

        if val > actual_val:
            print(val)
            greater_than += 1

    percent = (greater_than / num_trials) * 100

    with open(post_stop_analysis_outpath,'w+') as f:
        result = 'In {} permutations, {}% of the permutations had arrest rates greater than the actual arrest rate for drivers cateogrized as Black'.format(num_trials,percent)
        f.writelines([result])
    f.close()

def permutation_analysis_arrest_year_rates(valid_stops, post_stop_analysis_outpath):

    stops = valid_stops[['subject_race','arrested']]

    actual_val = valid_stops[valid_stops['subject_race'] == 'Black']['arrested'].value_counts(normalize=True)['Y']

    greater_than = 0

    num_trials = 100

    for _ in range(num_trials):

        stops_c = stops.copy()

        stops_c['subject_race'] = stops_c['subject_race'].sample(frac=1)

        val = stops_c[stops_c['subject_race'] == 'Black']['arrested'].value_counts(normalize=True)['Y']

        if val > actual_val:
            print(val)
            greater_than += 1

    percent = (greater_than / num_trials) * 100

    with open(post_stop_analysis_outpath,'w+') as f:
        result = 'In {} permutations, {}% of the permutations had arrest rates greater than the actual arrest rate for drivers cateogrized as Black for all years'.format(num_trials,percent)
        f.writelines([result])
    f.close()

def post_stop_outcome_analysis(valid_stops,outdir):

    number_of_stops_race = valid_stops.groupby('subject_race').count().max(axis=1)
    stop_count_dict = number_of_stops_race.to_dict()
    post_stop_outcomes = valid_stops.groupby('subject_race').agg({'citation':lambda x: sum(x == 'Y'),'arrested':lambda x: sum(x == 'Y'),'searched':lambda x: sum(x == 'Y'),'property_seized':lambda x: sum(x == 'Y'),'contraband':lambda x: sum(x == 'Y')})

    rates_df = pd.DataFrame(index=list(valid_stops['subject_race'].unique()),columns= post_stop_outcomes.columns)

    for race, row in post_stop_outcomes.iterrows():
        total_stops = stop_count_dict[race]
        for outcome in rates_df.columns:
            rate = row[outcome] / total_stops
            rates_df.loc[race,outcome] = rate

    rates_df.columns = [x + '_rate' for x in rates_df.columns]

    post_stop_rates_path = os.path.join(outdir,'post_stop_outcome_rates.csv')
    rates_df.to_csv(post_stop_rates_path)

    post_stop_analysis_outpath = os.path.join(outdir,'poststop_outcome_rates_analysis.txt')

    permutation_analysis_arrest_rates(valid_stops, post_stop_analysis_outpath)


def post_stop_outcome_analysis_year(valid_stops,outdir):

    valid_stops['year'] = valid_stops['stop_datetime'].apply(lambda x:x.year if type(x)!= float else x)
    number_of_stops_race = valid_stops.groupby(['subject_race','year']).count().max(axis=1)
    stop_count_dict = number_of_stops_race.to_dict()
    post_stop_outcomes = valid_stops.groupby(['subject_race','year']).agg({'citation':lambda x: sum(x == 'Y'),'arrested':lambda x: sum(x == 'Y'),'searched':lambda x: sum(x == 'Y'),'property_seized':lambda x: sum(x == 'Y'),'contraband':lambda x: sum(x == 'Y')})

    rates_df = post_stop_outcomes.div(number_of_stops_race.values,axis=0)

    rates_df.columns = [x + '_rate' for x in rates_df.columns]

    post_stop_rates_path = os.path.join(outdir,'post_stop_outcome_rates_year.csv')
    rates_df.to_csv(post_stop_rates_path)

    post_stop_analysis_outpath = os.path.join(outdir,'poststop_outcome_rates_year_analysis.txt')

    permutation_analysis_arrest_year_rates(valid_stops, post_stop_analysis_outpath)


def post_stop_analysis(**cfgs):

    indir, outdir, confidence = cfgs.values()

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    p_val = (100 - int(confidence.strip('%'))) / 100
    stops_file = os.path.join(indir,'cleaned_stops.csv')

    try:
        stops = pd.read_csv(stops_file,parse_dates=['stop_datetime'])
    except:
        stops = pd.read_csv(stops_file)

    valid_stops = stops[stops['stop_cause'].isin(['Moving Violation','Equiptment Violation'])]

    post_stop_outcome_analysis(valid_stops,outdir)
    post_stop_outcome_analysis_year(valid_stops,outdir)

def veil_of_darkness_race(valid_stops,outdir):

    valid_stops = valid_stops[valid_stops['stop_datetime'].apply(lambda x: time(17,9) < x.time() < time(20,29) if not pd.isna(x) else False)]
    valid_stops['month'] = valid_stops['stop_datetime'].apply(lambda x: x.month if type(x)!=float else x)
    valid_stops['days'] = valid_stops['stop_datetime'].apply(lambda x: x.day if type(x)!=float else x)

    times = pd.read_csv('data/census/twilight_times.csv',index_col=0)

    darkness = []
    lightness = []
    for num, row in valid_stops.iterrows():
        sunset_time = times[str(row['month'])][row['days']]
        if row['stop_datetime'].time()> pd.to_datetime(sunset_time).time():
            darkness.append(row)
        else:
            lightness.append(row)

    dark_df = pd.DataFrame(darkness)
    light_df = pd.DataFrame(lightness)

    light_stop_rates = light_df.subject_race.value_counts(normalize=True).sort_index()
    dark_stop_rates = dark_df.subject_race.value_counts(normalize=True).sort_index()

    vod_df = pd.DataFrame([light_stop_rates,dark_stop_rates],index=['Light','Dark'])

    vod_path = os.path.join(outdir,'veil_of_darkness_race.csv')

    vod_df.to_csv(vod_path)


def veil_of_darkness_analysis(**cfgs):

    indir, outdir, confidence = cfgs.values()

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    p_val = (100 - int(confidence.strip('%'))) / 100
    stops_file = os.path.join(indir,'cleaned_stops.csv')

    try:
        stops = pd.read_csv(stops_file,parse_dates=['stop_datetime'])
    except:
        stops = pd.read_csv(stops_file)

    valid_stops = stops[stops['stop_cause'].isin(['Moving Violation','Equiptment Violation'])]

    veil_of_darkness_race(valid_stops,outdir)
