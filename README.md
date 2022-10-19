# Backend

## Structural design

The application will use a microkernel architecture, which allows the user to add new algorithms as plugins,
without having to modify the core of the application.

### Reasons

To provide extensibility, flexibility, and modularity. We can add, remove, or change algorithms with little
or no impact on the rest of the core application or other plug-in algorithms. In this way, the application can also
load external pluggable algorithm components, without changing source code.

### How it works

![Microkernel architecture pattern](https://www.oreilly.com/api/v2/epubs/9781491971437/files/assets/sapr_0301.png)

![Plugin architecture pattern](https://miro.medium.com/max/4800/1*O5fy4IsGpZhgBYdqciBvAQ.png)

### Example

Each algorithm will be a separate module, which will be loaded at runtime. The module will be in a separate folder as a
plugin. Each plugin should implement the same interface/methods defined by a specific scheme, and it can also import
some common modules from the core application.

The core application will be responsible for detecting and loading the plugins, checking the compatibility based on 
the scheme, initializing them, calling them, saving the data/model, and delivering the results.

So when the event log is uploaded, it will automatically generate a list of available algorithms based on the 
applicable plugins. The user can then select the algorithm and the parameters to be used.

#### Example of plugins' folder structure

```
.
└── plugins/
    ├── algorithm_a/
    │   ├── __init__.py
    │   ├── a.py
    │   └── ...
    ├── algorithm_b/
    │   ├── __init__.py
    │   ├── b.py
    │   └── ...
    ├── algorithm_c/
    │   ├── __init__.py
    │   ├── c.py
    │   └── ...
    └── .../
        └── ...
```

#### Example of a plugin's main class

```python
class Algorithm:
    def __init__(self, name, description, parameters):
        self.name = name
        self.description = description
        self.parameters = parameters

    # ...... other lines of code

    def is_applicable(self, data):
        # check if the algorithm can be applied to the data
        pass

    def pre_process(self, data):
        # do some pre-processing on the data
        pass
    
    # ...... other lines of code
    
    def train(self, data):
        # train the algorithm on the data
        pass

    def save_model(self, model):
        # save the model to a file
        pass

    def load_model(self, model):
        # load the model from a file
        pass

    def predict(self, model, data):
        # predict the output of the data
        pass

    # ...... other lines of code
```

## API endpoints design

| URI                 | METHOD | DESCRIPTION                             |
|---------------------|--------|-----------------------------------------|
| /api/eventlog       | POST   | Upload a new eventlog to backend        |
| /api/eventlog/{id}  | POST   | Add a new event to the log              |
| /api/eventlog/{id}  | GET    | Get log details                         |
| /api/eventlog/{id}  | PUT    | Change and/or confirm eventlog          |
| /api/eventlog/{id}  | DELETE | Delete a event log                      |
| /api/dashboards     | GET    | Get dashboards list                     |
| /api/dashboard/{id} | GET    | Get overview information of a dashboard |
| /api/dashboard/{id} | DELETE | Delete a dashboard                      |
| /api/dashboard/{id} | PUT    | Update a dashboard (name, description)  |

## Technologies will be used

- Python 3.10
- FastAPI
- PostgreSQL
- Reusable methods from other open-source projects
- ...
- Docker
