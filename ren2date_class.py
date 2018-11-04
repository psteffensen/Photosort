#!/usr/bin/pythond
import os, sys
import datetime
# from datetime import datetime, time as datetime_time, timedelta
import shutil
# import sys
import pickle
import re
import subprocess
import pyexiftool.exiftool
import operator

"""
Class of methods to sort photos.


I maybe should split it into a configution and sorting class.
The configuration is a disctionary and is saved and opened as a pickleself.

The next class is the sorting method of the photos. First a list of files to be
sorted must be created using the configurations.


from skimage.measure import structural_similarity as ssim

if not os.path.isdirNdestination):
   os.mkdir(destination)
"""


class Ren2Date(object):
    """Class for handling settings and the sorting photos."""

    def __init__(self):
        """Initialize the configuration variables."""
        self.conf = {}
        self.dest_folder = "/home/psteffensen/Documents/SortMyPhotos"
        self.previous_sort = None

    def save_conf(self, name):
        """Save the configuration as a pickle."""
        conf = self.conf
        pickle.dump(conf, open(name + ".conf", "wb"))

    def open_conf(self, name):
        """Open the configuration pickle."""
        self.conf = pickle.load(open(name + ".conf", "rb"))

    def db_save(self, key, value):
        """Scave value to database."""
        self.conf[key] = value

    def db_get(self, key):
        """Get a value from database."""
        return self.conf[key]

    def db_delete(self, key):
        del self.conf[key]

    def get_source(self):
        """
        Get the info to connect to device via USBself.

        I got this from Stack overflow:
        https://stackoverflow.com/questions/8110310/simple-way-to-query-connected-usb-devices-info-in-python
        """

        device_re = re.compile(
            'Bus\s+(?P<bus>\d+)\s+Device\s+(?P<device>\d+).+'
            'ID\s(?P<id>\w+:\w+)\s(?P<tag>.+)$', re.I
            )
        df = subprocess.check_output("lsusb")
        devices = []
        for i in df.split('\n'):
            if i:
                info = device_re.match(i)
                if info:
                    dinfo = info.groupdict()
                    # dinfo['device'] =
                    #    '/dev/bus/usb/%s/%s' % (dinfo.pop('bus'),
                    #    dinfo.pop('device'))
                    devices.append(dinfo)

        for index, dinfo in enumerate(devices):
            print str(index) + ' ' + dinfo['tag']
        print "local If pictures are on harddrive"
        dev_number = raw_input('which one is your device? ')

        if dev_number == 'local':
            empty_dict = {}
            empty_dict['device'] = ''
            empty_dict['bus'] = ''
            self.conf['device'] = empty_dict
            return empty_dict
        else:
            self.conf["device"] = devices[int(dev_number)]
            return devices[int(dev_number)]

    def add_folder(self, num, folder, device="", bus=""):
        """
        Add a folder to the configuration.

        To get to the files:
        For example for device usb 001,008
        cd  /run/user/1000/gvfs...
            .../mtp:host=%5Busb%3A001%2C008%5D/Internal shared storage
        I got this from :
        https://askubuntu.com/questions/342319/where-are-mtp-mounted-devices-located-in-the-filesystem
        """
        
        if device and bus:  # check for empty sting in device and bus
            full_path = "/run/user/1000/gvfs/mtp:host=%5Busb%3A" + \
                bus + "%2C" + device + folder
            self.conf["folder" + "_" + str(num)] = full_path
        else:
            full_path = folder
            self.conf["folder" + "_" + str(num)] = full_path

        return full_path

    def analyze_folder(self, folder, device, bus, from_date, to_date):
        """Make a list of files and finds the date."""
        sorted_conf = sorted(self.conf.items(), key=operator.itemgetter(0))
        for key in sorted_conf:
            if "folder_" in key[0]:
                print (
                    ".../" + key[0] + " " +
                    key[1].split("/")[-2] + "/" + key[1].split("/")[-1]
                    )

        if device == "":
            picture_path = folder
        else:
            picture_path = "/run/user/1000/gvfs/mtp:host=%5Busb%3A" + bus + "%2C" + device + folder

        files = os.listdir(picture_path)

        if len(files) == 0:
            print "No files in directory.. exiting"
            exit()
        # program_path = os.path.dirname(os.path.realpath(__file__))
        os.chdir(picture_path)

        print "pyexif"
        with pyexiftool.exiftool.ExifTool() as et:
            metadata = et.get_metadata_batch(files)
            print "Done with exif metadata"

            #pickle.dump(metadata, open( program_path + "/" + "metadata.pickle", "wb" ) )
        print "pyexif done"
        
        
        allfiles_exif = []
        for d in metadata:
            print d
            try:
                allfiles_exif.append([
                    picture_path + "/" + d["SourceFile"],
                    d["EXIF:DateTimeOriginal"]
                    ])  # for DCIM pictures
            except KeyError:
                try:
                    allfiles_exif.append([
                        picture_path + "/" + d["SourceFile"],
                        d["QuickTime:MediaCreateDate"]
                        ])  # for MP4 videos
                except KeyError:
                    try:
                        allfiles_exif.append([
                            picture_path + "/" + d["SourceFile"],
                            d["File:FileInodeChangeDate"]
                            ])  # for some of the MP4 videos
                    except KeyError:
                        allfiles_exif.append([
                            picture_path + "/" + d["File:Filename"],
                            d["File:FileModifyDate"]
                            ])  # for almost all types of pictures

        files_exif = []
        for item in allfiles_exif:
            file_date = datetime.datetime.strptime(
                item[1][:19], '%Y:%m:%d %H:%M:%S'
                )
            if file_date >= from_date and file_date <= to_date:
                files_exif.append(item)

        print (
            "Files with date from exifdata: " +
            str(len(metadata)) + "/" + str(len(files))
            )

        print (
            "Files within specified date: " +
            str(len(files_exif))
            )

        return files_exif, metadata

    def sort_by_exif(self, files_exif):
        """Use the exif data to sort the photos/images."""
        for i, image in enumerate(files_exif):
            temp = image[0].split("/")[-1] + "\t" + str(i)
            sys.stdout.write(temp)
            
            
            year = image[1][0:4]
            month = image[1][5:7]
            day = image[1][8:10]
            hour = image[1][11:13]
            minute = image[1][14:16]
            second = image[1][17:19]
            try:
                Inode = True
                diff_plusminus = image[1][19]
                diff_hour = image[1][20:22]
                diff_minute = image[1][23:25]
            except IndexError:
                Inode = False
            base, extension = os.path.splitext(image[0])

            if Inode is True:

                time = year + ":" + month + ":" + day + ":" + hour + ":" + minute + ":" + second
                if diff_plusminus == "-":  # if minus in timezone then add
                    newtime = (
                        datetime.datetime.strptime(time, '%Y:%m:%d:%H:%M:%S') +
                        datetime.timedelta(0, 0, 0, 0, diff_minute, diff_hour, 0)  # class datetime.timedelta([days[, seconds[, microseconds[, milliseconds[, minutes[, hours[, weeks]]]]]]])
                        ).strftime('%Y%m%d_%H%M%S')
                elif diff_plusminus == "+":  # if + in timezone then subtract
                    newtime = (
                        datetime.datetime.strptime(time, '%Y:%m:%d:%H:%M:%S') -
                        datetime.timedelta(0, 0, 0, 0, int(diff_minute), int(diff_hour), 0)  # class datetime.timedelta([days[, seconds[, microseconds[, milliseconds[, minutes[, hours[, weeks]]]]]]])
                        ).strftime('%Y%m%d_%H%M%S')
                #  filename from date and time (20170203_133138.mp4)

                filename = (newtime + extension)

            elif Inode is False:
                #  filename from date and time (20170203_133138.mp4)
                filename = (
                    year + month + day + "_" + hour +
                    minute + second + extension
                    )

            destination = self.dest_folder + '/' + year + '/' + month

            if not os.path.isdir(destination[:-3]):  # Check if folder for year
                os.mkdir(destination[:-3])
            if not os.path.isdir(destination):  # Check if folder for month
                os.mkdir(destination)
            
            temp = image[0].split("/")[-1] + "\t" + str(i)
            for i in range(len(str(temp))):
                sys.stdout.write('\b') #ERASE_LINE = '\x1b[2K'    
            
            # shutil.copy(image[0], destination + '/' + filename)

            # copies and adds "_1" if a file is already
            # there with the same name.
            self.safe_copy(image[0], destination + '/' + filename)

        # if everything went well: self.previous_sort = datetime.datetime.now()

    def safe_copy(self, src, dest):
        """Check if file already exists, then add _#."""
        if not os.path.exists(dest):
            shutil.copy(src, dest)
        else:
            base, ext = os.path.splitext(dest)
            i = 1
            name = os.path.join(dest, '{}_{}{}'.format(base, i, ext))
            while os.path.exists(name):
                i += 1
                name = os.path.join(dest, '{}_{}{}'.format(base, i, ext))

            shutil.copy(src, name)


    def print_conf(self, conf_name):
        print conf_name + ":"
        self.open_conf(conf_name)
        folder_list = sorted(self.conf.items())
        
        folder_text = ""
        for item in folder_list:
            item = "\t%s: %s" % item
            folder_text += ''.join(item) + "\n"
        print folder_text

    def helptext(self):
        print """
usage: 
    photosort configuration function
    or photosort --help
example: 
    photosort 'MyConfiguration' new
    photosort 'MyConfiguration' add_folder int_num '/path/to/folder'
    photosort 'MyConfiguration' analyze_and_sort

functions:
    -h / --help \t Shows this help text.
    new \t\t Create new configuration
    print_conf \t\t Print the configuration file
    add_folder \t\t Add a folder to configuration


        """

