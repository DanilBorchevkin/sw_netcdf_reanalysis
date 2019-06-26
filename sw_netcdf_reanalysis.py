import xarray as xr
import csv
import glob
import os

CSV_DELIMETER = "    "
CSV_EOL = "\n"

def process_netcdf_file(fin, fout, **kwargs):
    print(">>> kwargs to process:")
    for key, value in kwargs.items():
        print("{0} = {1}".format(key, value))   

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

    # Check all neccessary dimensions
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

    # We should use coordinates from -180 to 180
    # But some netCDF files used 0 to 360.
    # So we just shift coordinates exaclty to -180 to 180
    start_longitude = ds.coords["longitude"].data[0]
    shift_longitude = 0
    if start_longitude == 0.0:
        shift_longitude = -180.0
        kwargs['longitude'] = list(map(lambda coord: coord-shift_longitude, kwargs['longitude']))

    # Check all neccessary kwargs
    if "latitude" not in kwargs:
        raise KeyError("Latitude dimension doesn't exists in kwargs. Please check your args")
    if kwargs["latitude"] not in ds.coords["latitude"].data:
        raise ValueError("Your latitude '{}' doesn't exist in dataset latitude dimenstion. Please check your args".format(kwargs["latitude"]))
    if "longitude" not in kwargs:
        raise KeyError("Longitude dimension doesn't exists in kwargs. Please check your args")
    if (kwargs["longitude"]) not in ds.coords["longitude"].data:
        raise ValueError("Your longitude '{}' doesn't exist in dataset longitude dimenstion. Please check your args".format(kwargs["longitude"]))
    if "data" not in kwargs:
        raise KeyError("You didn't provide name of data_var. Please check your args - add <data> if it doesn't exist")
    if kwargs["data"] not in ds.data_vars:
        raise KeyError("Interested data var <{}> doesn't exist in dataset. Please check your main() function or file".format(kwargs["data"]))
    
    # Check additional dimensions like 'level'
    if ("level" in ds.coords) and ("level" not in kwargs):
        raise KeyError("Target file has LEVEL coords but you didn't provide it. Please check your args")
    if ("level" in ds.coords) and (kwargs["level"] not in ds.coords["level"].data):
        raise ValueError("Your level '{}' doesn't exist in dataset level dimenstion. Please check your args".format(kwargs["level"]))
 
    # Select data by time with constant lat, long and level if it exists and write it to corresponding file
    dsloc = None
    resulting_list = list()


    if ("level" not in ds.coords):
        for lat in kwargs['latitude']:
            for lon in kwargs["longitude"]:
                dsloc = ds.sel(latitude=lat, longitude=lon)
                time_list = dsloc.data['time']
                data_list = dsloc.data[kwargs['data']]
                resulting_list.append(pack_data_to_list(time_list, data_list, lat=lat, lon=lon+shift_longitude))
    else:
        for lat in kwargs['latitude']:
            for lon in kwargs["longitude"]:
                for lev in kwargs['level']:
                    dsloc = ds.sel(latitude=lat, longitude=lon, level=lev)
                    time_list = dsloc['time'].data
                    data_list = dsloc[kwargs['data']].data
                    resulting_list.extend(pack_data_to_list(time_list, data_list, lat=lat, lon=lon+shift_longitude, lev=lev))

    save_to_csv_file(fout, resulting_list)

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

def save_to_csv_file(fout, data_list):
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

def get_out_file_name(file_path, **kwargs):
    result = ""

    # Get only file name
    result = os.path.basename(file_path)

    # Truncate extension
    result = result[: result.rfind(".")]

    # Append data from kwargs

    # Append extenstion
    result += ".dat"

    return result

def process_all_files_in_folder(in_folder, out_folder, **kwargs):
    for file_path in glob.glob(in_folder + "/" + "*.nc"):
        out_file_name = get_out_file_name(file_path)
        print(" >>> Process file '{}' with output name '{}'".format(file_path, out_file_name))
        process_netcdf_file(file_path, out_folder + "/" + out_file_name, **kwargs)
        print("")

def main():
    params = {
        # latitude from 90.0 to -90.0 with step ???
        "latitude": [0.0], 
        # longitude from -180.0 to 180.0 with step ???         
        "longitude": [0.0],
        # level if exist for this type of the netCDF data. If not exist - please comment it
        "level": [1],
        # interested data - please provide name of variable
        "data": "w"
    }
    process_all_files_in_folder("./input", "./output", **params)

if __name__ == "__main__":
    main()