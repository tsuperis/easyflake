# EasyFlake

[![Test passing](https://github.com/tsuperis/easyflake/actions/workflows/test.yml/badge.svg)](https://github.com/tsuperis/easyflake/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/tsuperis/easyflake/branch/main/graph/badge.svg?token=3TIHGMYN1G)](https://codecov.io/gh/tsuperis/easyflake)
[![PyPI](https://img.shields.io/pypi/v/easyflake)](https://pypi.org/project/easyflake/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/easyflake)](https://pypi.org/project/easyflake/)
[![License](https://img.shields.io/github/license/tsuperis/easyflake)](https://github.com/tsuperis/easyflake/blob/main/LICENSE)

EasyFlake is a Python package for generating 64-bit IDs similar to Snowflake or Sonyflake. It provides a simple way to generate unique and sortable IDs that can be used as primary keys in databases, message queue messages, or other distributed systems.

## Introduction

In a distributed system, it can be challenging to generate unique IDs for records that need to be stored or processed across multiple nodes. EasyFlake provides a way to generate IDs that are unique, sortable, and easy to work with.


## Use Cases

Here are some examples of use cases for EasyFlake:

* User account IDs: Generate unique IDs for user accounts that can be used across multiple servers or databases.
* Transaction IDs: Generate IDs for financial transactions that need to be processed across multiple systems.
* Order numbers: Generate unique order numbers that can be sorted by timestamp.

## Installation

Install the latest version of EasyFlake using pip:

```bash
pip install easyflake
```

## Usage

To use EasyFlake, simply create an instance of the `EasyFlake` class, passing in a unique node ID:

```python
from easyflake import EasyFlake

ef = EasyFlake(node_id=1)
print(ef.get_id())
```

The `get_id()` method generates the next ID by the current timestamp. You can customize the number of bits used for the node ID and sequence ID parts, as well as the epoch timestamp and time scale.

```python
ef = EasyFlake(node_id=0, node_id_bits=4, sequence_bits=6)
print(ef.get_id())
```

The components of the output ID are the sequence value, node ID, and timestamp, in order from the lower bits.

### Arguments

* `node_id` (int, [NodeIdPool](#nodeidpool)): A unique ID for the current node. This ID should be between 0 and (2 ^ node_id_bits) - 1.
* `node_id_bits` (int): The maximum number of bits used to represent the node ID. This argument defaults to 8 / max node ID is 255.
* `sequence_bits` (int): The maximum number of bits used to represent the sequence number. This argument defaults to 8 / max sequence number is 255.
* `epoch` (float): A timestamp used as a reference when generating the timestamp section of the ID. This argument defaults to 1675859040 (2023-02-08T12:24:00Z).
* `time_scale` (int): The number of decimal places used to represent the timestamp. This argument defaults to 3 (milliseconds).

### API

#### `NodeIDPool`

This is a class that manages node IDs in a single-threaded or single-process environment. The default options provided are `GrpcNodeIdPool` and `FileNodeIdPool.` By inheriting from `BaseNodeIdPool`, you can also create your own custom node ID management.

##### `easyflake.FileNodeIdPool`

This is a file-based node ID management class. Care should be taken in distributed systems, as node IDs are managed by a single file.

###### Arguments

* `endpoint` (str): The path to the file where node IDs are recorded.
* `bits` (int): The maximum number of bits for node IDs.

##### `easyflake.GrpcNodeIdPool`

This is a gRPC-based node ID management class.
You can start a gRPC server using [`easyflake-cli grpc`](#easyflake-cli-grpc).  
However, it's important to note that the gRPC server can become a single point of failure in your system, so proper measures should be taken to ensure its availability.

###### Arguments

* `endpoint` (str): The address of the gRPC server.
* `bits` (int): The maximum number of bits for node IDs.

### Command

#### `easyflake-cli grpc`

This command starts a gRPC server for managing node IDs.

##### `Options`

* `-p`, `--port`: Specifies the port number of the gRPC server.
* `-d`, `--daemon`: Starts the server in daemon mode (not supported on Windows).
* `--pid-file`: Specifies the path to the PID file.

## Contributing

See the [contributing guide](https://github.com/tsuperis/easyflake/blob/main/CONTRIBUTING.md).

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/tsuperis/easyflake/blob/main/LICENSE) file for details.
