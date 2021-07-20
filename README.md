# JSON Messagepack Convert
convert text in json to bytes in messagepack and vice versa.

## Usage
```shell script
usage: main.py [-h] [--output [OUTPUT]] [input]

JSON Messagepack Convert

positional arguments:
  input                 If file is a single dash `-` or absent, reads from the stdin

optional arguments:
  -h, --help            show this help message and exit
  --output [OUTPUT], -o [OUTPUT]
                        Write to FILE instead of stdout
```

### Example
with stdin and stdout
```shell script
echo '{"compact": true, "schema": 0}' | python main.py -       
82 a7 63 6f 6d 70 61 63 74 c3 a6 73 63 68 65 6d 61 00%
```

both input and output are file
```shell script
python main.py -o packed_bin json_file.txt       
```

## Note
* When serialize float object into bytes in messagepack, float object is serialized with double precision.