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
        return AttrDict(yaml.load(config_f))


def get_filtered_options(options):
    print(f"{Colors.OKBLUE}Config loaded successfully!{Colors.ENDC}")
    settings = [setting["key"] for setting in options]

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

    return [setting for setting in options
            if setting["key"] in answers["interests"]]


def install(args):
    config = get_config(args["--config"])
    if args["--all"]:
        options = config.options
    else:
        options = get_filtered_options(config.options)

    base_dir = args["--base-dir"]
    if base_dir is None:
        base_dir = BASE_DIR

    for setting_index, setting in enumerate(options):
        total_steps = len(setting.steps)
        print(f"Running settings of "
              f"{Colors.fg.lightred}{setting.key}{Colors.ENDC} - "
              f"{Colors.OKBLUE}{setting.description}{Colors.ENDC}")
        for index, step in enumerate(setting.steps):
            counter = Counter()
            print(f"- Running step {1 + index}/{total_steps} - "
                  f"{step.description}")
            for key, handler in CONFIG_TO_HANDLER.items():
                if hasattr(step, key):
                    handler(base_dir,
                            getattr(step, key), args=args, counter=counter)

            print(f"- Done step {1 + index}/{total_steps} - "
                  f"{Colors.OKGREEN}"
                  f"successes: {counter['ok']}"
                  f"{Colors.ENDC}, {Colors.WARNING}"
                  f"warnings: {counter['warnings']}"
                  f"{Colors.ENDC}")
            if counter['warnings'] > 0:
                print(f"{Colors.WARNING}"
                      f"***Try running with -f to force install***"
                      f"{Colors.ENDC}")

    print(f"{Colors.fg.green}Done!{Colors.ENDC}")


def show_config(args):
    config = get_config(args["--config"])
    for setting in config.options:
        print(f"{setting.key} - {setting.description}")
        for index, step in enumerate(setting.steps):
            print(f" step {index + 1} - {step.description}")


def main():
    args = docopt.docopt(__doc__)

    if args["show"]:
        show_config(args)

    else:
        install(args)


if __name__ == '__main__':
    main()
