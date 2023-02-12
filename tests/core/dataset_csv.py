from datetime import datetime

from pandas import DataFrame, read_csv

from core.enums.definition import ColumnDefinition, Operator
from core.schemas.definition import ProjectDefinition, Definition
from core.functions.event_log.dataset import get_processed_dataframe


def get_dataframe() -> DataFrame:
    df = read_csv("data/bpic2012.csv", dtype=str)
    df_obj = df.select_dtypes(['object'])
    df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
    return df


def get_definition() -> Definition:
    columns_definition = {
        "Case ID": ColumnDefinition.CASE_ID,
        "start_time": ColumnDefinition.START_TIMESTAMP,
        "end_time": ColumnDefinition.END_TIMESTAMP,
        "AMOUNT_REQ": ColumnDefinition.NUMBER,
        "REG_DATE": ColumnDefinition.DATETIME,
        "Activity": ColumnDefinition.ACTIVITY,
        "Resource": ColumnDefinition.RESOURCE
    }
    outcome_definition = [
        [
            ProjectDefinition(
                column="Activity",
                operator=Operator.EQUAL,
                value="A_APPROVED"
            )
        ]
    ]
    treatment_definition = [
        [
            ProjectDefinition(
                column="Activity",
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
        treatment_definition=treatment_definition,
        fast_mode=True,
        start_transition="start",
        end_transition="complete"
    )


def main():
    df = get_dataframe()
    definition = get_definition()
    start_time = datetime.now()
    processed_df = get_processed_dataframe(df, definition)
    end_time = datetime.now()

    print(f"Time: {end_time - start_time}")
    processed_df.to_csv("data/bpic2012_csv_processed.csv", index=False)
    print("Done!")


if __name__ == "__main__":
    main()
