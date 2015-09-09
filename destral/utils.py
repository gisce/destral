import imp
import os


def update_config(config, **kwargs):
    for key, value in kwargs.iteritems():
        config[key] = value
    return config


def detect_module(path):
    stack = path.split(os.path.sep)
    if not stack[0]:
        stack[0] = os.path.sep
    stack = [x for x in stack if x]
    while stack:
        path = os.path.join(*stack)
        module = stack.pop()
        if not os.path.isdir(path):
            continue
        files = os.listdir(path)
        if '__terp__.py' in files:
            return module
    return None


def module_exists(module):
    modlist = module.split('.')
    pathlist = None
    for mod in modlist:
        try:
            openfile, pathname, desc = imp.find_module(mod, pathlist)
            pathlist = [pathname]
        except ImportError:
            return False
        else:
            if openfile:
                openfile.close()
                return True
