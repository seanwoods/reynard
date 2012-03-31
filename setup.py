from setuptools import setup, find_packages

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
    
    install_requires = [
        'CherryPy>=3.2.0',
    ],
    
    zip_safe = False

)
