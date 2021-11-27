from django.apps import AppConfig


class MediclesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'medicles'

    # Activity stream implementation
    def ready(self):
        from actstream import registry
        registry.register(self.get_model('Article'))
    
    # def ready(self):
    #     from medicles import services
    #     srv = services
    #     srv.create_db('covid', 100, 400)

'''
    def ready(self):
        from medicles import updater
        updater.start()
'''

