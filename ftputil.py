import ftplib

class FTPUtil:
    def __init__(self, ftpconfig, logger):
        self.logger=logger
        self.ftp=ftplib.FTP(ftpconfig['server'],
                            user=ftpconfig['username'],
                            passwd=ftpconfig['password'],
                            timeout=60)

    def recursive_mkd_cwd(self,path):
        """ like mkdir -p $path && cd $path """
        if path[0]=='/':
            self.ftp.cwd('/')
            path=path[1:]
        for seg in path.split("/"):
            try:
                self.ftp.cwd(seg)
            except ftplib.error_perm:
                self.ftp.mkd(seg)
                self.ftp.cwd(seg)

    def mkd_cwd(self,path):
        try:
            self.ftp.mkd(path)
        except ftplib.error_perm:
            self.logger.warn('failed to create dir '+path)
        self.ftp.cwd(path)
        return self.ftp.pwd()
    def upload(self, filename, fileobj, blocksize, callback):
        self.ftp.storbinary("STOR "+filename,fileobj,blocksize=blocksize,callback=callback)
        


