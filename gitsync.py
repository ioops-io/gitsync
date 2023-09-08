#!/usr/bin/env python3
#

#
# Gitsync
#

import argparse
from distutils.command.config import config
import yaml
from pathlib import Path
import os
import subprocess
import io
import re
import sys, traceback
import shutil
from pathlib import PurePath
from pprint import pprint
from datetime import datetime 
import time

git = '/usr/bin/git'
rsync = '/usr/bin/rsync' 

parser = argparse.ArgumentParser(description='Gitsync :: A GIT syncronizer between two unrelated git repositories')
parser.add_argument('-f', dest='configFile', help='Gitsync configuration file.')
parser.add_argument('-workdir', dest='workdirPath', help='Path to workdir directory (override all other configuration).')
args = parser.parse_args()

#
# Check git version
#
def check_gitVersion():
    result = subprocess.run([git, '--version'], capture_output=True, stdout=subprocess.PIPE, text=True)
    if result.returncode == 0:
        buf = io.StringIO(result.stdout)
        line = buf.readline()
        version = line.split()
        release = version[2].split()
        if ((release[0] >= 2) and (release[1] >= 0)):
            return True
        else:
            return False
    else:
        return False
    
def check_rsyncVersion():
    result = subprocess.run([rsync, '--version'], capture_output=True, stdout=subprocess.PIPE, text=True)
    if result.returncode == 0:
        buf = io.StringIO(result.stdout)
        line = buf.readline()
        version = line.split()
        release = version[2].split()
        if ((release[0] >= 2) and (release[1] >= 4)):
            return True
        else:
            return False
    else:
        return False

#
# Execute a process or rollback process in case of failure
#
def run_shell(execute, workdir, rollback = None):

    # print('------------------------------------ Debug execute')
    # pprint(execute)
    # print('------------------------------------ Debug execute')
    execRun = subprocess.run(execute, cwd=workdir)

    if execRun.returncode != 0:
        print('Shell execution error: Exit code = ' + str(execRun.returncode))

        if rollback is not None:
            print('  Rollback previous command.')
            execRollback = subprocess.run(rollback, 
                cwd=workdir, 
                capture_output=True)

#
# Read configuration file
#
def read_config(filename, workdir = None):

    #print('DEBUG check_file ' + filename)

    if ((filename.endswith('.yaml')) or (filename.endswith('.yml'))):

        p = None
        if workdir is None:
            p = Path(filename)
        else:
            p = Path(workdir, filename)

        if p.resolve().is_file():
            try:
                return yaml.safe_load(p.read_text())
            except Exception as e:
                ex_type, ex_value, ex_traceback = sys.exc_info()
                print('Exception reading configuration: ' + str(ex_value))
            
    return None

def parse_config(gitsync):

    if gitsync is None:
        print("Config has no gitsync section.")
        return False
    
    if (gitsync['workdir'] is None):
         print("Workdir is required.")
         return False
    
    path = Path(gitsync['workdir'])
    absolutePath = path.expanduser().resolve()
    gitsync['workdir'] = str(absolutePath)

    if ((gitsync['strategy'] != 'update') and (gitsync['strategy'] != 'create-branch')):
        print("Unsuported strategy '" + gitsync['strategy'] + "'. Please set update or create-branch in config.")
        return False
    
    if (gitsync['source'] is None):
        print("Source section is required.")
        return False
    
    if (gitsync['source']['repository'] is None):
        print("Source repository is required.")
        return False
    
    if gitsync['source']['repository'].startswith("http"):
         print("Source repository is URL Address. Clonning repository first.")
         print("TODO Implement")
         exit(1)

    path = Path(os.path.join(config['workdir'], gitsync['source']['repository']))
    absolutePath = path.expanduser().resolve()
    gitsync['source']['repository'] = str(absolutePath)

    if (os.path.isdir(gitsync['source']['repository']) is False):
        print("Source repository does not exist or is not a directory.")
        return False
    
    if (gitsync['source']['path'] is None):
            print("Source path is required.")
            return False

    if (gitsync['source']['branch'] is None):
            print("Source branch is required.")
            return False
    
    if (gitsync['target'] is None):
        print("Target section is required.")
        return False
    
    if (gitsync['target']['repository'] is None):
        print("Target repository is required.")
        return False

    path = Path(os.path.join(config['workdir'], gitsync['target']['repository']))
    absolutePath = path.expanduser().resolve()
    gitsync['target']['repository'] = str(absolutePath)

    if (os.path.isdir(gitsync['target']['repository']) is False):
            print("Target repository does not exist or is not a directory.")
            return False

    if (gitsync['target']['path'] is None):
            print("Target path is required.")
            return False

    if (gitsync['target']['branch'] is None):
            print("Target branch is required.")
            return False
    
    return True

