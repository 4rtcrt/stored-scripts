#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-


from typing import List, Tuple, Dict, Any, Type
import os
import subprocess


class PackageManager(object):
    """Base class provide some default methods for works with system packages info.

    :attr _BACKUP_FOLDER: Folder name in which packages backups will be stored
    :attr _childs: List of childs of the `PackageManager` class.
    """

    _BACKUP_FOLDER: str = 'backlibs'
    _childs: list = []

    def __new__(cls, *args, **kwargs) -> Type[Any]:
        """Manage the creation of instances in order to save all childs.

        :return: Class instance.
        """
        instance = object.__new__(cls, *args, **kwargs)
        cls._childs.append(instance)
        return instance

    @classmethod
    def sum_pkgs(cls) -> Tuple[List[str]]:
        """Find the final list of packages installed by the user, as the difference between the sets of marked packages and logged packages.

        :return: Tuple of list with packages names and list with packages dependencies.
        """
        for child in cls._childs:
            if isinstance(child, MarkedPackages):
                mark_pkgs = [child.pkgs_names, child.pkgs_dpnds]
            if isinstance(child, LogsPackages):
                logs_pkgs = [child.pkgs_names, child.pkgs_dpnds]

        pkgs_names = mark_pkgs[0] - logs_pkgs[0]
        pkgs_dpnds = mark_pkgs[1] - logs_pkgs[1]
        pkgs_names = pkgs_names - pkgs_dpnds
        return (pkgs_names, pkgs_dpnds)

    @classmethod
    def struct_pkgs(cls, pkgs_names: List[str]) -> Dict[str, List[str]]:
        """Create several different groups of packages for convenience.

        :param pkgs_names: Description of parameter `pkgs_names`.
        :return: Dictionary of all packages groups.
        """
        py_pkgs = {i for i in filter(lambda pkg: True if 'pyth' in pkg else False, pkgs_names)}
        lib_pkgs = {i for i in filter(lambda pkg: True if 'lib' in pkg else False, pkgs_names)}
        lib_pkgs = lib_pkgs - py_pkgs
        sum_pkgs = pkgs_names - py_pkgs - lib_pkgs
        result_data = {'gen_pkgs': sum_pkgs, 'py_pkgs': py_pkgs, 'lib_pkgs': lib_pkgs}

        for child in cls._childs:
            if isinstance(child, SnapPackages):
                result_data['snap_pkgs'] = child.pkgs_names

        return result_data

    @classmethod
    def save_data(cls, **kwargs: Dict[str, List[str]]) -> None:
        """Save data in files.

        :param **kwargs: Dictionary of group name and list packages to save.
        :return: None.
        """
        if not os.path.exists(cls._BACKUP_FOLDER):
            os.mkdir(cls._BACKUP_FOLDER)

        for key, value in kwargs.items():
            with open(cls._BACKUP_FOLDER+'/'+key+'.txt', 'w') as file:
                for v in value:
                    file.write(v+'\n')
        return None

    def _run_command(self, command: List[str]) -> str:
        """Run shell command.

        :param command: List of commands to be executed.
        :return: String of command result.
        """
        result = subprocess.run(command, capture_output=True)
        result = result.stdout.decode('utf-8')
        return result

    def _separate_all_info(self, info):
        """Separate string of all packages info.

        :param info: String of package info.
        """
        return info.split('\n\n')

    def _separate_pkg_info(self, info):
        """Separate string of one package info.

        :param info: String of package info.
        """
        return info.split('\n')

    def _separate_structured_info(self, info: str, name_trigger: str, depends_trigger: str) -> Tuple[List[str]]:
        """Separate 'package' and 'depends' from string info.

        :param info: String of package info.
        :param name_trigger: A string that is a trigger that further information about the package name is.
        :param depends_trigger: A string that is a trigger that further information about the package dependencies is.
        :return: Tuple of list packages names and list packages dependencies.
        """
        pkg_name = list(filter(lambda pkg_line: True if name_trigger in pkg_line else False, info))
        if len(pkg_name) > 0:
            pkg_name = pkg_name[0].replace('Package: ', '')
        else:
            pkg_name = ''

        pkg_dpnd = list(filter(lambda pkg_line: True if depends_trigger in pkg_line else False, info))
        if len(pkg_dpnd) > 0:
            pkg_dpnd = pkg_dpnd[0].replace('Depends: ', '')
        else:
            pkg_dpnd = ''
        return (pkg_name, pkg_dpnd)

    def _parse_dpnds(self, pkg_dpnd: str) -> List[str]:
        """Parse dependencies from string.

        :param pkg_dpnd: A string containing unparsed dependency information.
        :return: List of parsed dependencies.
        """
        pkg_dpnd = pkg_dpnd.replace('Pre-', '').replace('|', '').strip().split(', ')
        pkg_dpnd = list(map(lambda x: x.split(' ')[0], pkg_dpnd))
        return pkg_dpnd


