# FedEx-InterIITTech13
Team 83 - FedEx Inter IIT Tech Meet


## Pre-requisite Software

* ### Python (>= 3.10)

* ### Python libaries
    * #### Navigate to the src/ directory and run:
        ```shell
        pip install -r requirements.txt`
        ```
* ### 2 seperate CSV files for Packages and ULDs respectively

* ### File Structure has to be maintained 
```
.
├── script.sh       # The bash script
├── src/
    ├── main.py     # The main Python script
    ├── (other Python files)
```


## Executing the program

**We recommend you to execute our program through run.sh**

```shell
./script.sh <solver-type> <uld-file> <package-file> <output-dir>
```


| **Parameter**     | **Description**                                                      |
| :---------------: |:---------------------------------------------------------------------|
| `<solver-type>`   | Specifies the type of solver to use. Supported values:               |
|                   | -  `Mixed` (Recommened)                                              |
|                   | - `BasicNonOverlap` (not fully functional for 100% priority packing) |
|                   | - `Tree`                                                             |
|                   | - `BasicOverlap`                                                     |
| `<uld-file>`      | Path to the ULD (Unit Load Device) file.                             |
| `<package-file>`  | Path to the package data file.                                       |
| `<output-dir>`    | Directory to store the output results.                               |


#### Example
```shell
./script.sh BasicOverlap input/ulds.csv input/packages.csv output/
```

## Troubleshooting

* ### Permission Denied:
```shell
    chmod +x script.sh
```
* ### Missing Dependencies:
    Install Python dependencies as described above.
