"""
    Various OS functions

    @author: jldupont
    @created on 2011-03-01
        
    e.g.
    [['rootfs', '/', 'rootfs', 'rw', '0', '0'], 
    ['none', '/sys', 'sysfs', 'rw,nosuid,nodev,noexec,relatime', '0', '0'], 
    ['none', '/proc', 'proc', 'rw,nosuid,nodev,noexec,relatime', '0', '0'], 
    ['none', '/dev', 'devtmpfs', 'rw,relatime,size=3079056k,nr_inodes=195142,mode=755', '0', '0'], 
    ['none', '/dev/pts', 'devpts', 'rw,nosuid,noexec,relatime,gid=5,mode=620,ptmxmode=000', '0', '0'], 
    ['fusectl', '/sys/fs/fuse/connections', 'fusectl', 'rw,relatime', '0', '0'], 
    ['/dev/disk/by-uuid/0b337c64-1d0c-4aaf-85d0-33aef31e801f', '/', 'ext4', 'rw,relatime,errors=remount-ro,barrier=1,data=ordered', '0', '0'], 
    ['none', '/sys/kernel/debug', 'debugfs', 'rw,relatime', '0', '0'], ['none', '/sys/kernel/security', 'securityfs', 'rw,relatime', '0', '0'], 
    ['none', '/dev/shm', 'tmpfs', 'rw,nosuid,nodev,relatime', '0', '0'], ['none', '/var/run', 'tmpfs', 'rw,nosuid,relatime,mode=755', '0', '0'], 
    ['none', '/var/lock', 'tmpfs', 'rw,nosuid,nodev,noexec,relatime', '0', '0'], 
    ['binfmt_misc', '/proc/sys/fs/binfmt_misc', 'binfmt_misc', 'rw,nosuid,nodev,noexec,relatime', '0', '0'], 
    ['//NAS/Music/', '/mnt/music', 'cifs', 'rw,mand,relatime,unc=\\\\NAS\\Music,username=guest,uid=0,noforceuid,gid=0,noforcegid,addr=192.168.1.114,posixpaths,serverino,acl,rsize=16384,wsize=57344', '0', '0'], 
    ['/home/jldupont/.Private', '/home/jldupont', 'ecryptfs', 'rw,relatime,ecryptfs_fnek_sig=e7f453e7385cb95c,ecryptfs_sig=8140b505545d9f98,ecryptfs_cipher=aes,ecryptfs_key_bytes=16', '0', '0'], 
    ['gvfs-fuse-daemon', '/home/jldupont/.gvfs', 'fuse.gvfs-fuse-daemon', 'rw,nosuid,nodev,relatime,user_id=1000,group_id=1000', '0', '0'], 
    ['/dev/sdb1', '/media/2TB_280810', 'ext4', 'rw,nosuid,nodev,relatime,barrier=1,data=ordered', '0', '0'], ['']]
"""

__all__=[]

_filters=["rootfs", "none", "/dev/sd", "binfmt_misc", "gvfs", "fuse", "/dev/disk"]

def mounts():
    """
    Retrieves the mount points
    
    @return: list of [src_path, mount_point, filesystem_type, options, p1, p2]
    """
    file=open("/proc/mounts", "r")
    _mounts=file.read().split("\n")
    file.close()
    
    result=[]
    for mount in _mounts:
        bits=mount.split(' ')
        if len(bits) > 1:
            result.append(bits)
    return result

def lookup_mount(path, allmounts=None, matchstart=False, trylowercase=False):
    """
    Lookup a mount record for the specified path
    @returns: None or [mount ...] 
    """
    if allmounts is None:
        allmounts=mounts()
        
    for mount in allmounts:
        if mount[0]==path:
            return mount
        if matchstart:
            if path.startswith(mount[0]):
                return mount
            
        if trylowercase:
            if mount[0].lower()==path.lower():
                return mount
        if matchstart:
            if path.lower().startswith(mount[0].lower()):
                return mount
            
    return None



def filtered_mounts(allmounts=None):
    """
    Returns a 'sanitized' list of mounts
    """
    skip=False
    result=[]
    if allmounts is None:
        allmounts=mounts()
    for mount in allmounts:
        
        for filter in _filters:
            if mount[0].startswith(filter):
                skip=True
                break
        if not skip:
            result.append(mount)
        skip=False
        
    return result
            

if __name__=="__main__":
    print mounts()
    
    print lookup_mount("//NAS/Music/", trylowercase=True)
    print lookup_mount("//NAS/Music/", trylowercase=True)==lookup_mount("//nas/music/", trylowercase=True)

    print lookup_mount("//NAS/Music/_lib", matchstart=True, trylowercase=True)            
    print lookup_mount("//NAS/Music/_lib", matchstart=True, trylowercase=True)==lookup_mount("//nas/music/_lib", matchstart=True, trylowercase=True)            

    print filtered_mounts()
    