class LogsPackages(PackageManager):
    """Realisation of packages from logs.

    :attr PKGS_COMMAND: List of commands that will be executed to get a list of packages.
    :attr PKG_NAME_TRIGGER: A string that is a trigger that further information about the package name is.
    :attr PKG_DEPENDS_TRIGGER: str: A string that is a trigger that further information about the package dependencies is.
    """

    PKGS_COMMAND: List[str] = ['gzip', '-dc', '/var/log/installer/initial-status.gz', '|', 'sort -u']
    PKG_NAME_TRIGGER: str = 'Package: '
    PKG_DEPENDS_TRIGGER: str = 'Depends: '

    def main(self) -> None:
        """Search information about packages and dependencies from the logs.

        :return: None.
        """
        pkgs_info = self._run_command(self.PKGS_COMMAND)
        pkgs_info = self._separate_all_info(pkgs_info)

        pkgs_names, pkgs_dpnds = [], []
        for info in pkgs_info:
            info = self._separate_pkg_info(info)
            pkg_name, pkg_dpnd = self._separate_structured_info(info, self.PKG_NAME_TRIGGER, self.PKG_DEPENDS_TRIGGER)
            if len(pkg_name) > 0:
                pkgs_names.append(pkg_name)
            if len(pkg_dpnd) > 0:
                pkg_dpnd = self._parse_dpnds(pkg_dpnd)
                pkgs_dpnds.extend(pkg_dpnd)

        pkgs_names, pkgs_dpnds = set(pkgs_names), set(pkgs_dpnds)
        pkgs_names = pkgs_names - pkgs_dpnds
        self.pkgs_names, self.pkgs_dpnds = pkgs_names, pkgs_dpnds


class MarkedPackages(PackageManager):
    """Realisation of packages from marked apt list.

    :attr PKGS_COMMAND: List of commands that will be executed to get a list of packages.
    :attr INFO_COMMAND: List of commands that will be executed to get information about the package.
    :attr PKG_NAME_TRIGGER: A string that is a trigger that further information about the package name is.
    :attr PKG_DEPENDS_TRIGGER: str: A string that is a trigger that further information about the package dependencies is.
    """

    PKGS_COMMAND: List[str] = ['apt-mark', 'showmanual', '|', 'sort -u', ]
    INFO_COMMAND: List[str] = ['apt', 'show', '{pkg_name}', ]
    PKG_NAME_TRIGGER: str = 'Package: '
    PKG_DEPENDS_TRIGGER: str = 'Depends: '

    def main(self) -> None:
        """Search information about packages and dependencies from marked apt list.

        :return: None.
        """
        pkgs_pre_names = self._run_command(self.PKGS_COMMAND)
        pkgs_pre_names = self._separate_pkg_info(pkgs_pre_names)

        pkgs_dpnds, pkgs_names = [], []
        for pkg_name in pkgs_pre_names:
            command = self.INFO_COMMAND.copy()
            command[2] = command[2].format(pkg_name=pkg_name)
            info = self._run_command(command)
            info = self._separate_pkg_info(info)
            pkg_name, pkg_dpnd = self._separate_structured_info(info, self.PKG_NAME_TRIGGER, self.PKG_DEPENDS_TRIGGER)
            if len(pkg_name) > 0:
                pkgs_names.append(pkg_name)
            if len(pkg_dpnd) > 0:
                pkg_dpnd = self._parse_dpnds(pkg_dpnd)
                pkgs_dpnds.extend(pkg_dpnd)

        pkgs_names, pkgs_dpnds = set(pkgs_names), set(pkgs_dpnds)
        pkgs_names = pkgs_names - pkgs_dpnds
        self.pkgs_names, self.pkgs_dpnds = pkgs_names, pkgs_dpnds


class SnapPackages(PackageManager):
    """Realisation of packages from snap list.

    :attr PKGS_COMMAND: List of commands that will be executed to get a list of snap packages.
    :attr IGNORED_PKGS: List of packages to ignore.
    """

    PKGS_COMMAND: List[str] = ['snap', 'list']
    IGNORED_PKGS: List[str] = ['canonical', 'core', 'chromium-ffmpeg', 'qt513', 'snapd', 'ufw', 'gnome', 'kde']

    def main(self) -> None:
        """Search information about packages from marked snap list.

        :return: None.
        """
        pkgs_info = self._run_command(self.PKGS_COMMAND)
        pkgs_info = self._separate_pkg_info(pkgs_info)
        pkgs_info = pkgs_info[1:]

        def rm_pkg(pkgs):
            for ignored in self.IGNORED_PKGS:
                if ignored in pkgs:
                    return False
            else:
                return True

        pkgs_info = list(map(lambda pkg:
            list(filter(lambda elem: len(elem) > 0, pkg.split(' '))),
            pkgs_info))
        pkgs_names = [pkg[0] for pkg in pkgs_info if len(pkg) > 0]
        pkgs_names = list(filter(rm_pkg, pkgs_names))
        pkgs_dpnds = ['snap-store', ]
        pkgs_names, pkgs_dpnds = set(pkgs_names), set(pkgs_dpnds)
        pkgs_names = pkgs_names - pkgs_dpnds
        self.pkgs_names, self.pkgs_dpnds = pkgs_names, pkgs_dpnds


def main() -> None:
    """Run all the necessary methods.

    :return: None.
    """
    MarkedPackages().main()
    LogsPackages().main()
    SnapPackages().main()

    pkgs_names, pkgs_dpnds = PackageManager.sum_pkgs()
    struct_pkgs = PackageManager.struct_pkgs(pkgs_names)
    struct_pkgs['full_pkgs'] = pkgs_names
    struct_pkgs['full_dpnds'] = pkgs_dpnds
    PackageManager.save_data(**struct_pkgs)


if __name__ == '__main__':
    main()
