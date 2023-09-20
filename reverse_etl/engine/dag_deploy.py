from reverse_etl.engine.objects import Pipe, Model, Environment
import logging
from datetime import datetime
from airflow import DAG

from airflow.operators.mysql_operator import MySqlOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook
from airflow.operators.python_operator import BranchPythonOperator
from airflow.operators.python import get_current_context
from airflow.utils.trigger_rule import TriggerRule
from utils.constants.schedule_interval import ScheduleInterval
from utils.operators.slack.slack_success import build_slack_success
from utils.operators.bigquery_to_mysql import BigQueryToMySqlOperatorSword

from utils.variables import (
    dag_default_args,
    get_json_variable_value,
    get_variable,
)
from sqlalchemy.dialects import mysql


def check_is_initial_snapshot(mysql_hook, table_name, empty_table_task, non_empty_table_task):
    row_count = mysql_hook.get_pandas_df(
        f"select count(*) as total_rows from {table_name}"
    )
    force_snapshot = get_current_context()["dag_run"].conf.get("force_snapshot", False)

    logging.info("%s has %s rows", table_name, row_count['total_rows'][0])
    logging.info("force_snapshot: %s", force_snapshot)

    if row_count["total_rows"][0] == 0 or force_snapshot is not False:
        return empty_table_task

    return non_empty_table_task


def define_dag(dag_id, pipe: Pipe, model: Model, environment: Environment):
    try:
        if model.model_id in get_variable("inactive_dags"):  # TODO: Remove this and pull from environments yaml file
            return None
    except KeyError:
        print("Key not found. Proceeding......")

    with DAG(
        dag_id=f"{model.model_id}_{dag_id}",
        default_args=dag_default_args(
            state_date=datetime(2022, 6, 26),

        ),
        tags=[environment.env,
        ],
        # rest of the dag settings
        catchup=False,
        schedule_interval=ScheduleInterval.EVER_4HOUR_AT_MINUTE_45,
        is_paused_upon_creation=True,
        max_active_runs=1

    ) as dag:
        is_initial_snapshot = BranchPythonOperator(
            task_id = "check_is_incremental",
            python_callable=lambda: check_is_initial_snapshot(
                mysql_hook=MySqlHook(
                    mysql_conn_id="<mysql_conn_id>" # Need to work on this
                ),
                table_name=pipe.target.table,
                empty_table_task="bq_to_mysql_snapshot",
                non_empty_table_task="bq_to_mysql_incremental"
            ),
        )

        bq_to_mysql_snapshot = BigQueryToMySqlOperatorSword(
            task_id="ba_to_mysql_snapshot",
            gcp_conn_id=environment.settings.gcp_conn_id,
            bq_table=pipe.source.table,
            database=pipe.tmp.database,
            mysql_conn_id="<mysql_conn_id>",
            sql=pipe.source.table,
            mysql_table=pipe.tmp.table,
            sql_limit=300000,
            schema_dtype=pipe.target.schema,
            **pipe.source.snapshot_options
        )

        bq_to_mysql_incremental = BigQueryToMySqlOperatorSword(
            task_id="ba_to_mysql_incremental",
            gcp_conn_id=environment.settings.gcp_conn_id,
            bq_table=pipe.source.table,
            database=pipe.tmp.database,
            mysql_conn_id="<mysql_conn_id>",
            sql=pipe.source.table,
            mysql_table=pipe.tmp.table,
            sql_limit=300000,
            schema_dtype=pipe.target.schema,
            **pipe.source.incremental_options
        )

        is_initial_snapshot >> [bq_to_mysql_snapshot, bq_to_mysql_incremental]

        previous_task = None
        for task_id, query in pipe.tasks.items():
            current_task = MySqlOperator(
                task_id=task_id,
                database=pipe.target.database,
                sql=query,
                mysql_con_id="<mysql_con_id>",
                trigger_rule=TriggerRule.NONE_FAILED,
            )

            if previous_task:
                previous_task >> current_task
            else:
                bq_to_mysql_snapshot >> current_task
                bq_to_mysql_incremental >> current_task

            previous_task = current_task

        slack_succeeded = build_slack_success()

        previous_task >> slack_succeeded
        return dag