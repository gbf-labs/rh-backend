import os
import sys
import subprocess

def Bash(Command):

    if isinstance(Command, str):
        Command = [Command]
    elif not isinstance(Command, list):
        return True
            
    for SubCommand in Command:
        
        CommandList = SubCommand.split()
        with open(os.devnull, 'w') as DEVNULL:
            
            try:
                
                subprocess.check_call(
                    CommandList,
                    stdout=DEVNULL,  # suppress output
                    stderr=DEVNULL
                )
                                    
            except subprocess.CalledProcessError:
                return True

    return False