def main():
    import sys
    
    r2d = Ren2Date()
    
    if len(sys.argv) == 1:
        print "I need more arguments, try " + sys.argv[0] + " --help"
    
    elif len(sys.argv) == 2:
        if "--help" == sys.argv[1] or "-h" == sys.argv[1]:
            r2d.helptext()
            
    elif len(sys.argv) > 2:
        if 'print_conf' == str(sys.argv[2]):
            r2d.print_conf(sys.argv[1])
        
        elif 'add_folder' == str(sys.argv[2]):
            try:
                r2d.open_conf(sys.argv[1])
                r2d.add_folder(sys.argv[3], sys.argv[4])
                r2d.save_conf(sys.argv[1])
            except:
                print "Creating new configuration file"
                r2d.add_folder(sys.argv[3], sys.argv[4])
                r2d.save_conf(sys.argv[1])
            
            
        elif 'analyze_and_sort' == str(sys.argv[2]): 
            r2d.open_conf(sys.argv[1])
            device = r2d.get_source()
            
            for r2dkey, picture_path in r2d.conf.iteritems():
                if r2dkey.startswith('folder_'):
                    print picture_path
                    files_exif, metadata = r2d.analyze_folder(picture_path, device["device"], device["bus"], datetime.datetime.strptime("20180521_000001", '%Y%m%d_%H%M%S'), datetime.datetime.strptime("20181023_235959", '%Y%m%d_%H%M%S')) # for test only, use previous
                    #ans = raw_input("Continue to sort the files? (y/n): ")
                    #if ans == 'y' or ans == 'yes':
                    r2d.sort_by_exif(files_exif)
                    #else:
                    #    print "You did not answer yes...exiting"
        
    
    
    #r2d = Ren2Date()
    ##r2d.open_conf('PetersTelefon')
    ##r2d.open_conf('KarinsTelefon')
    ##r2d.open_conf('A5000_2')
    #device = r2d.get_source()

    #r2d.add_folder(1, "%5D/SD card/DCIM/100ANDRO", device["device"], device["bus"])
    #r2d.add_folder(2, "%5D/Internal shared storage/DCIM/100ANDRO", device["device"], device["bus"])
    #r2d.add_folder(3, "%5D/Internal shared storage/Pictures/Messenger", device["device"], device["bus"])
    #r2d.add_folder(4, "%5D/SD card/Pictures/Messenger", device["device"], device["bus"])
    #r2d.add_folder(5, "%5D/Internal shared storage/Pictures/Screenshots", device["device"], device["bus"])
    #r2d.add_folder(6, "%5D/SD card/Pictures/Screenshots", device["device"], device["bus"])
    #r2d.add_folder(7, "%5D/Internal shared storage/Snapchat", device["device"], device["bus"])
    #r2d.save_conf('PetersTelefon')
    

    #'''
    #r2d.add_folder(1, "%5D/SD-kort/DCIM/100ANDRO", device["device"], device["bus"])
    #r2d.add_folder(2, "%5D/Delat internt lagringsutrymme/Pictures/Messenger", device["device"], device["bus"])
    #r2d.add_folder(3, "%5D/SD-kort/Pictures/Messenger", device["device"], device["bus"])
    #r2d.add_folder(4, "%5D/Delat internt lagringsutrymme/Pictures/Screenshots", device["device"], device["bus"])
    #r2d.add_folder(5, "%5D/SD-kort/Pictures/Screenshots", device["device"], device["bus"])
    #r2d.add_folder(6, "%5D/Delat internt lagringsutrymme/Snapchat", device["device"], device["bus"])
    #r2d.add_folder(7, "%5D/Delat internt lagringsutrymme/viber/media/Viber Images", device["device"], device["bus"])
    #r2d.add_folder(8, "%5D/Delat internt lagringsutrymme/viber/media/Viber Videos", device["device"], device["bus"])
    #r2d.save_conf('KarinsTelefon')
    #'''

    #'''
    ##r2d.add_folder(1, "/home/psteffensen/Pictures/Billeder Backup/A5100")
    #r2d.add_folder(1, "/home/psteffensen/Pictures/Billeder Backup/Sommer billeder a5000")
    #r2d.save_conf('A5000_2')
    #'''
    
    ##files_exif, metadata = r2d.analyze_folder(datetime.strptime("20171111_125626", '%Y%m%d_%H%M%S') ,  datetime.strptime("20180313_000000", '%Y%m%d_%H%M%S'))
    ##files_exif, metadata = r2d.analyze_folder(datetime.datetime.strptime("20180313_000001", '%Y%m%d_%H%M%S'), datetime.datetime.strptime("20180521_000000", '%Y%m%d_%H%M%S'))
    
    #for r2dkey, picture_path in r2d.conf.iteritems():
        #if r2dkey.startswith('folder_'):
            #print picture_path
            #files_exif, metadata = r2d.analyze_folder(picture_path, device["device"], device["bus"], datetime.datetime.strptime("20180521_000001", '%Y%m%d_%H%M%S'), datetime.datetime.strptime("20181023_235959", '%Y%m%d_%H%M%S')) # for test only, use previous
            #r2d.sort_by_exif(files_exif)

    
    
if __name__ == "__main__":
    main()
