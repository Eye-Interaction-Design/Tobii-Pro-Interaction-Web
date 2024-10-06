# Tobii Pro Interaction Web

## Usage

### For Apple Silicon Macs

The official Tobii Pro SDK used in this app currently does not support Apple Silicon Macs ([ref](https://developer.tobiipro.com/tobiiprosdk/platform-and-language.html)).

First, follow the steps below to install the Intel (Rosetta 2) version of Python (Japanese only):  
[https://zenn.dev/shikibu9419/articles/36e3d37460efa0](https://zenn.dev/shikibu9419/articles/36e3d37460efa0)

```shell
# after installing drivers for Intel macOS
> poetry env <path to the installed Python>
> poetry install
```

### Setup

1. Install Tobii Pro Eye Tracker Manager
2. Install drivers from the Tobii Pro Eye Tracker Manager
3. Run the following:

```shell
> poetry install
> poetry run dev
```
