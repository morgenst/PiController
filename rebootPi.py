__author__ = 'Marcus Matthias Morgenstern'
__mail__ = 'marcus.matthias.morgenstern@cern.ch'
__date__ = 'September, 16th, 2015'
__version__ = '1.0'

import argparse
import getpass
import pexpect
import pxssh
import sys


class LoginException(Exception):
    def __init__(self, msg):
        self.msg = msg

class ProcessException(Exception):
    def __init__(self,msg):
        self.msg =msg

class SSHHandle:
    def __init__(self, uName, pwd):
        self.user = uName
        self.pwd = pwd
        self.connection = pxssh.pxssh()
        self.connection.SSH_OPTS += " -o StrictHostKeyChecking=no"
        self.connection.force_password = True
        self.cmd = "reboot"

    def __login(self, server):
        try:
            self.connection.login(server, self.user, self.pwd)
        except pexpect.EOF as e:
            raise LoginException('LoginFailure at server %s' % server)

    def close(self):
        if not self.connection.isalive():
            return
        self.connection.logout()
        self.connection.close()

    def reboot(self, server):
        try:
            self.__login(server)
        except LoginException:
            raise
        self.connection.sendline(self.cmd)
        self.connection.expect(self.connection.PROMPT, timeout=10)
        prompt = self.connection.before
        if prompt.find('Need to be root'):
            self.close()
            raise ProcessException('Need to be root')
        self.close()


def main(argv):
    parser = argparse.ArgumentParser(description='Script to reboot remote server')
    parser.add_argument('--serverlist', '-sl', type=str, default="serverlist.txt", help='Text file containing servers to reboot')
    parser.add_argument('--listfailed', '-lf', action='store_true', default=False, help='Print list of failed connections')
    failedConnections = []
    args = parser.parse_args()
    try:
        f = open(args.serverlist)
    except IOError:
        print 'File %s supposed to contain server list does not exist.' % args.serverlist
        exit(1)
    servers = [s for s in f.readlines()]
    uName = raw_input('Enter user name: ')
    pwd = getpass.getpass('Enter password: ', sys.stdout)
    handle = SSHHandle(uName, pwd)
    for server in servers:
        try:
            handle.reboot(server)
        except (LoginException, ProcessException) as e:
            print e.msg
            failedConnections.append(server)
            continue

    if len(failedConnections) == 0:
        print 'Succeded to reboot %i servers' % len(servers)
    else:
        print 'Failed on %i servers. Call with -lf option to list failed connections.' % len(failedConnections)
        if args.listfailed:
            for fc in failedConnections:
                print fc

if __name__ == '__main__':
    main(sys.argv[1:])
