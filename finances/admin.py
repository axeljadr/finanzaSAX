from django.contrib import admin

from .models import Concepto, Movimiento, Tarjeta, TipoMovimiento


@admin.register(Tarjeta)
class TarjetaAdmin(admin.ModelAdmin):
    list_display = ("banco", "ultimos_4_digitos", "tipo_tarjeta", "monto", "usuario")
    search_fields = ("banco", "usuario__username")
    list_filter = ("tipo_tarjeta", "usuario")


@admin.register(TipoMovimiento)
class TipoMovimientoAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


@admin.register(Concepto)
class ConceptoAdmin(admin.ModelAdmin):
    list_display = ("nombre_concepto",)
    search_fields = ("nombre_concepto",)


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ("fecha", "descripcion", "monto", "concepto", "tipo", "tarjeta", "medio", "usuario")
    search_fields = ("descripcion", "usuario__username")
    list_filter = ("fecha", "tipo", "concepto", "usuario")