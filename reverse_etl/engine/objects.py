import yaml
from dotmap import DotMap
from pathlib import Path
from reverse_etl.engine.dir_paths import PathResolution


class Environment:
    def __init__(self, config: str):
        self.env = config
        self.config = self.parse_config(config)
        self.settings = self.config.settings
        self.inactive_dags = self.config.inactive_dags
        self.composer_cluster = self.config.composer_cluster
        self.dbt_kube_operator = self.config.dbt_kube_operator
        self.status_cake_notifications = self.config.status_cake_notifications
        self.slack_notifications = self.config.slack_notifications
        self.frequency = self.config.frequency

    def parse_config(self, config):
        path = PathResolution()
        with open(Path(path.environments / self.env).with_suffix(".yml"), "r") as file:
            config = DotMap(yaml.safe_load(file))
            return config


class Model:
    def __init__(self, model_dir: Path):
        self.model_dir = model_dir
        self.config = self.parse_config()
        self.model_id = self.config.model_id
        self.environments = self.config.environments
        self.dag_options = self.config.dag_options
        self.pipes = self.config.pipes

    def read_file(self, rel_path, pipe):
        abs_path = (self.model_dir / rel_path).resolve()
        content = open(abs_path, "r").read()
        if abs_path.suffix == ".sql":
            template = {
                "SOURCE_TABLE_NAME": pipe.source.table,
                "TMP_TABLE_NAME": pipe.tmp.table,
                "TARGET_TABLE_NAME": pipe.target.table,
                "TMP_DATABASE": pipe.tmp.database,
                "TARGET_DATABASE": pipe.target.database
            }
            content = content.format(**template)
        return content

    def parse_config(self, config_file="model_config.yml"):
        config_file = self.model_dir / config_file
        with open(config_file, 'r') as file:
            config = DotMap(yaml.safe_load(file))
            for dag_id, pipe in config.pipes.items():
                pipe.source.query = self.read_file(pipe.source.query, pipe)
                pipe.target.schema = self.read_file(pipe.target.schema, pipe)
                for query in pipe.tasks.values():
                    query = self.read_file(query, pipe)
                config.pipes[dag_id] = Pipe(**pipe)
            return config


class Pipe:
    def __init__(self, source, tmp, target, options):
        self.source = BigQuerySource(**source)
        self.tmp = MySQLTemp(**tmp)
        self.target = MySQLTarget(**target)
        self.options = options


class BigQuerySource:
    def __init__(self, table, query):
        self.table = table
        self.query = query


class MySQLTemp:
    def __init__(self, database, table):
        self.database = database
        self.table = table


class MySQLTarget:
    def __init__(self, database, table, query):
        self.database = database
        self.table = table
        self.query = query
