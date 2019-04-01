
import threading

def launch_thr(target, args=None):
    """ Launch thread """
    if args is not None:
        t = threading.Thread(target=target, args=args)
    else:
        t = threading.Thread(target=target)
    t.start()