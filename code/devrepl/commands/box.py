import glob
from ftplib import FTP_TLS
from pathlib import Path

from tqdm import tqdm
from proc import cmd
from util import rm, rm_recursive
import console_output as out
from . import ReplCommand
from . import pentaho


class Box(ReplCommand):

    def do_set_box_info(self, arg):
        self.session['box_host'] = input('Box FTPS Server (ftp.box.com):')
        self.session['box_user'] = input('Box Username:')
        self.session['box_pwd'] = input('Box Password:')
        self.session['ci_root'] = input('CI Root Dir (e.g. /CI/9.0-QAT/):')
        self.session['bi_version'] = input('BI version (e.g. 9.0.0.0):')

    def do_get_qat(self, arg):
        ftps = FTP_TLS(host=self.session['box_host'], user=self.session['box_user'], passwd=self.session['box_pwd'])

        builds = list(ftps.mlsd(self.session['ci_root']))
        builds.sort(key=lambda entry: entry[1]['modify'], reverse=True)

        out.info("Retrieving build number " + builds[2][0])

        build_num = builds[2][0]
        prev_build_num = builds[3][0]

        path_to_installer = self.path_to_installer_for_build(build_num)
        local_filename = self.session['dot_dir'] + '/pentaho-business-analytics.app.tar.gz'

        rm(local_filename)
        try:
            self.retrieve_file(ftps, local_filename, path_to_installer)
        except:
            out.error('Failed to get build ' + build_num + '.\nTrying to get build ' + prev_build_num)
            path_to_installer = self.path_to_installer_for_build(prev_build_num)
            try:
                self.retrieve_file(ftps, local_filename, path_to_installer)
            except:
                out.error('Failed to get build ' + prev_build_num)


    def path_to_installer_for_build(self, build_num):
        filename = "pentaho-business-analytics-{}-{}-x64.app.tar.gz".format(self.session['bi_version'], build_num)
        path_to_installer = self.session['ci_root'] + build_num + "/ee/installers/" + filename
        return path_to_installer

    def retrieve_file(self, ftps, local_filename, remote_filename):
        localfile = open(local_filename, 'wb')
        total_size = ftps.size(remote_filename)
        out.info("writing to " + local_filename + ", size:  " + str(total_size / 1024 / 1024) + "M")
        pbar = tqdm(total=total_size)
        ftps.retrbinary('RETR ' + remote_filename, self.progress_wrapper(pbar, localfile.write), 1024)
        ftps.close()
        localfile.close()

    def do_install_qat(self, arg):
        pentaho.stop_pentaho_server(self.session['dot_dir'] + 'qat')
        rm_recursive(self.session['dot_dir'] + '/temp')
        # cmd(['find', '.', '!', '-name', "'.*'", '-maxdepth', '1', '-exec', 'rm', '-rf', '"{}"', ';'],
        #     self.session['dot_dir'] + 'qat')
        cmd(['rm', '-rf', self.session['dot_dir'] + 'qat'])
        cmd(['mkdir', 'qat'], self.session['dot_dir'])
        cmd(['mkdir', 'temp'], self.session['dot_dir'])
        cmd(['tar', 'xvzf', 'pentaho-business-analytics.app.tar.gz', '-C', self.session['dot_dir'] + 'temp'],
            self.session['dot_dir'])

        # find builder
        installer = [file for file in
                     glob.iglob(self.session['dot_dir'] + 'temp/' + '**/installbuilder.sh', recursive=True)]
        if len(installer) != 1:
            print('Couldn''t find installer.\n' + str(installer))
            return
        installer_dir = Path(installer[0]).parent.as_posix()
        cmd(['./installbuilder.sh', '--unattendedmodeui', 'minimal',
             '--mode', 'unattended', '--prefix',
             '{}qat'.format(self.session['dot_dir']), '--debuglevel', '4', '--postgres_password', 'password',
             '--installsampledata', '1'], installer_dir)
        # remove .installedLicenses so the shared one in ~/.pentaho will be used
        cmd(['rm', self.session['dot_dir'] + 'qat/.installedLicenses.xml'])
        # skip the eula
        cmd(['rm', self.session['dot_dir'] + 'qat/server/pentaho-server/promptuser.sh'])



    def do_get_install_qat(self, arg):
        self.do_get_qat(arg)
        self.do_install_qat(arg)

    def progress_wrapper(self, pbar, write_fun):
        def callback(data):
            pbar.update(1024)
            write_fun(data)

        return callback

    def prompt_str(self):
        return None
