import sys
import pyflycap2.interface as flycap

if __name__ == '__main__':
    fname1 = "Capture.png"
    fname2 = "Capture2.png"
    ctx = flycap.CameraContext()
    print ctx.get_gige_cams()
    # print ctx.cycle_time()
    cam = flycap.Camera(ip=[192,168,100,3])
    cam.connect()
    cam.set_property_value('frame_rate', 26.0)
    print cam.get_property('frame_rate'), 'frame_rate'
    print cam.get_gige_mode()
    cam.set_gige_mode(1)
    for k, v in cam.get_gige_config().iteritems():
        print k, v

    cam.start_capture()
    # -----------set property-----------
    # cam.set_property_value('gain', 15.0)
    # print cam.get_property('gain'), 'gain'
    # cam.set_property_value('white_balance', (550, 800))

    # ---------- get time --------------
    # cam.read_next_image()
    # print cam.get_current_image_config()
    # -----------save image-------------
    # print 'start save'
    # cam.save_current_image(fname1)
    # print 'done'
    #
    #-------------get image-------------------
    cam.grab_image_to_disk(fname2)
    # -----------get numpy image -------
    print 'start get numpy image'
    # image2 = cam.get_current_image()
    # print image2['pix_fmt']
    img = cam.grab_numpy_image('bgr')
    # ----------------------------------
    # cam.grab_image_to_disk(fname2, ext='png')
    cam.stop_capture()