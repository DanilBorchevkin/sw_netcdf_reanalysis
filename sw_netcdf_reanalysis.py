import xarray as xr
import csv
import glob
import os


def process_netcdf_file(fin, fout, **kwargs):
    print(">>> kwargs to process:")
    for key, value in kwargs.items():
        print("{0} = {1}".format(key, value))   
    print("")

    # Open netCDF file
    ds = xr.open_dataset(fin)

    # netCDF data set has
    # - coords - coordinates - lat, long, time, level dimenstions
    # - data_vars - data for coordinates - temperature, pressure and so on
    # You can check it by following expression
    #print(ds.coords)
    #print(ds.data_vars)

    # Check all neccessary dimension
    if "latitude" not in ds.coords:
        raise KeyError("Latitude dimension doesn't exists in Dataset coordinates. Please check your file {}".format(fin))
    if "longitude" not in ds.coords:
        raise KeyError("Longitude dimension doesn't exists in Dataset coordinates. Please check your file{}".format(fin))
    if "time" not in ds.coords:
        raise KeyError("Time dimension doesn't exists in Dataset coordinates. Please check your file {}".format(fin))

    # We should use coordinates from -180 to 180
    # But some netCDF files used 0 to 360.
    # So we just shift coordinates exaclty to -180 to 180
    start_longitude = ds.coords["longitude"].data[0]
    shift_longitude = 0
    if start_longitude == 0.0:
        shift_longitude = -180.0

    # Check all neccessary kwargs
    if "latitude" not in kwargs:
        raise KeyError("Latitude dimension doesn't exists in kwargs. Please check your args")
    if kwargs["latitude"] not in ds.coords["latitude"].data:
        raise ValueError("Your latitude '{}' doesn't exist in dataset latitude dimenstion. Please check your args".format(kwargs["latitude"]))
    if "longitude" not in kwargs:
        raise KeyError("Longitude dimension doesn't exists in kwargs. Please check your args")
    if (kwargs["longitude"] - shift_longitude) not in ds.coords["longitude"].data:
        raise ValueError("Your longitude '{}' doesn't exist in dataset longitude dimenstion. Please check your args".format(kwargs["longitude"]))
    if "data" not in kwargs:
        raise KeyError("You didn't provide name of data_var. Please check your args")
    if kwargs["data"] not in ds.data_vars:
        raise KeyError("Interested data var {} doesn't exist in dataset. Please check your main() function or file".format(kwargs["data"]))
    
    # Check additional dimensions like 'level'
    # TODO finish this
 

    # Select air data by time with constant lat, long and level
    #dsloc = ds.sel(lat=lat, lon=lon, level=level)

    # Get data 

    # Save data to file 

def get_out_file_name(file_path):
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
        # latitude from 90.0 to -90.0
        "latitude": 50.0, 
        # longitude from -180.0 to 180.0          
        "longitude": 50.0,
        # level if exist for this type of the netCDF data. If not exist - delete
        #"level": 50,
        # interested data - please provide name of variable
        "data": "sp"
    }

    process_all_files_in_folder("./input", "./output", **params)

if __name__ == "__main__":
    main()