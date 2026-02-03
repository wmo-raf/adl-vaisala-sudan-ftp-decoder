from adl_ftp_plugin.registries import ftp_decoder_registry
from django.apps import AppConfig


class VaisalaSudanPluginConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = "adl_vaisala_sudan_ftp_decoder"
    
    def ready(self):
        from .decoders import VaisalaSudanDecoder
        
        ftp_decoder_registry.register(VaisalaSudanDecoder())
