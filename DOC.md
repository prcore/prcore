## API Documentation

### `GET /result/{dashboard_id}`

#### Streaming technology

This endpoint is using [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events) to stream the results.

The first call to this endpoint will return the current results state of dashboard, and then will stream the results as they are updated.

#### Output example

Result of single case:

```json
{
    "case_id": 8004285,
    "current_activity": "W_Nabellen offertes",
    "prescription": [
        {
            "id": 126758,
            "date": 1673432022,
            "type": "next_activity",
            "output": "O_SENT_BACK",
            "model": {
                "name": "KNN next activity prediction",
                "accuracy": 0.8,
                "recall": 0.8,
                "precision": 0.8,
                "probability": 0.8
            }
        },
        {
            "id": 126758,
            "date": 1673432022,
            "type": "alarm",
            "output": true,
            "model": {
                "name": "Random Forest Alarm",
                "accuracy": 0.8,
                "recall": 0.8,
                "precision": 0.8,
                "probability": 0.8
            }
        },
        {
            "id": 126760,
            "date": 1673432024,
            "type": "cate_prediction",
            "output": {
                "proba_if_treated": 0.48833414912223816,
                "proba_if_untreated": 0.24659280478954315,
                "cate": 0.241741344332695
            },
            "model": {
                "name": "Casual Lift Algorithm",
                "accuracy": 0.766,
                "precision": 0.895,
                "recall": 0.75,
                "roc_auc": 0.875
            }
        }
    ]
}
```

#### Other possible fields

- [ ] activities: `can be easily added if need`
    - [ ] event_name
    - [ ] start_timestamp
    - [ ] end_timestamp
    - [ ] resource
- [ ] similar_cases: `not sure how to add this feature`
