from ast import literal_eval
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


def get_dependencies(module, addons_path=None, deps=None):
    if deps is None:
        deps = []
    if addons_path is None:
        from destral.openerp import OpenERPService
        service = OpenERPService()
        addons_path = service.config['addons_path']
    pj = os.path.join
    module_path = pj(addons_path, module)
    if not os.path.exists(module_path):
        raise Exception('Module {} not found in {}'.format(
            module, addons_path
        ))
    terp_path = pj(module_path, '__terp__.py')
    if not os.path.exists(terp_path):
        raise Exception(
            'Module {} is not a valid module. Missing __terp__.py file'.format(
                module
            )
        )
    with open(terp_path, 'r') as terp_file:
        terp = literal_eval(terp_file.read())

    for dep in terp['depends']:
        deps.append(dep)
        deps += get_dependencies(dep, addons_path, deps)

    return list(set(deps))
