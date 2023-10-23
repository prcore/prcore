# PrCore

[![](https://img.shields.io/github/actions/workflow/status/prcore/prcore/main.yml?label=Docker%20compose%20service)](https://github.com/prcore/prcore/actions/workflows/main.yml)
[![](https://img.shields.io/codefactor/grade/github/prcore/prcore/main?label=Code%20quality)](https://www.codefactor.io/repository/github/prcore/prcore/overview/main)
[![](https://img.shields.io/github/license/prcore/prcore?color=blue&label=License)](https://github.com/prcore/prcore/blob/main/LICENSE)

PrCore is a backend application used for prescriptive process monitoring. 
It takes historical event log files and provides ongoing case prescriptions based on the 
received event streaming data or new event log dataset. 
It is flexible and can be applied to event logs in various domains. 
Its prescribing and predicting algorithms can be easily modified, replaced, or added due to its plugin mechanism. 
Moreover, its API is easy to use and can be integrated into any application.

```mermaid
flowchart LR
    upload(Upload) --> train(Train) --> new(New Data) --> result(Prescriptions)
```

Please check out following link(s) for more information:

- Documentation: [https://prcore-docs.chaos.run](https://prcore-docs.chaos.run)

PrCore is licensed under the [MIT License](LICENSE).
