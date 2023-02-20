# PrCore

PrCore is a backend application used for prescriptive process monitoring.

## Installation

Pre-requisites:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

Steps:

1. Clone the repository
2. Create a `.env` file from the `example.env` file
3. Run `install.sh`
4. Done!

Example:

```bash
git clone https://github.com/prcore/prcore.git
cd prcore
cp example.env .env
vim .env  # Edit the .env file
cd scripts
bash install.sh
```

## Documentation

The documentation is available at [https://prcore-docs.chaos.run](https://prcore-docs.chaos.run) 
and [https://prcore.gitlab.io](https://prcore.gitlab.io)
