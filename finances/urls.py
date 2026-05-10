from django.urls import path

from .views import (
    AppLoginView,
    ConceptoCreateView,
    ConceptoDeleteView,
    ConceptoListView,
    ConceptoUpdateView,
    DashboardView,
    MovimientoCreateView,
    MovimientoDeleteView,
    MovimientoListView,
    MovimientoUpdateView,
    TarjetaCreateView,
    TarjetaDeleteView,
    TarjetaListView,
    TarjetaUpdateView,
    TipoMovimientoCreateView,
    TipoMovimientoDeleteView,
    TipoMovimientoListView,
    TipoMovimientoUpdateView,
    PresupuestoCreateView,
    PresupuestoDeleteView,
    PresupuestoListView,
    PresupuestoUpdateView,
)

urlpatterns = [
    path("", MovimientoListView.as_view(), name="movimientos"),

    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    # Movimientos
    path("movimientos/", MovimientoListView.as_view(), name="movimientos"),
    path("movimientos/nuevo/", MovimientoCreateView.as_view(), name="movimiento_create"),
    path("movimientos/<int:pk>/editar/", MovimientoUpdateView.as_view(), name="movimiento_update"),
    path("movimientos/<int:pk>/eliminar/", MovimientoDeleteView.as_view(), name="movimiento_delete"),
    # Tarjetas (propias)
    path("tarjetas/", TarjetaListView.as_view(), name="tarjetas"),
    path("tarjetas/nueva/", TarjetaCreateView.as_view(), name="tarjeta_create"),
    path("tarjetas/<int:pk>/editar/", TarjetaUpdateView.as_view(), name="tarjeta_update"),
    path("tarjetas/<int:pk>/eliminar/", TarjetaDeleteView.as_view(), name="tarjeta_delete"),
    # Conceptos (globales)
    path("conceptos/", ConceptoListView.as_view(), name="conceptos"),
    path("conceptos/nuevo/", ConceptoCreateView.as_view(), name="concepto_create"),
    path("conceptos/<int:pk>/editar/", ConceptoUpdateView.as_view(), name="concepto_update"),
    path("conceptos/<int:pk>/eliminar/", ConceptoDeleteView.as_view(), name="concepto_delete"),
    # Tipos de movimiento (globales)
    path("tipos/", TipoMovimientoListView.as_view(), name="tipos"),
    path("tipos/nuevo/", TipoMovimientoCreateView.as_view(), name="tipo_create"),
    path("tipos/<int:pk>/editar/", TipoMovimientoUpdateView.as_view(), name="tipo_update"),
    path("tipos/<int:pk>/eliminar/", TipoMovimientoDeleteView.as_view(), name="tipo_delete"),
    
    path("presupuestos/", PresupuestoListView.as_view(), name="presupuestos"),
    path("presupuestos/nuevo/", PresupuestoCreateView.as_view(), name="presupuesto_create"),
    path("presupuestos/<int:pk>/editar/", PresupuestoUpdateView.as_view(), name="presupuesto_update"),
    path("presupuestos/<int:pk>/eliminar/", PresupuestoDeleteView.as_view(), name="presupuesto_delete"),
    
    path("login/", AppLoginView.as_view(), name="logout"),
]