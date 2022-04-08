from django.apps import AppConfig

class UsersConfig(AppConfig):
    name = 'src.models'

    # actstream register model
    # def ready(self):
    #     from actstream import registry
    #     registry.register(self.get_model('User'))
