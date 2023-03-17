# PrCore

[![Docker Compose Test](https://github.com/prcore/prcore/actions/workflows/main.yml/badge.svg)](https://github.com/prcore/prcore/actions/workflows/main.yml) [![](https://img.shields.io/pingpong/status/sp_c60bb412baf14b219102581cecc9631f?style=flat)](https://prcore.pingpong.host/en/)

## Introduction

PrCore is a backend application used for prescriptive process monitoring. 
It takes historical event log files and provides ongoing case prescriptions based on the 
received event streaming data or new event log dataset. 
It is flexible and can be applied to event logs in various domains. 
Its prescribing and predicting algorithms can be easily modified, replaced, or added due to its plugin mechanism. 
Moreover, its API is easy to use and can be integrated into any application.

- Documentation: [https://prcore-docs.chaos.run](https://prcore-docs.chaos.run)
- Demo API: [https://prcore.chaos.run](https://prcore.chaos.run)

![](https://download.chaos.run/prcore/flow.png?45329)

## License

PrCore is licensed under the [MIT License](LICENSE).
