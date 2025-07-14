# Tobii Pro Interaction Web

## Usage

### For Apple Silicon Macs

The official Tobii Pro SDK used in this app currently does not support Apple Silicon Macs ([ref](https://developer.tobiipro.com/tobiiprosdk/platform-and-language.html)).

First, follow the steps below to install the Intel (Rosetta 2) version of Python (Japanese only):  
[https://zenn.dev/shikibu9419/articles/36e3d37460efa0](https://zenn.dev/shikibu9419/articles/36e3d37460efa0)

```shell
# after installing drivers for Intel macOS
> export UV_PYTHON=<path to the installed Python>
> uv sync
```

### Setup

1. Install Tobii Pro Eye Tracker Manager
2. Install drivers from the Tobii Pro Eye Tracker Manager
3. Run the following:

```shell
> uv run uvicorn src.app:app --reload
```
