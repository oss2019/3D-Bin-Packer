# 3D Bin Packer
Initally created for the FedEx PS - Inter IIT Tech Meet 13.0


## Pre-requisites

* Python (>= 3.10)

* Python libaries
    * Navigate to the root directory of our code and run:
        ```shell
        pip install -r requirements.txt
        ```
* 2 seperate CSV files for Packages and ULDs respectively

* File Structure has to be maintained 
```
.
├── run.sh          # The bash script
├── src/
    ├── main.py     # The main Python script
    ├── (other Python files)
```


## Executing the program

**We recommend you to execute our program through run.sh**

```shell
./run.sh <solver-type> <uld-file> <package-file> <output-dir>
```


| **Parameter**     | **Description**                                                      |
| :---------------: |:---------------------------------------------------------------------|
| `<solver-type>`   | Specifies the type of solver to use. Supported values:               |
|                   | - `Preference`                                                       |
|                   | - `Tree`                                                             |
|                   | - `BasicOverlap`                                                     |
|                   | - `BasicNonOverlap` (not fully functional for 100% priority packing) |
| `<uld-file>`      | Path to the ULD (Unit Load Device) file.                             |
| `<package-file>`  | Path to the package data file.                                       |
| `<output-dir>`    | Directory to store the output results.                               |


## Example
```shell
./run.sh BasicOverlap input/ulds.csv input/packages.csv output/
```
* If you do not have access to a shell on a Linux system, try the following to run the python script directly
    * Create an output folder `output/`
    * Create an input folder `input/` with all the CSV files
    * From the root of the downloaded code, run
```shell
python src/main.py Preference input/ulds.csv input/packages.csv output/
```

* The PyVista window then opens up and displays the packing in each ULD

## Troubleshooting

* If you encounter an error that says `Permission Denied`, mark the script as executable:
```shell
    chmod +x script.sh
```
* Missing Dependencies:
    Install Python dependencies as described above.
