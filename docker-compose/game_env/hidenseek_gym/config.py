import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

stream = open('/opt/app/game_env/default_config.yml', 'r')
config = yaml.load(stream, Loader=Loader)
