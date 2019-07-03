import xarray as xr
from collections import defaultdict
import csv
import glob
import os

CSV_DELIMETER = "    "
CSV_EOL = "\n"
CSV_FLOAT_FORMAT = '.10f'

def process_netcdf_file(fin, fout, **kwargs):
    print(">>> kwargs to process:")
    for key, value in kwargs.items():
        print("{0} = {1}".format(key, value)) 

    # Check all neccessary kwargs
    if "latitude" not in kwargs:
        raise KeyError("Latitude dimension doesn't exists in kwargs. Please check your args")
    if "longitude" not in kwargs:
        raise KeyError("Longitude dimension doesn't exists in kwargs. Please check your args")
    if "data" not in kwargs:
        raise KeyError("You didn't provide name of data_var. Please check your args - add <data> if it doesn't exist")

    # Open netCDF file
    ds = xr.open_dataset(fin)

    # netCDF data set has
    # - coords - coordinates - lat, long, time, level dimenstions
    # - data_vars - data for coordinates - temperature, pressure and so on
    # You can check it by following expression
    #print(ds.coords)
    #print(ds.data_vars)

    print("<{}> contains from the following data_var:".format(fin))
    print(ds.data_vars)

    # Check all neccessary dimensions inside netCDF file
    if "latitude" not in ds.coords:
        print("Available coods")
        print(ds.coords)
        raise KeyError("Latitude dimension doesn't exists in Dataset coordinates. Please check your file {}".format(fin))
    if "longitude" not in ds.coords:
        print("Available coods")
        print(ds.coords)
        raise KeyError("Longitude dimension doesn't exists in Dataset coordinates. Please check your file{}".format(fin))
    if "time" not in ds.coords:
        print("Available coods")
        print(ds.coords)
        raise KeyError("Time dimension doesn't exists in Dataset coordinates. Please check your file {}".format(fin))

    # Create dedicated variables for lats and longs
    lats = kwargs["latitude"]
    lons = kwargs["longitude"]

    # We should use longitude coordinates from -180 to 180
    # But some netCDF files used 0 to 360.
    # So we just shift coordinates exaclty to -180 to 180
    start_longitude = ds.coords["longitude"].data[0]
    shift_longitude = 0
    if start_longitude == 0.0:
        shift_longitude = 180.0
        lons = list(map(lambda coord: coord+shift_longitude, lons))

    # Check that own lats and lons exist inside netCDF file
    if not set(lats).issubset(set(ds.coords["latitude"].data)):
        raise ValueError("Your latitude '{}' doesn't exist in dataset latitude dimenstion. Please check your args".format(lats))
    if not set(lons).issubset(set(ds.coords["longitude"].data)):
        raise ValueError("Your longitude '{}' doesn't exist in dataset longitude dimenstion. Please check your args".format(lons))
    if kwargs["data"] not in ds.data_vars:
        raise KeyError("Interested data var <{}> doesn't exist in dataset. Please check your main() function or file".format(kwargs["data"]))
    
    # Check additional dimensions like 'level'
    if ("level" in ds.coords) and ("level" not in kwargs):
        raise KeyError("Target file has LEVEL coords but you didn't provide it. Please check your args")
    if ("level" in ds.coords) and (not set(kwargs["level"]).issubset(ds.coords["level"].data)):
        raise ValueError("Your level '{}' doesn't exist in dataset level dimenstion. Please check your args".format(kwargs["level"]))
 
    # Select data by time with constant lat, long and level if it exists and write it to corresponding file
    dsloc = None
    resulting_list = list()

    if ("level" not in ds.coords):
        for lat in lats:
            for lon in lons:
                dsloc = ds.sel(latitude=lat, longitude=lon)
                time_list = list(map(lambda val: str(val), dsloc['time'].data))
                data_list = list(map(lambda val: format(val, CSV_FLOAT_FORMAT), dsloc[kwargs['data']].data))
                resulting_list.extend(pack_data_to_list(time_list, data_list, lat=lat, lon=lon-shift_longitude))
    else:
        for lat in lats:
            for lon in lons:
                for lev in kwargs['level']:
                    dsloc = ds.sel(latitude=lat, longitude=lon, level=lev)
                    time_list = list(map(lambda val: str(val), dsloc['time'].data))
                    data_list = list(map(lambda val: format(val, CSV_FLOAT_FORMAT), dsloc[kwargs['data']].data))
                    resulting_list.extend(pack_data_to_list(time_list, data_list, lat=lat, lon=lon-shift_longitude, lev=lev))

    save_all_to_csv_files_by_date(fout, resulting_list)

def pack_data_to_list(*args, **kwargs):
    out_list = list()

    if len(args) > 0:
        list_len = len(args[0])
        for i in range(list_len):
            inner_list = list()
            for arg in args:
                inner_list.append(arg[i])
            for _, value in kwargs.items():
                inner_list.append(value)
            out_list.append(inner_list)
    
    return out_list

def save_all_to_csv_file(fout, data_list):
    with open(fout, 'a') as file:
        for line in data_list:
            # When we use CSV we can't use delimeter with several chars
            # So in this case we use "bare-metal" write
            out_string = ''
            for idx, val in enumerate(line):
                if idx != 0:
                    out_string += CSV_DELIMETER
                out_string += str(val)

            out_string += CSV_EOL

            file.write(out_string)

def separate_data_by_date(data_list):
    # we got all data in list of lists
    # we should separate all data by date
    data_by_date = defaultdict(list)

    for data in data_list:
        data_by_date[data[0]].append(data)
    
    return data_by_date

def save_all_to_csv_files_by_date(fout, data_list):
    data_dict_by_date = defaultdict()
    data_dict_by_date = separate_data_by_date(data_list)

    for key, value_list in data_dict_by_date.items():
        output_file = fout[:fout.rfind('.')] + '_' + key[:key.find(':')] + fout[fout.rfind('.'):]

        with open(output_file, 'a') as file:
            for data in value_list:
                # When we use CSV we can't use delimeter with several chars
                # So in this case we use "bare-metal" write
                out_string = ''
                for idx, val in enumerate(data):
                    if idx != 0:
                        out_string += CSV_DELIMETER
                    out_string += str(val)

                out_string += CSV_EOL

                file.write(out_string)

def get_out_file_name(file_path, **kwargs):
    result = ""

    # Get only file name
    result = os.path.basename(file_path)

    # Truncate extension
    result = result[: result.rfind(".")]

    # Append data from kwargs
    result += '_' + kwargs['data']
    result += '_' + str(kwargs['level'][0])

    # Append extenstion
    result += ".dat"

    return result

def process_all_files_in_folder(in_folder, out_folder, **kwargs):
    for file_path in glob.glob(in_folder + "/" + "*.nc"):
        out_file_name = get_out_file_name(file_path, **kwargs)
        print(" >>> Process file '{}' with output name '{}'".format(file_path, out_file_name))
        process_netcdf_file(file_path, out_folder + "/" + out_file_name, **kwargs)
        print("")
        print(" >>> file '{}' with output name '{}' was processed".format(file_path, out_file_name))
        print("")

def main():
    params = {
        # latitude from 90.0 to -90.0 with step 0.75
        "latitude": [0.0], 
        # longitude from -180.0 to 179.25 with step 0.75         
        "longitude": [0.0],
        # level if exist for this type of the netCDF data. If not exist - please comment it
        "level": [1],
        # interested data - please provide name of variable
        "data": "sp"
    }
    process_all_files_in_folder("./input", "./output", **params)
    print('Script is finished')

if __name__ == "__main__":
    main()