def generate_source_log(config):

    out = open(os.path.join(config['workdir'], ".gitsync.log"), "w")
    out.write("This folder was sincronized by Gitsync\n")

    gitSource = subprocess.run([git, 'ls-remote', '--get-url', 'origin'], 
        cwd=config['source']['repository'],
        stdout=subprocess.PIPE,
        text=True)

    if gitSource.returncode == 0:
        buf = io.StringIO(gitSource.stdout)
        line = buf.readline()
        out.write("Source repository: " + line)

    out.write("Source branch: " + config['source']['branch'] + "\n")
    out.write("Source path: " + config['source']['path'] + "\n")
        
    changeLog = subprocess.run([git, 'log', '--name-status', '-1', '--no-color'], 
        cwd=config['source']['repository'],
        stdout=subprocess.PIPE,
        text=True)

    if changeLog.returncode == 0:
        buf = io.StringIO(changeLog.stdout)
        line = buf.readline()
        while line:
            if re.match(r'^commit ', line):
                commit = line.split(' ', 1)[1]
                out.write("Source latest commit: " + commit)
            elif re.match(r'^Author: ', line.strip()):
                out.write(line)
            elif re.match(r'^Date: ', line.strip()):
                out.write(line)
            line = buf.readline()

    out.close()

print('Gitsync starting...')

#
# Main
#
if args.configFile is not None:
    config = read_config(args.configFile)["gitsync"]

    #Override workdir
    if args.workdirPath is not None:
        print('Setting workdir from parameters: ' + args.workdirPath)
        config['workdir'] = args.workdirPath
    else:
        print('Using workdir from configuration: ' + str(config['workdir']))


    if parse_config(config) is False:
         print('Configuration is invalid.')
         exit(1)

    if not os.path.isdir(config['workdir']):
        os.mkdir(config['workdir'])
        print('Creating workdir ' + config['workdir'])

    print('')
    print('1/4: Initializing source: fetch -> pull -> switch.')

    #Prepare source
    run_shell([git, 'fetch'], config['source']['repository'])
    run_shell([git, 'pull'], config['source']['repository'])
    run_shell([git, 'switch', config['source']['branch']], config['source']['repository'])
    generate_source_log(config)
    print('  Source initialized.')

    print('')
    print('2/4: Initializing target: fetch -> pull -> switch.')

    run_shell([git, 'fetch'], config['target']['repository'])

    if config['strategy'] == 'update':
        print('  Strategy is update, switching to branch: ' + config['target']['branch'] + '.')
        run_shell([git, 'switch', config['target']['branch']], config['target']['repository'])
        run_shell([git, 'pull'], config['target']['repository'])

    if config['strategy'] == 'create-branch':
        print('Strategy is create-branch, creating new branch sync/' + config['target']['path'] + ' from (' + config['target']['branch'] + ') and switching.')
        run_shell([git, 'switch', config['target']['branch']], config['target']['repository'])
        run_shell([git, 'pull'], config['target']['repository'])
        run_shell([git, 'branch', 'sync/' + config['target']['path']], config['target']['repository'])
        run_shell([git, 'switch', 'sync/' + config['target']['path']], config['target']['repository'])
    
    print('')
    print('3/4: Starting sync...')

    rsyncCommand = [rsync, '-avc']

    #--delete-excluded for mirror = true
    if config['sync']['mirror'] is True:
         rsyncCommand.append('--delete-excluded')

    path = Path(os.path.join(config['source']['repository'], config['source']['path']))
    absolutePath = path.expanduser().resolve()
    rsyncCommand.append(str(absolutePath) + os.sep)

    path = Path(os.path.join(config['target']['repository'], config['target']['path']))
    absolutePath = path.expanduser().resolve()
    rsyncCommand.append(str(absolutePath))

    run_shell(rsyncCommand, config['workdir'])

    shutil.copy(config['workdir'] + '/.gitsync.log', str(absolutePath) + '/.gitsync.log')
    
    print('')
    print('4/4: Commit changes...')

    now = datetime.now()
    dateTime = now.strftime("%d-%m-%Y, %H:%M:%S")

    run_shell([git, 'add', config['target']['path'], '-u'], config['target']['repository'])
    run_shell([git, 'add', config['target']['path'], '-A'], config['target']['repository'])
    run_shell([git, 'commit', '-m', 'Gitsync on ' + dateTime + ' commited differences.'], config['target']['repository'])
    if config['strategy'] == 'update':
        run_shell([git, 'push'], config['target']['repository'])

    elif config['strategy'] == 'create-branch':
        run_shell([git, 'push', '--set-upstream', 'origin', 'sync/' + config['target']['path']], config['target']['repository'])
    else:
        print('Unknown strategy to push.')