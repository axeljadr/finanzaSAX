from django import forms
from datetime import date

from .models import Concepto, Movimiento, Tarjeta, TipoMovimiento, PresupuestoMensual


class BaseOwnedModelForm(forms.ModelForm):
    """Form base para estandarizar apariencia."""

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        for _, field in self.fields.items():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs["class"] = f"{field.widget.attrs.get('class', '')} {css_class}".strip()


class TarjetaForm(BaseOwnedModelForm):
    class Meta:
        model = Tarjeta
        fields = ["ultimos_4_digitos", "tipo_tarjeta", "banco", "monto"]


class ConceptoForm(BaseOwnedModelForm):
    class Meta:
        model = Concepto
        fields = ["nombre_concepto", "tipo_default"]


class TipoMovimientoForm(BaseOwnedModelForm):
    class Meta:
        model = TipoMovimiento
        fields = ["nombre"]


class MovimientoForm(BaseOwnedModelForm):
    fecha = forms.DateField(
        widget=forms.DateInput(
            attrs={"type": "date"},
            format="%Y-%m-%d",
        ),
        input_formats=["%Y-%m-%d"],
    )

    class Meta:
        model = Movimiento
        fields = ["fecha", "monto", "descripcion", "concepto", "tipo", "tarjeta", "tarjeta_destino", "medio"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, user=user, **kwargs)
        if self.user:
            self.fields["concepto"].queryset = Concepto.objects.all().order_by("nombre_concepto")
            self.fields["tipo"].queryset = TipoMovimiento.objects.all().order_by("nombre")
            self.fields["tarjeta"].queryset = Tarjeta.objects.filter(usuario=self.user).order_by("banco")
            self.fields["tarjeta_destino"].queryset = Tarjeta.objects.filter(usuario=self.user).order_by("banco")
        # Fecha de hoy solo en registros nuevos
        if not self.is_bound and not getattr(self.instance, "pk", None):
            self.initial["fecha"] = date.today().strftime("%Y-%m-%d")


class PresupuestoMensualForm(BaseOwnedModelForm):
    mes = forms.DateField(
        widget=forms.DateInput(attrs={"type": "month"}),
        help_text="Selecciona el mes",
        input_formats=["%Y-%m"],
    )

    class Meta:
        model = PresupuestoMensual
        fields = ["concepto", "monto_asignado", "mes"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, user=user, **kwargs)
        self.fields["concepto"].queryset = Concepto.objects.all().order_by("nombre_concepto")

    def clean_mes(self):
        mes = self.cleaned_data["mes"]
        return date(mes.year, mes.month, 1)