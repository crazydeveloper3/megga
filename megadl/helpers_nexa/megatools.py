# Copyright (c) 2022 Itz-fork
# Don't kang this else your dad is gae

import os
import subprocess

from functools import partial
from asyncio import get_running_loop

from megadl import meganzbot
from config import Config


class MegaTools:
    """
    Helper class to interact with megatools cli

    Author: https://github.com/Itz-fork
    Project: https://github.com/Itz-fork/Mega.nz-Bot
    """

    def __init__(self, cache_first=True) -> None:
        self.config = "cache/config.ini"
        if cache_first and not os.path.isfile(self.config):
            self.genConfig()
        else:
            print("\nConfig validation wasn't performed as 'cache_first=False'. Program won't work if the config was missing or corrupted!\n")

    async def download(self, *dargs, path="MegaDownloads"):
        """
        Download file/folder from given link

        Arguments:
            link: string - Mega.nz link of the content
            *dargs - Chat id and message id
            path (optional): string - Path to where the content need to be downloaded
        """
        if await self.__is_account():
            cmd = f"megadl --config {self.config} --path {path} {dargs[0]}"
        else:
            cmd = f"megadl --path {path} {dargs[0]}"
        await self.runCmd(cmd, True, dargs[1], dargs[2])
        return [val for sublist in [[os.path.join(i[0], j) for j in i[2]] for i in os.walk(path)] for val in sublist]

    async def makeDir(self, path):
        """
        Make directories

        Arguments:
            path: string - Name of the directory
        """
        cmd = f"megamkdir --config {self.config} /Root/{path}"
        await self.runCmd(cmd)

    async def upload(self, *uargs, m_path="MegaBot"):
        """
        Upload files

        Arguments:
            *uargs - Chat id and message id
            m_path (optional): string - Custom path to where the files need to be uploaded
        """
        if not await self.__is_account():
            raise NoMegaAccountFound("Mega.nz email or password is missing")
        if not os.path.isfile(uargs[0]):
            raise UploadFailed(self.__genErrorMsg(
                "Given path isn't belong to a file."))
        # Checks if the remote upload path is exists
        if not f"/Root/{m_path}" in await self.runCmd(f"megals --config {self.config} /Root"):
            await self.makeDir(m_path)
        ucmd = f"megaput --config {self.config} --disable-previews --no-ask-password --path \"/Root/{m_path}\" \"{uargs[0]}\""
        await self.runCmd(ucmd, True, uargs[1], uargs[2])
        lcmd = f"megaexport --config {self.config} \"/Root/{m_path}/{os.path.basename(uargs[0])}\""
        ulink = await self.runCmd(lcmd)
        if not ulink:
            raise UploadFailed(self.__genErrorMsg(
                "Upload failed due to an unknown error."))
        return ulink

    async def runCmd(self, cmd, *args):
        """
        Run synchronous functions in a non-blocking coroutine

        Arguments
            cmd: str - Command to execute
        """
        loop = get_running_loop()
        return await loop.run_in_executor(
            None,
            partial(self.__shellExec, cmd, args)
        )

    async def __is_account(self):
        if Config.MEGA_EMAIL and Config.MEGA_PASSWORD:
            return True
        return False

    def genConfig(self, sp_limit=0):
        """
        Function to generate 'config.ini' file

        Arguments:
            sp_limit: int - Maximum speed limit for both download and upload
        """
        if os.path.isfile(self.config):
            print("\n'config.ini' file was found. Applying changes!\n")
        else:
            print("\nNo 'config.ini' file was found. Creating a new config file...\n")
        # Creating the config file
        conf_temp = f"""
[Login]
Username = {Config.MEGA_EMAIL}
Password = {Config.MEGA_PASSWORD}

[Cache]
Timeout = 10

[Network]
SpeedLimit = {sp_limit}

[Upload]
CreatePreviews = false
"""
        f = open(self.config, "w+")
        f.write(conf_temp)
        f.close()

    def __shellExec(self, cmd, rdata=None):
        run = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True, encoding="utf-8")
        if rdata and rdata[0]:
            # Live process info update
            while run.poll() is None:
                rsh_out = run.stdout.readline()
                if rsh_out != "":
                    try:
                        meganzbot.edit_message_text(
                            rdata[1],
                            rdata[2],
                            f"**Process info:** \n`{rsh_out}`"
                        )
                    except:
                        pass
        else:
            sh_out = run.stdout.read()[:-1]
            self.__checkErrors(sh_out)
            return sh_out

    def __genErrorMsg(self, bs):
        return f"""
>>> {bs}

Please make sure that you've provided the correct username and password.

You can open a new issue if the problem persists - https://github.com/Itz-fork/Mega.nz-Bot/issues
        """

    def __checkErrors(self, out):
        if "not found" in out:
            raise MegatoolsNotFound(
                "'megatools' cli is not installed in this system. You can download it at - https://megatools.megous.com/")

        elif "Can't create directory" in out:
            raise UnableToCreateDirectory(self.__genErrorMsg(
                "The program wasn't able to create the directory you requested for."))
        elif "No directories specified" in out:
            raise UnableToCreateDirectory(
                self.__genErrorMsg("No directory name was given."))

        elif "Upload failed" in out:
            raise UploadFailed(self.__genErrorMsg(
                "Uploading was cancelled due to an (un)known error."))
        elif "No files specified for upload" in out:
            raise UploadFailed(self.__genErrorMsg(
                "Path to the file which need to be uploaded wasn't provided"))

        elif "Can't login to mega.nz" in out:
            raise LoginError(self.__genErrorMsg(
                "Unable to login to your mega.nz account."))

        elif "ERROR" in out:
            raise UnknownError(self.__genErrorMsg(
                "Operation cancelled due to an unknown error."))

        else:
            return


# Errors

class MegatoolsNotFound(Exception):
    pass


class UnableToCreateDirectory(Exception):
    pass


class UploadFailed(Exception):
    pass


class NoMegaAccountFound(Exception):
    pass


class LoginError(Exception):
    pass


class UnknownError(Exception):
    pass
