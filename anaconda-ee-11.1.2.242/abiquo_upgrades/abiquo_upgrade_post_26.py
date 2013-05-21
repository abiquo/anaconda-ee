import os
import iutil
import shutil
import logging
import ConfigParser
import time
import re
from subprocess import *

log = logging.getLogger("anaconda")

def abiquo_upgrade_post(anaconda):

    schema_path = anaconda.rootPath + "/usr/share/doc/abiquo-server/database/kinton-2.6.0-delta.sql"
    work_path = anaconda.rootPath + "/opt/abiquo/tomcat/work"
    temp_path = anaconda.rootPath + "/opt/abiquo/tomcat/temp"
    mysql_path = anaconda.rootPath + "/etc/init.d/mysql"
    xen_path = anaconda.rootPath + "/etc/xen"
    xen_kernel = '/xen.gz-3.4.2'

    log.info("ABIQUO: Post install steps")
    # Clean tomcat 
    if os.path.exists(work_path):
        log.info("ABIQUO: Cleaning work folder...")
        for f in os.listdir(work_path):
            fpath = os.path.join(work_path,f)
            try:
                if os.path.isfile(fpath):
                    os.unlink(fpath)
                else:
                    shutil.rmtree(fpath)
            except Exception, e:
                print e
    if os.path.exists(temp_path):
        log.info("ABIQUO: Cleaning temp folder...")
        for f in os.listdir(temp_path):
            fpath = os.path.join(temp_path,f)
            try:
                if os.path.isfile(fpath):
                    os.unlink(fpath)
                else:
                    shutil.rmtree(fpath)
            except Exception, e:
                print e

    # Upgrade database if this is a server install and MariaDB exists
    if os.path.exists(schema_path) and os.path.exists(mysql_path):
        log.info("ABIQUO: Updating Abiquo database...")
        # log debug
        iutil.execWithRedirect("/sbin/ifconfig",
                                ['lo', 'up'],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        iutil.execWithRedirect("/etc/init.d/mysql",
                                ['start'],
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        time.sleep(6)
        schema = open(schema_path)
        iutil.execWithRedirect("/usr/bin/mysql",
                                ['kinton'],
                                stdin=schema,
                                stdout="/mnt/sysimage/var/log/abiquo-postinst.log", stderr="/mnt/sysimage/var/log/abiquo-postinst.log",
                                root=anaconda.rootPath)
        schema.close()


    if os.path.exists(xen_path):
        # replace default kernel entry 
        log.info("ABIQUO: Updating XEN grub entry ...")
        f = open(anaconda.rootPath + '/boot/grub/menu.lst')
        buf = f.readlines()
        f.close()
        fw = open(anaconda.rootPath + '/boot/grub/menu.lst', 'w')
        for line in buf:
            fw.write(re.sub('\/xen.gz-2.6.18.*',
                            xen_kernel,
                            line))
        fw.close()


    # restore fstab
    backup_dir = anaconda.rootPath + '/opt/abiquo/backup/2.4.0'
    if os.path.exists('%s/fstab.anaconda' % backup_dir):
        shutil.copyfile("%s/fstab.anaconda" % backup_dir,
                '%s/etc/fstab' % anaconda.rootPath)
