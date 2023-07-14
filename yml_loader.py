
import yaml

def load_yml(filepath: str):
    with open(filepath) as f:
        return yaml.load(f, Loader=yaml.Loader)
