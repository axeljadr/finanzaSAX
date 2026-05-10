import django_filters
from django import forms
from django.contrib.auth import get_user_model

from .models import Concepto, Movimiento, Tarjeta, TipoMovimiento


class MovimientoFilter(django_filters.FilterSet):
    fecha_desde = django_filters.DateFilter(
        field_name="fecha",
        lookup_expr="gte",
        label="Fecha desde",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    fecha_hasta = django_filters.DateFilter(
        field_name="fecha",
        lookup_expr="lte",
        label="Fecha hasta",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    monto_min = django_filters.NumberFilter(field_name="monto", lookup_expr="gte", label="Monto mínimo")
    monto_max = django_filters.NumberFilter(field_name="monto", lookup_expr="lte", label="Monto máximo")
    descripcion = django_filters.CharFilter(field_name="descripcion", lookup_expr="icontains", label="Descripción")

    class Meta:
        model = Movimiento
        fields = ["concepto", "tipo", "tarjeta", "usuario"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()

        # Usuario: todos (para ver movimientos de ambos en el dashboard)
        self.filters["usuario"].queryset = User.objects.all().order_by("username")

        # Globales: sin filtro por usuario
        self.filters["concepto"].queryset = Concepto.objects.all().order_by("nombre_concepto")
        self.filters["tipo"].queryset = TipoMovimiento.objects.all().order_by("nombre")

        # Tarjetas: solo las del usuario logueado
        if user is not None:
            self.filters["tarjeta"].queryset = Tarjeta.objects.filter(usuario=user).order_by("banco")
        else:
            self.filters["tarjeta"].queryset = Tarjeta.objects.none()

        for _, field in self.form.fields.items():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = f"{field.widget.attrs.get('class', '')} {css_class}".strip()