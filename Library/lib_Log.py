'''
        Library to show fancy text-layout in the console
'''
import logging
import inspect
import logging.handlers

import sys
import os

import lib_Log


class consoleColors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        ERROR = '\033[91m'
        FAIL = '\033[91m'
        BOLD = '\033[1m'
        DEBUG = '\033[2m'
        ITALIC = '\033[3m'
        UNDERLINE = '\033[4m'
        ENDC = '\033[0m' #end colors

def Banner(WriteToFile = True):
        
        color1 = consoleColors.OKGREEN
        color2 = consoleColors.ERROR
        colorEND = consoleColors.ENDC
        colorUNDERLINE = consoleColors.UNDERLINE
        hashTags = " " + color1
        if WriteToFile:
                color1 = ""
                color2 = ""
                colorEND = ""
                colorUNDERLINE = ""
                hashTags = "# "
                
        String = ""
        String += hashTags + "          _ _       ___           ___                  \n"
        String += hashTags + "         | | | ___ | . \ ___ " + color2 + " ___" + color1 + "|_ _|___  ___  _ _ _  \n"
        String += hashTags + "         |   |/ ._>|   // . \\" + color2 + "|___|" + color1 + "| |/ ._><_> || ' ' | \n"
        String += hashTags + "         |_|_|\___.|_\_\\\___/     |_|\___.<___||_|_|_| \n\n" +  colorUNDERLINE
        String += hashTags + "                                                                \n"
        String += hashTags + colorUNDERLINE + "Created by HeRo-Team in colaboration with Radio-Holland-Belgium \n\n"
        String += colorEND
        return String
def FileWarning():
        String = ""
        String += "#---< Do not touch >---\n"
        String += "#This File is autogenerated by RHBOX \n\n\n"
        return String

def getLogger(name='root',LOG_FILENAME = 'log/RHBOX.log'):

        if name == "__main__":
                logger = logging.getLogger("Main")
                # if logger 'name' already exists, return it to avoid logging duplicate
                # messages by attaching multiple handlers of the same type

                if logger.handlers:
                        return logger
                # if logger 'name' does not already exist, create it and attach handlers


                logger.setLevel(logging.DEBUG)

                # create handler
                handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=5242880, backupCount=10)
                #Formatter = logging.Formatter(fmt='%(asctime)s\t%(threadName)s\t' + "{0:<{1}}".format(moduleName[:30],30) + '\t%(levelname)-8s\t%(message)s',datefmt='%m-%d %H:%M:%S')
                Formatter = logging.Formatter(fmt='%(asctime)s\t%(threadName)s\t%(name)-30s\t%(levelname)-8s\t%(message)s',datefmt='%m-%d %H:%M:%S')
                handler.setFormatter(Formatter)
                # add handler to logger
                logger.addHandler(handler)
        else:

                logger = logging.getLogger("Main." + name)

        return logger

class Log:
        def __init__(self, PrintToConsole = False, level = 1, LOG_FILENAME = 'log/RHBOX.log'):
                self.PrintToConsole = PrintToConsole
                self.level = level
                frame = inspect.stack()[1]
                module = inspect.getmodule(frame[0])
                self.logger = lib_Log.getLogger(module.__name__,LOG_FILENAME)

        def increaseLevel(self):
                self.level += 1

        def decreaseLevel(self):
                if self.level > 0:
                        self.level -= 1

        def setLevel(self, level):
                self.level = level

        def resetLevel(self):
                self.level = 1

        def disablePrintToConsole(self):
                self.PrintToConsole = False

        def enablePrintToConsole(self):
                self.PrintToConsole = True

        def mainTitle(self, string):
                self.level = 0
                """Show title"""
                self.logger.info(string.upper())

                if self.PrintToConsole:
                        print(consoleColors.UNDERLINE + consoleColors.BOLD + consoleColors.HEADER + string.upper() + consoleColors.ENDC)

                return

        def subTitle(self, string, Warning = False, Error = False):
                self.level = 0
                """print subtitle"""
                prefix = ""
                if Warning:
                        self.logger.warning("  " * self.level + string)
                        prefix = consoleColors.WARNING
                elif Error:
                        self.logger.error("  " * self.level + string)
                        prefix = consoleColors.ERROR
                else:
                        self.logger.info(string)
                        prefix = consoleColors.OKBLUE

                if self.PrintToConsole:
                        print("  " * self.level + prefix + consoleColors.BOLD + string + consoleColors.ENDC)
                self.level += 1
                return

        def printError(self,string):
                """print error"""

                self.logger.error(string)

                if self.PrintToConsole:
                        print("  " * self.level + consoleColors.ERROR + string + consoleColors.ENDC)

        def printWarning(self,string):
                """print warning"""

                self.logger.warning("  " * self.level + string)

                if self.PrintToConsole:
                        print("  " * self.level + consoleColors.WARNING + string + consoleColors.ENDC)

        def printInfo(self,string):
                """print default text"""

                self.logger.info("  " * self.level + string)

                if self.PrintToConsole:
                        print("  " * self.level + string)

        def printBoldInfo(self, string):
                """print bold default text"""

                self.logger.info("  " * self.level + string)
                if self.PrintToConsole:
                        print("  " * self.level + consoleColors.BOLD + string + consoleColors.ENDC)

        def printUnderlinedInfo(self, string):
                """print bold default text"""

                self.logger.info("  " * self.level + string)

                if self.PrintToConsole:
                        print("  " * self.level + consoleColors.UNDERLINE + string + consoleColors.ENDC)

        def printDebug(self, string):
                """print debug"""

                self.logger.debug(string)

                print(consoleColors.DEBUG + consoleColors.UNDERLINE + "--START DEBUG--" + consoleColors.ENDC)
                print(consoleColors.DEBUG + string)
                print(consoleColors.DEBUG + consoleColors.UNDERLINE + "--END DEBUG--" + consoleColors.ENDC)

        def printOK(self, string):
                """print OK"""
                #self.level = 2

                self.logger.info("  " * self.level + string)

                if self.PrintToConsole:
                        print("  " * self.level + consoleColors.OKGREEN + string + consoleColors.ENDC)

        def ConsoleLayoutDemo(self):
                """ Prints a couple of examples """
                maintitle("Main Title")
                subtitle("Sub Title Default")
                subtitle("Sub Title self.level 0",0)
                subtitle("Sub Title self.level 1",1)
                subtitle("Sub Title self.level 2",2)
                subtitle("Sub Title - Error", Error = True)
                subtitle("Sub Title self.level 2 - Warning",2, Warning = True)
                printError("Error")
                printError("Error lvl 0", 0)
                printError("Error lvl 1", 1)
                printError("Error lvl 2", 2)
                printWarning("Warning")
                printWarning("Warning lvl 0", 0)
                printWarning("Warning lvl 1", 1)
                printWarning("Warning lvl 2", 2)
                printText("Text")
                printText("Text lvl 0", 0)
                printText("Text lvl 1", 1)
                printText("Text lvl 2", 2)
                printBoldText("Bold Text")
                printUnderlinedText("Underlined Text")
                printDebug("Debug Text")
                printOK("OK Text")
                printText("Mixed " + consoleColors.ITALIC + "Text" + consoleColors.OKBLUE + ", end" + consoleColors.ERROR + " always" + consoleColors.OKGREEN + " with" + consoleColors.BOLD + " ENDC"+ consoleColors.ENDC)
                return
