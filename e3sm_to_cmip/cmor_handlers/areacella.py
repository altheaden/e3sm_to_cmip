"""
LANDFRAC to sftlf converter
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import cmor
import os
import logging
import json
from tqdm import tqdm
import xarray as xr
import numpy as np
from e3sm_to_cmip import resources
from e3sm_to_cmip.util import print_message
from e3sm_to_cmip.lib import handle_variables
from e3sm_to_cmip.mpas import write_netcdf

# list of raw variable names needed
RAW_VARIABLES = [str('area')]
VAR_NAME = str('areacella')
VAR_UNITS = str('m2')
TABLE = str('CMIP6_fx.json')
RADIUS = 6.37122e6


def handle_simple(infiles):
    resource_path, _ = os.path.split(os.path.abspath(resources.__file__))
    table_path = os.path.join(resource_path, TABLE)
    with open(table_path, 'r') as ip:
        table_data = json.load(ip)

    ds = xr.Dataset()
    outname = f'{VAR_NAME}_fx.nc'
    with xr.open_dataset(infiles[RAW_VARIABLES[0]][0]) as inputds:

        ds['lat'] = inputds['lat']
        ds['lat_bnds'] = inputds['lat_bnds']
        ds['lon'] = inputds['lon']
        ds['lon_bnds'] = inputds['lon_bnds']
        outdata = inputds['area'] * pow(RADIUS, 2)

        for attr, val in inputds.attrs.items():
            ds.attrs[attr] = val

    ds[VAR_NAME] = outdata
    for attr in ['standard_name', 'cell_methods', 'long_name', 'comment', 'units']:
        ds[VAR_NAME].attrs[attr] = table_data["variable_entry"][VAR_NAME][attr]

    fillVals = {
        np.dtype('float32'): 1e20,
        np.dtype('float64'): 1e20,
    }
    write_netcdf(ds, outname, fillValues=fillVals, unlimited=['time'])


def handle(infiles, tables, user_input_path, **kwargs):

    simple = kwargs.get('simple')

    logger = logging.getLogger()
    msg = '{}: Starting'.format(VAR_NAME)
    logger.info(msg)

    # check that we have some input files for every variable
    zerofiles = False
    for variable in RAW_VARIABLES:
        if len(infiles[variable]) == 0:
            msg = '{}: Unable to find input files for {}'.format(
                VAR_NAME, variable)
            print_message(msg)
            logging.error(msg)
            zerofiles = True
    if zerofiles:
        return None

    if simple:
        handle_simple(infiles)
        return VAR_NAME

    # Create the logging directory and setup cmor
    logdir = kwargs.get('logdir')
    if logdir:
        logpath = logdir
    else:
        outpath, _ = os.path.split(logger.__dict__['handlers'][0].baseFilename)
        logpath = os.path.join(outpath, 'cmor_logs')
    os.makedirs(logpath, exist_ok=True)

    logfile = os.path.join(logpath, VAR_NAME + '.log')

    cmor.setup(
        inpath=tables,
        netcdf_file_action=cmor.CMOR_REPLACE,
        logfile=logfile)

    cmor.dataset_json(str(user_input_path))
    cmor.load_table(str(TABLE))

    msg = '{}: CMOR setup complete'.format(VAR_NAME)
    logging.info(msg)

    # extract data from the input file
    msg = 'areacella: loading area'
    logger.info(msg)

    filename = infiles['area'][0]

    if not os.path.exists(filename):
        raise IOError("File not found: {}".format(filename))

    ds = xr.open_dataset(filename, decode_times=False)

    # load the lon and lat info & bounds
    data = {
        'lat': ds['lat'],
        'lon': ds['lon'],
        'lat_bnds': ds['lat_bnds'],
        'lon_bnds': ds['lon_bnds'],
        'area': ds['area']
    }

    msg = '{name}: loading axes'.format(name=VAR_NAME)
    logger.info(msg)

    axes = [{
        str('table_entry'): str('latitude'),
        str('units'): data['lat'].units,
        str('coord_vals'): data['lat'].values,
        str('cell_bounds'): data['lat_bnds'].values
    }, {
        str('table_entry'): str('longitude'),
        str('units'): data['lon'].units,
        str('coord_vals'): data['lon'].values,
        str('cell_bounds'): data['lon_bnds'].values
    }]

    msg = 'areacella: running CMOR'
    logging.info(msg)

    axis_ids = list()
    for axis in axes:
        axis_id = cmor.axis(**axis)
        axis_ids.append(axis_id)

    varid = cmor.variable(VAR_NAME, VAR_UNITS, axis_ids)

    outdata = data['area'].values * pow(RADIUS, 2)
    cmor.write(
        varid,
        outdata)

    msg = '{}: write complete, closing'.format(VAR_NAME)
    logger.debug(msg)

    cmor.close()

    msg = '{}: file close complete'.format(VAR_NAME)
    logger.debug(msg)

    return 'areacella'
