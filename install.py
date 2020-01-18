"""Usage:
install.py [options]

-f --force                 force linking new paths [default: False].
--config=<config_path>     config file of the install script [default: config.yaml].
--base-dir=<base_dir>      base directory of all assets.
"""
import os
import shutil
from collections import Counter

import yaml
import docopt
import inquirer
from inquirer.themes import GreenPassion
from attrdict import AttrDict

from methods import CONFIG_TO_HANDLER
from methods.utils import Colors


BASE_DIR = os.path.dirname(os.path.realpath(__file__))


def get_config(path):
    with open(path) as config_f:
        return yaml.load(config_f)


def get_filtered_config(path):
    config = get_config(path)
    print(f"{Colors.OKBLUE}Config loaded successfully!{Colors.ENDC}")
    steps = [step["key"] for step in config]

    questions = [
        inquirer.Checkbox('interests',
                          message="What are you interested in?",
                          choices=steps),
    ]
    answers = inquirer.prompt(questions, theme=GreenPassion())
    return [step for step in config if step["key"] in answers["interests"]]


def install():
    args = docopt.docopt(__doc__)
    config = get_filtered_config(args["--config"])
    base_dir = args["--base-dir"]
    if base_dir is None:
        base_dir = BASE_DIR

    total = len(config)
    for index, step in enumerate(config):
        counter = Counter()
        step = AttrDict(step)
        print(f"Running step {1 + index}/{total} - {step.description}")
        for key, handler in CONFIG_TO_HANDLER.items():
            if hasattr(step, key):
                handler(base_dir,
                        getattr(step, key), args=args, counter=counter)

        print(f"Done step {1 + index}/{total} - "
              f"{Colors.OKGREEN}successes: {counter['ok']}{Colors.ENDC}, "
              f"{Colors.WARNING}warnings: {counter['warnings']}{Colors.ENDC}")

    print(f"{Colors.fg.green}Done!{Colors.ENDC}")


if __name__ == '__main__':
    install()
