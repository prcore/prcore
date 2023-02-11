from datetime import datetime

from pandas import DataFrame
from pm4py import read_xes

from core.enums.definition import ColumnDefinition, Operator
from core.schemas.definition import ProjectDefinition, Definition
from core.functions.event_log.dataset import get_processed_dataframe


def get_dataframe() -> DataFrame:
    df = read_xes("data/bpic2012.xes", dtype=str)
    df_obj = df.select_dtypes(['object'])
    df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
    return df


def get_definition() -> Definition:
    columns_definition = {
        "org:resource": ColumnDefinition.RESOURCE,
        "lifecycle:transition": ColumnDefinition.TRANSITION,
        "concept:name": ColumnDefinition.ACTIVITY,
        "time:timestamp": ColumnDefinition.TIMESTAMP,
        "case:reg_date": ColumnDefinition.DATETIME,
        "case:concept:name": ColumnDefinition.CASE_ID,
        "case:AMOUNT_REQ": ColumnDefinition.NUMBER
    }
    outcome_definition = [
        [
            ProjectDefinition(
                column="concept:name",
                operator=Operator.EQUAL,
                value="A_APPROVED"
            )
        ]
    ]
    treatment_definition = [
        [
            ProjectDefinition(
                column="concept:name",
                operator=Operator.EQUAL,
                value="O_SENT_BACK"
            )
        ]
    ]
    return Definition(
        id=1,
        created_at=datetime.now(),
        columns_definition=columns_definition,
        outcome_definition=outcome_definition,
        treatment_definition=treatment_definition
    )


def main():
    df = get_dataframe()
    definition = get_definition()
    start_time = datetime.now()
    processed_df = get_processed_dataframe(df, definition)
    end_time = datetime.now()

    print(f"Time: {end_time - start_time}")
    processed_df.to_csv("data/bpic2012_xes_processed.csv", index=False)
    print("Done!")


if __name__ == "__main__":
    main()
