#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Dict
import subprocess
import json
import os


class PipUpgrade:
    """Simple class for upgrading pip packages.

    :attr PIP_LIST_CMD: Command for getting pip packages.
    :attr PIP_UPGRADE_CMD: Command for upgrading pip package.
    :attr PIP_PKGS: Dictionary of pip packages.
    :attr ERRORS: Array of stored errors.
    :attr LOGS: Simple log file for all scripts.
    """

    def __init__(self) -> None:
        """Magick method for initial class instance.

        :return: None.
        """
        self.PIP_LIST_CMD: List[str] = ['pip3', 'list', '-o', '--format=json']
        self.PIP_UPGRADE_CMD: List[str] = ['pip3', 'install', '--upgrade', '{pkg}']
        self.PIP_PKGS: Dict[str, str] = {}
        self.ERRORS: List[str] = []
        self.LOGS: str = 'logs.txt'
        if not os.path.exists(self.LOGS):
            os.mknod(self.LOGS)

    def get_pip_pkgs(self) -> None:
        """Get all pip packages.

        :return: None.
        """
        pkgs = subprocess.run(self.PIP_LIST_CMD, capture_output=True)
        pkgs = pkgs.stdout.decode('utf-8')
        pkgs = json.loads(pkgs)
        self.PIP_PKGS = pkgs

    def upgrade_pip_pkgs(self) -> None:
        """Upgrade pip packages from dictionary.

        :return: None.
        """
        for pkg in self.PIP_PKGS:
            upgrade_command = self.PIP_UPGRADE_CMD.copy()
            upgrade_command[3] = upgrade_command[3].format(pkg=pkg)
            pkg_info = subprocess.run(upgrade_command, capture_output=True)
            info, err = pkg_info.stdout.decode('utf-8'), pkg_info.stderr.decode('utf-8')
            print(info)
            if len(err) > 0:
                self.ERRORS.append(err)

    def write_err(self) -> None:
        """Will record errors if they were.

        :return: None.
        """
        if len(self.ERRORS) > 0:
            with open(self.LOGS, 'a') as file:
                for err in self.ERRORS:
                    file.write(str(err) + '\n')

    def main(self) -> None:
        """Run upgrading process.

        :return: None.
        """
        self.get_pip_pkgs()
        self.upgrade_pip_pkgs()
        self.write_err()


if __name__ == '__main__':
    PipUpgrade().main()
