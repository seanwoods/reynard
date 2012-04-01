from setuptools import setup, find_packages

def semantic_greater_than(v1, v2):
    """Compare semantic version sequences."""
    
    if v1 == v2:
        return 0

    v1 = [int(i) for i in v1.split('.')]
    v2 = [int(i) for i in v2.split('.')]

    for idx, num in enumerate(v1):
        if num > v2[idx]:
            return 1

    return -1

install_requires = [
    'CherryPy>=3.2.0',
    'Mako>=0.6.2'
]

# Detect a proper version of PyZMQ
# TODO: Find a way to do this through setuptools...

HAS_ZMQ = False

try:
    import zmq
    
    if semantic_greater_than(zmq.__version__, '2.1.11') >= 0:
        HAS_ZMQ = True

except ImportError:
    pass

if not HAS_ZMQ:
    install_requires.append('PyZMQ>=2.1.11')

setup(
    name = 'Reynard',
    version = '0.2-alpha',
    description = 'Object persistence library and frontend.',
    author = 'Sean Woods',
    author_email = 'sean@seanwoods.com',
    packages = find_packages(),

    package_data = {
        'reynard.apps' : [
            'static/*',
            'templates/*'
        ]
    },
    
    install_requires = install_requires,
    
    zip_safe = False

)
