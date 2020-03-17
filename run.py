import json
import shutil
import sys


sys.path.insert(0, 'src') # add library code to path
from data.get_data import get_stops_data
from process.clean_data import clean_pre_ripa_data, clean_ripa_data, clean_census_data
from process.clean_data import combined_cleaned_data, clean_service_area_data, population_service_area
from analysis.analyze import stop_rate_analysis, post_stop_analysis, veil_of_darkness_analysis

def load_params(fp):
    with open(fp) as fh:
        param = json.load(fh)
    return param

DATA_PARAMS = 'config/01-data-params.json'
CLEAN_PARAMS = 'config/02-clean-params.json'
ANALYZE_PARAMS = 'config/03-analyze-params.json'

TEST_DATA_PARAMS = 'config/test-01-data-params.json'
TEST_CLEAN_PARAMS = 'config/test-02-clean-params.json'
TEST_ANALYZE_PARAMS = 'config/test-03-analyze-params.json'
COLUMN_MAPPER_PARAMS = 'config/columns_mapper.json'


def main(targets):

    if 'project' in targets:

        shutil.rmtree('data/raw', ignore_errors=True)
        shutil.rmtree('data/cleaned', ignore_errors=True)
        shutil.rmtree('data/out', ignore_errors=True)

        data_cfgs = load_params(DATA_PARAMS)
        clean_cfgs = load_params(CLEAN_PARAMS)
        analyze_cfgs = load_params(ANALYZE_PARAMS)
        cols_cfgs = load_params(COLUMN_MAPPER_PARAMS)

        get_stops_data(cols_cfgs, **data_cfgs)

        pre_ripa = clean_pre_ripa_data(cols_cfgs,**clean_cfgs)
        ripa = clean_ripa_data(cols_cfgs,**clean_cfgs)
        combined_cleaned_data(pre_ripa,ripa,**clean_cfgs)

        service_area = clean_service_area_data(**clean_cfgs)
        census = clean_census_data(**clean_cfgs)
        population_service_area(census,service_area, **clean_cfgs)

        stop_rate_analysis(**analyze_cfgs)
        post_stop_analysis(**analyze_cfgs)
        veil_of_darkness_analysis(**analyze_cfgs)


    if 'test-project' in targets:

        shutil.rmtree('data/test/raw', ignore_errors=True)
        shutil.rmtree('data/test/cleaned', ignore_errors=True)
        shutil.rmtree('data/test/out', ignore_errors=True)


        data_cfgs = load_params(TEST_DATA_PARAMS)
        clean_cfgs = load_params(TEST_CLEAN_PARAMS)
        analyze_cfgs = load_params(TEST_ANALYZE_PARAMS)
        cols_cfgs = load_params(COLUMN_MAPPER_PARAMS)

        get_stops_data(cols_cfgs, **data_cfgs)

        pre_ripa = clean_pre_ripa_data(cols_cfgs,**clean_cfgs)
        ripa = clean_ripa_data(cols_cfgs,**clean_cfgs)
        combined_cleaned_data(pre_ripa,ripa,**clean_cfgs)

        service_area = clean_service_area_data(**clean_cfgs)
        census = clean_census_data(**clean_cfgs)
        population_service_area(census,service_area, **clean_cfgs)

        stop_rate_analysis(**analyze_cfgs)
        post_stop_analysis(**analyze_cfgs)
        veil_of_darkness_analysis(**analyze_cfgs)


if __name__ == '__main__':
    targets = sys.argv[1:]
    main(targets)
