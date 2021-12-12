from django.apps import AppConfig, apps



class MediclesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'medicles'

    # def ready(self):
    #     from medicles import services
    #     srv = services
    #     srv.create_db('covid', 100, 400)

'''
    def ready(self):
        from medicles import updater
        updater.start()
'''

