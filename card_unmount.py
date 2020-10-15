#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pwd
import subprocess


class SimpleUmout:
    """Simple class to umount user device.

    :attr DEVICES_FOLDER: Directory where devices to umount are located.
    :attr DEVICE_NAME: Name of device for umount.
    :attr USERNAME: Name of current system user.
    :attr PATH: Full path where stored user devices.
    :attr MOUNTS: List of all user mounted devices.
    :attr LOGS: Simple log file for all scripts.
    """

    def __init__(self) -> None:
        """Magick method for initial class instance.

        :return: None.
        """
        self.DEVICES_FOLDER: str = '/media/'
        self.DEVICE_NAME: str = os.getenv('MOUNT_CARD')
        self.USERNAME: str = pwd.getpwuid(os.getuid())[0]
        self.PATH: str = f'{self.DEVICES_FOLDER}/{self.USERNAME}'
        self.MOUNTS: list = os.listdir(self.PATH)
        self.LOGS: str = 'logs.txt'
        if not os.path.exists(self.LOGS):
            os.mknod(self.LOGS)

    def main(self) -> None:
        """Umount user device.

        :return: None.
        """
        if len(self.MOUNTS) != 0 and self.DEVICE_NAME in self.MOUNTS:
            umount_path = f'{self.PATH}/{self.DEVICE_NAME}'
            try:
                subprocess.run(['umount', umount_path])
            except Exception as e:
                with open(self.LOGS, 'a') as file:
                    file.write(str(e)+'\n')


if __name__ == '__main__':
    SimpleUmout().main()
