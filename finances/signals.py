from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Concepto, TipoMovimiento


@receiver(post_save, sender=get_user_model())
def create_default_finance_catalogs(sender, instance, created, **kwargs):
    if not created:
        return

    # Tipos globales — solo se crean si no existen aún
    for nombre in ["Ingreso", "Gasto", "Ahorro"]:
        TipoMovimiento.objects.get_or_create(nombre=nombre)

    # Conceptos globales — solo se crean si no existen aún
    for nombre in ["General", "Comida", "Transporte", "Renta", "Salud"]:
        Concepto.objects.get_or_create(nombre_concepto=nombre)


def crear_datos_iniciales(sender, instance, created, **kwargs):
    if created:
        tipo_gasto, _    = TipoMovimiento.objects.get_or_create(nombre="Gasto")
        tipo_ingreso, _  = TipoMovimiento.objects.get_or_create(nombre="Ingreso")
        tipo_transf, _   = TipoMovimiento.objects.get_or_create(nombre="Transferencia")

        defaults_conceptos = [
            ("Comida",      tipo_gasto),
            ("Transporte",  tipo_gasto),
            ("Servicios",   tipo_gasto),
            ("Entretenimiento", tipo_gasto),
            ("Sueldo",      tipo_ingreso),
            ("Freelance",   tipo_ingreso),
            ("Ahorro",      tipo_transf),
        ]
        for nombre, tipo in defaults_conceptos:
            Concepto.objects.get_or_create(
                nombre_concepto=nombre,
                defaults={"tipo_default": tipo}
            )