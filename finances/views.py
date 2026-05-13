import json
from decimal import Decimal
from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Case, DecimalField, F, Sum, Value, When
from django.db.models.functions import Coalesce, TruncMonth
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from .filters import MovimientoFilter
from .forms import ConceptoForm, MovimientoForm, PresupuestoMensualForm, TarjetaForm, TipoMovimientoForm
from .models import Concepto, Movimiento, PresupuestoMensual, Tarjeta, TipoMovimiento


# ── Auth ──────────────────────────────────────────────────────────────────────

class AppLoginView(LoginView):
    template_name = "registration/login.html"


# ── Movimientos ───────────────────────────────────────────────────────────────

class MovimientoListView(LoginRequiredMixin, ListView):
    template_name = "finances/movimiento_list.html"
    model = Movimiento
    context_object_name = "movimientos"
    paginate_by = 20

    def get_queryset(self):
        queryset = Movimiento.objects.select_related(
            "concepto", "tipo", "tarjeta", "tarjeta_destino", "usuario"
        )
        self.filterset = MovimientoFilter(self.request.GET, queryset=queryset, user=self.request.user)
        return self.filterset.qs.order_by("-fecha", "-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filterset"] = self.filterset

        # 1. Obtener presupuestos del mes actual
        from datetime import date
        hoy = date.today()
        presupuestos = PresupuestoMensual.objects.filter(
            usuario=self.request.user,
            mes__year=hoy.year,
            mes__month=hoy.month,
        ).select_related("concepto")
        
        # Crear el mapa para búsqueda rápida
        presupuesto_map = {p.concepto_id: p for p in presupuestos}

        # 2. ASIGNAR PRESUPUESTO A CADA MOVIMIENTO (Solo los de la página actual)
        # Usamos context["movimientos"] que es lo que ListView ya paginó
        for mov in context["movimientos"]:
            mov.presupuesto_del_mes = presupuesto_map.get(mov.concepto_id)

        # 3. Gestión de filtros para la UI
        GET = self.request.GET
        filtros = {
            "usuario":     GET.get("usuario", ""),
            "tipo":        GET.get("tipo", ""),
            "concepto":    GET.get("concepto", ""),
            "tarjeta":     GET.get("tarjeta", ""),
            "fecha_desde": GET.get("fecha_desde", ""),
            "fecha_hasta": GET.get("fecha_hasta", ""),
            "descripcion": GET.get("descripcion", ""),
            "monto_min":   GET.get("monto_min", ""),
            "monto_max":   GET.get("monto_max", ""),
        }
        context["filtros"] = filtros
        context["hay_filtros"] = any(filtros.values())
        
        return context


class MovimientoCreateView(LoginRequiredMixin, CreateView):
    template_name = "finances/movimiento_form.html"
    model = Movimiento
    form_class = MovimientoForm
    success_url = reverse_lazy("movimientos")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    # En MovimientoCreateView
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = date.today()
        context["verbose_name"] = self.model._meta.verbose_name
        context["concepto_tipo_map"] = list(
            Concepto.objects.filter(tipo_default__isnull=False).values("id", "tipo_default_id"))
        context["saldos_tarjetas"] = list(
        Tarjeta.objects.filter(usuario=self.request.user).values("id", "monto", "banco")
    )
        context["presupuestos_usuario"] = [
            {
            "concepto_id": p.concepto_id,
            "monto_asignado": p.monto_asignado,
            "monto_usado": p.monto_usado(),
            "monto_restante": p.monto_restante(),
            }
            for p in PresupuestoMensual.objects.filter(
                usuario=self.request.user,
                mes__year=hoy.year,
                mes__month=hoy.month,
                ).select_related("concepto")
                ]
        return context

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        response = super().form_valid(form)
        # Aplicar efecto en saldo de tarjeta(s)
        self.object.aplicar_saldo()
        messages.success(self.request, "Movimiento creado correctamente.")
        return response


class MovimientoUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "finances/form.html"
    model = Movimiento
    form_class = MovimientoForm
    success_url = reverse_lazy("movimientos")

    def get_queryset(self):
        return Movimiento.objects.filter(usuario=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    # En MovimientoUpdateView — exactamente el mismo get_context_data
    def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       hoy = date.today()
       context["verbose_name"] = self.model._meta.verbose_name
       context["concepto_tipo_map"] = list(
           Concepto.objects.filter(tipo_default__isnull=False).values("id", "tipo_default_id")
       )
       context["saldos_tarjetas"] = list(
           Tarjeta.objects.filter(usuario=self.request.user).values("id", "monto", "banco")
       )
       context["presupuestos_usuario"] = [
           {
               "concepto_id": p.concepto_id,
               "monto_asignado": p.monto_asignado,
               "monto_usado": p.monto_usado(),
               "monto_restante": p.monto_restante(),
           }
           for p in PresupuestoMensual.objects.filter(
               usuario=self.request.user,
               mes__year=hoy.year,
               mes__month=hoy.month,
           ).select_related("concepto")
       ]
       return context

    def form_valid(self, form):
        # Revertir saldo anterior antes de guardar
        old = Movimiento.objects.select_related("tarjeta", "tarjeta_destino", "tipo").get(pk=self.object.pk)
        old.revertir_saldo()
        response = super().form_valid(form)
        # Aplicar nuevo saldo
        self.object.refresh_from_db()
        self.object.aplicar_saldo()
        messages.success(self.request, "Movimiento actualizado correctamente.")
        return response


class MovimientoDeleteView(LoginRequiredMixin, DeleteView):
    model = Movimiento
    template_name = "finances/confirm_delete.html"
    success_url = reverse_lazy("movimientos")

    def get_queryset(self):
        return Movimiento.objects.filter(usuario=self.request.user)

    def form_valid(self, form):
        # Revertir saldo antes de eliminar
        obj = self.get_object()
        obj.revertir_saldo()
        messages.success(self.request, "Movimiento eliminado correctamente.")
        return super().form_valid(form)


# ── Vistas base PROPIAS ───────────────────────────────────────────────────────

class OwnedListView(LoginRequiredMixin, ListView):
    template_name = "finances/ownership_list.html"
    paginate_by = 20

    TITLES = {
        "tarjeta": "Tarjetas",
        "presupuestomensual": "Presupuesto Mensual",
    }

    def get_queryset(self):
        return self.model.objects.filter(usuario=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        model_name = self.model._meta.model_name
        url_prefix = "presupuesto" if model_name == "presupuestomensual" else model_name
        context.update({
            "title": self.TITLES.get(model_name, model_name.title()),
            "create_url_name": f"{url_prefix}_create",
            "update_url_name": f"{url_prefix}_update",
            "delete_url_name": f"{url_prefix}_delete",
        })
        return context


class OwnedCreateView(LoginRequiredMixin, CreateView):
    template_name = "finances/form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["verbose_name"] = self.model._meta.verbose_name
        return context

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        messages.success(self.request, f"{self.model._meta.verbose_name.title()} creado correctamente.")
        return super().form_valid(form)


class OwnedUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "finances/form.html"

    def get_queryset(self):
        return self.model.objects.filter(usuario=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["verbose_name"] = self.model._meta.verbose_name
        return context

    def form_valid(self, form):
        messages.success(self.request, f"{self.model._meta.verbose_name.title()} actualizado correctamente.")
        return super().form_valid(form)


class OwnedDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "finances/confirm_delete.html"

    def get_queryset(self):
        return self.model.objects.filter(usuario=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, f"{self.model._meta.verbose_name.title()} eliminado correctamente.")
        return super().form_valid(form)


# ── Vistas base GLOBALES ──────────────────────────────────────────────────────

class GlobalListView(LoginRequiredMixin, ListView):
    template_name = "finances/ownership_list.html"
    paginate_by = 20

    TITLES = {
        "concepto": "Conceptos",
        "tipomovimiento": "Tipos de movimiento",
    }

    def get_queryset(self):
        order = "nombre_concepto" if self.model._meta.model_name == "concepto" else "nombre"
        return self.model.objects.all().order_by(order)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        model_name = self.model._meta.model_name
        url_prefix = "tipo" if model_name == "tipomovimiento" else model_name
        context.update({
            "title": self.TITLES.get(model_name, model_name.title()),
            "create_url_name": f"{url_prefix}_create",
            "update_url_name": f"{url_prefix}_update",
            "delete_url_name": f"{url_prefix}_delete",
        })
        return context


class GlobalCreateView(LoginRequiredMixin, CreateView):
    template_name = "finances/form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["verbose_name"] = self.model._meta.verbose_name
        return context

    def form_valid(self, form):
        messages.success(self.request, f"{self.model._meta.verbose_name.title()} creado correctamente.")
        return super().form_valid(form)


class GlobalUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "finances/form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["verbose_name"] = self.model._meta.verbose_name
        return context

    def form_valid(self, form):
        messages.success(self.request, f"{self.model._meta.verbose_name.title()} actualizado correctamente.")
        return super().form_valid(form)


class GlobalDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "finances/confirm_delete.html"

    def form_valid(self, form):
        messages.success(self.request, f"{self.model._meta.verbose_name.title()} eliminado correctamente.")
        return super().form_valid(form)


# ── Tarjeta ───────────────────────────────────────────────────────────────────

class TarjetaListView(OwnedListView):
    model = Tarjeta

class TarjetaCreateView(OwnedCreateView):
    model = Tarjeta
    form_class = TarjetaForm
    success_url = reverse_lazy("tarjetas")

class TarjetaUpdateView(OwnedUpdateView):
    model = Tarjeta
    form_class = TarjetaForm
    success_url = reverse_lazy("tarjetas")

class TarjetaDeleteView(OwnedDeleteView):
    model = Tarjeta
    success_url = reverse_lazy("tarjetas")


# ── Concepto ──────────────────────────────────────────────────────────────────

class ConceptoListView(GlobalListView):
    model = Concepto

class ConceptoCreateView(GlobalCreateView):
    model = Concepto
    form_class = ConceptoForm
    success_url = reverse_lazy("conceptos")

class ConceptoUpdateView(GlobalUpdateView):
    model = Concepto
    form_class = ConceptoForm
    success_url = reverse_lazy("conceptos")

class ConceptoDeleteView(GlobalDeleteView):
    model = Concepto
    success_url = reverse_lazy("conceptos")


# ── TipoMovimiento ────────────────────────────────────────────────────────────

class TipoMovimientoListView(GlobalListView):
    model = TipoMovimiento

class TipoMovimientoCreateView(GlobalCreateView):
    model = TipoMovimiento
    form_class = TipoMovimientoForm
    success_url = reverse_lazy("tipos")

class TipoMovimientoUpdateView(GlobalUpdateView):
    model = TipoMovimiento
    form_class = TipoMovimientoForm
    success_url = reverse_lazy("tipos")

class TipoMovimientoDeleteView(GlobalDeleteView):
    model = TipoMovimiento
    success_url = reverse_lazy("tipos")


# ── PresupuestoMensual ────────────────────────────────────────────────────────

class PresupuestoListView(OwnedListView):
    model = PresupuestoMensual
    template_name = "finances/presupuesto_list.html"
    context_object_name = "presupuestos"

    def get_queryset(self):
        return PresupuestoMensual.objects.select_related("concepto", "usuario").filter(
            usuario=self.request.user
        ).order_by("-mes")

class PresupuestoCreateView(OwnedCreateView):
    model = PresupuestoMensual
    form_class = PresupuestoMensualForm
    success_url = reverse_lazy("presupuestos")

class PresupuestoUpdateView(OwnedUpdateView):
    model = PresupuestoMensual
    form_class = PresupuestoMensualForm
    success_url = reverse_lazy("presupuestos")

class PresupuestoDeleteView(OwnedDeleteView):
    model = PresupuestoMensual
    success_url = reverse_lazy("presupuestos")


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "finances/dashboard.html"

    def _base_queryset(self):
        queryset = Movimiento.objects.select_related("usuario", "tipo", "concepto")
        fecha_desde = self.request.GET.get("fecha_desde")
        fecha_hasta = self.request.GET.get("fecha_hasta")
        usuario_id  = self.request.GET.get("usuario")
        concepto_id = self.request.GET.get("concepto")
        tipo_id     = self.request.GET.get("tipo")
        q           = self.request.GET.get("q", "").strip()
        monto_min   = self.request.GET.get("monto_min")
        monto_max   = self.request.GET.get("monto_max")

        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)
        if concepto_id:
            queryset = queryset.filter(concepto_id=concepto_id)
        if tipo_id:
            queryset = queryset.filter(tipo_id=tipo_id)
        if q:
            queryset = queryset.filter(descripcion__icontains=q)
        if monto_min:
            queryset = queryset.filter(monto__gte=monto_min)
        if monto_max:
            queryset = queryset.filter(monto__lte=monto_max)
        return queryset

    @staticmethod
    def _sumar_por_tipo(queryset, texto_tipo):
        return queryset.filter(tipo__nombre__icontains=texto_tipo).aggregate(
            total=Coalesce(Sum("monto"), Decimal("0.00"))
        )["total"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self._base_queryset()

        # Resúmenes generales
        
        insert = self._sumar_por_tipo(queryset, "ingreso")
        ahorros  = self._sumar_por_tipo(queryset, "ahorro")
        ingresos = insert + ahorros    
        gastos   = self._sumar_por_tipo(queryset, "gasto")
        balance  = ingresos - gastos

        ahorros_qs = (
            Tarjeta.objects
            .filter(tipo_tarjeta__in=["debito", "efectivo"])
            .values("usuario_id", "usuario__username")
            .annotate(total=Coalesce(Sum("monto"), Decimal("0.00")))
        )
        ahorros_total = sum(r["total"] for r in ahorros_qs)
        ahorros_por_usuario = {r["usuario_id"]: r["total"] for r in ahorros_qs}

        # 2. Obtener el detalle de CADA tarjeta por usuario
        # En get_context_data, donde creas tarjetas_detalle
        tarjetas_detalle = {}
        for tarjeta in Tarjeta.objects.filter(tipo_tarjeta__in=["debito", "efectivo"]).select_related('usuario'):
            uid = tarjeta.usuario_id
            # Construye un nombre legible para la tarjeta
            if tarjeta.tipo_tarjeta == "efectivo":
                nombre_mostrar = "Efectivo"
            else:
                # Para débito, muestra banco y últimos 4 dígitos si existen
                if tarjeta.ultimos_4_digitos:
                    nombre_mostrar = f"{tarjeta.banco} (****{tarjeta.ultimos_4_digitos})"
                else:
                    nombre_mostrar = tarjeta.banco
            tarjetas_detalle.setdefault(uid, []).append({
                'nombre': nombre_mostrar,
                'tipo': tarjeta.get_tipo_tarjeta_display(),   # "Débito" o "Efectivo"
                'monto': tarjeta.monto
            })

        # 3. Construir resumen por usuario (ya tenías la lógica de movimientos)
        usuarios_resumen = {}
        for mov in queryset:
            row = usuarios_resumen.setdefault(
                mov.usuario_id,
                {
                    "username": mov.usuario.username,
                    "user_id": mov.usuario_id,   # añadimos id para referenciar
                    "ingresos": Decimal("0.00"),
                    "gastos": Decimal("0.00"),
                    "transferencias": Decimal("0.00"),
                    "ahorros": Decimal("0.00"),
                },
            )
            tipo_nombre = mov.tipo.nombre.lower()
            if "ingreso" in tipo_nombre:
                row["ingresos"] += mov.monto
            elif "gasto" in tipo_nombre:
                row["gastos"] += mov.monto
            elif "transferencia" in tipo_nombre:
                row["transferencias"] += mov.monto

        resumen_usuarios = []
        for uid, row in usuarios_resumen.items():
            row["balance"] = row["ingresos"] - row["gastos"]
            row["ahorros"] = ahorros_por_usuario.get(uid, Decimal("0.00"))
            row["tarjetas"] = tarjetas_detalle.get(uid, [])   # lista de tarjetas
            resumen_usuarios.append(row)
        resumen_usuarios.sort(key=lambda x: x["username"])
        # Datos para Gráfica Mensual (Líneas)
        mensual = (
            queryset.annotate(mes=TruncMonth("fecha"))
            .values("mes")
            .annotate(
                ingresos=Coalesce(Sum(Case(When(tipo__nombre__icontains="ingreso", then=F("monto")), default=Value(0), output_field=DecimalField())), Decimal("0")),
                gastos=Coalesce(Sum(Case(When(tipo__nombre__icontains="gasto", then=F("monto")), default=Value(0), output_field=DecimalField())), Decimal("0")),
            )
            .order_by("mes")
        )

        # Filtros
        GET = self.request.GET
        filtros = {k: GET.get(k, "") for k in ["fecha_desde", "fecha_hasta", "usuario", "concepto", "tipo", "q", "monto_min", "monto_max"]}

        context.update({
            "movimientos_lista": queryset.order_by("-fecha", "-id")[:15], # Lista de los últimos 15 filtrados
            "ingresos": ingresos,
            "gastos": gastos,
            "ahorros": ahorros_total,
            "balance": balance,
            "resumen_usuarios": resumen_usuarios,
            "usuarios": Movimiento.objects.values("usuario_id", "usuario__username").distinct(),
            "conceptos": Concepto.objects.all().order_by("nombre_concepto"),
            "tipos": TipoMovimiento.objects.all().order_by("nombre"),
            "filtros": filtros,
            "hay_filtros": any(filtros.values()),
            "chart_labels": json.dumps([r["mes"].strftime("%b %Y") for r in mensual if r["mes"]]),
            "chart_ingresos": json.dumps([float(r["ingresos"]) for r in mensual]),
            "chart_gastos": json.dumps([float(r["gastos"]) for r in mensual]),
            "pie_labels": json.dumps([r["username"] for r in resumen_usuarios]),
            "pie_data": json.dumps([float(r["ahorros"]) for r in resumen_usuarios]),
        })
        return context