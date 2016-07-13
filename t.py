import sys
import cv2
import pyflycap2.interface as flycap

if __name__ == '__main__':
    fname1 = "Capture.png"
    fname2 = "Capture2.png"
    flycap.init_conf('/home/lee/PycharmProjects/Test_pro/interface.conf')
    cam = flycap.Camera(serial=[15631910], ctx_type='IIDC')  # other = GigE
    # print cam.get_num_cameras()
    cam.connect()

    cam.start_capture()
    cam.read_next_image()
    cam.grab_image_to_disk(fname2)
    # -----------get numpy image -------
    # print 'start get numpy image'
    # image2 = cam.get_current_image()
    # print image2['pix_fmt']
    img = cam.grab_numpy_image('bgr')
    cv2.imshow('1', img)
    cv2.waitKey()
    # ----------------------------------
    # cam.grab_image_to_disk(fname2, ext='png')
    cam.stop_capture()