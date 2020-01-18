#!/usr/bin/env python3
"""Usage:
install.py show
install.py [options]

-a --all                    install all in config.
-f --force                  force linking new paths [default: False].
--config=<config_path>      config file of the install script [default: config.yaml].
--base-dir=<base_dir>       base directory of all assets.
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


def get_filtered_config(args):
    config = get_config(args["--config"])
    print(f"{Colors.OKBLUE}Config loaded successfully!{Colors.ENDC}")
    if args["--all"]:
        return config

    settings = [setting["key"] for setting in config]

    questions = [
        inquirer.Checkbox('interests',
                          message="What are you interested in?",
                          choices=settings),
    ]
    answers = inquirer.prompt(questions, theme=GreenPassion())
    if answers is None:
        answers = {
            "interests": []
        }

    return [setting for setting in config
            if setting["key"] in answers["interests"]]


def install(args):
    config = get_filtered_config(args)
    base_dir = args["--base-dir"]
    if base_dir is None:
        base_dir = BASE_DIR

    for setting_index, setting in enumerate(config):
        setting = AttrDict(setting)
        total_steps = len(setting.steps)
        print(f"Running settings of {setting.key} - {setting.description}")
        for index, step in enumerate(setting.steps):
            counter = Counter()
            print(f"- Running step {1 + index}/{total_steps} - {step.description}")
            for key, handler in CONFIG_TO_HANDLER.items():
                if hasattr(step, key):
                    handler(base_dir,
                            getattr(step, key), args=args, counter=counter)

            print(f"- Done step {1 + index}/{total_steps} - "
                  f"{Colors.OKGREEN}successes: {counter['ok']}{Colors.ENDC}, "
                  f"{Colors.WARNING}warnings: {counter['warnings']}{Colors.ENDC}")

    print(f"{Colors.fg.green}Done!{Colors.ENDC}")


def show_config(args):
    config = get_config(args["--config"])
    for index, step in enumerate(config):
        step = AttrDict(step)
        print(f"{index} - {step.key} - {step.description}")


def main():
    args = docopt.docopt(__doc__)

    if args["show"]:
        show_config(args)

    else:
        install(args)


if __name__ == '__main__':
    main()
