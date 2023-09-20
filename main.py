from pathlib import Path
from reverse_etl.engine.objects import Model


ROOT = Path(__file__).parent.resolve()
PKG_ROOT = ROOT / "reverse_etl"
MODEL_ROOT = PKG_ROOT / "models"


if __name__ == "__main__":
    for model_dir in MODEL_ROOT.glob("*/"):

        if model_dir.stem == "test":

            print(model_dir)

            print("####################")

            model = Model(model_dir)
            source_query = open(model.pipes.snapshot.source.query, 'r')
            insert_query = open(model.pipes.snapshot.target.query, 'r')
            #
            print(model.dag_id)
            print(model.environments)
            # print(source_query.read())
            # print(insert_query.read())

            print(model.pipes)
            print(vars(model.pipes.snapshot.source))
            # print(vars(model.pipes.snapshot.tmp))
            # print(vars(model.pipes.snapshot.target))
