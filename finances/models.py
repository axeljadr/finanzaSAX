from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class TipoMovimiento(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "tipo de movimiento"
        verbose_name_plural = "tipos de movimiento"

    def __str__(self):
        return self.nombre


class Concepto(models.Model):
    nombre_concepto = models.CharField(max_length=100, unique=True)
    tipo_default = models.ForeignKey(
        "TipoMovimiento",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conceptos",
        verbose_name="tipo por defecto",
    )
    class Meta:
        verbose_name = "concepto"
        verbose_name_plural = "conceptos"

    def __str__(self):
        return self.nombre_concepto


class Tarjeta(models.Model):
    TIPO_CHOICES = [
        ("debito", "Débito"),
        ("credito", "Crédito"),
        ("efectivo", "Efectivo"),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tarjetas")
    ultimos_4_digitos = models.CharField(max_length=4, blank=True, null=True)
    tipo_tarjeta = models.CharField(max_length=20, choices=TIPO_CHOICES, default="debito")
    banco = models.CharField(max_length=100)
    monto = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = "tarjeta"
        verbose_name_plural = "tarjetas"

    def __str__(self):
        if self.ultimos_4_digitos:
            return f"{self.banco} ****{self.ultimos_4_digitos} ({self.usuario.username})"
        return f"{self.banco} ({self.usuario.username})"


class Movimiento(models.Model):
    MEDIO_CHOICES = [
        ("tarjeta", "Tarjeta"),
        ("efectivo", "Efectivo"),
        ("transferencia", "Transferencia"),
    ]
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="movimientos")
    fecha = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.CharField(max_length=255, blank=True)
    concepto = models.ForeignKey(Concepto, on_delete=models.PROTECT, related_name="movimientos")
    tipo = models.ForeignKey(TipoMovimiento, on_delete=models.PROTECT, related_name="movimientos")
    tarjeta = models.ForeignKey(Tarjeta, on_delete=models.SET_NULL, null=True, blank=True, related_name="movimientos")
    tarjeta_destino = models.ForeignKey(
        Tarjeta, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="transferencias_recibidas"
    )
    medio = models.CharField(max_length=20, choices=MEDIO_CHOICES, blank=True, null=True)

    class Meta:
        verbose_name = "movimiento"
        verbose_name_plural = "movimientos"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.fecha} | {self.tipo} | ${self.monto}"

    def aplicar_saldo(self):
        """Aplica el efecto del movimiento sobre las tarjetas."""
        tipo = self.tipo.nombre.lower()
        if self.tarjeta:
            if "ingreso" in tipo:
                self.tarjeta.monto += self.monto
            elif "gasto" in tipo:
                self.tarjeta.monto -= self.monto
            elif "transferencia" in tipo:
                self.tarjeta.monto -= self.monto
                if self.tarjeta_destino:
                    self.tarjeta_destino.monto += self.monto
                    self.tarjeta_destino.save()
            self.tarjeta.save()

    def revertir_saldo(self):
        """Revierte el efecto del movimiento sobre las tarjetas."""
        tipo = self.tipo.nombre.lower()
        if self.tarjeta:
            if "ingreso" in tipo:
                self.tarjeta.monto -= self.monto
            elif "gasto" in tipo:
                self.tarjeta.monto += self.monto
            elif "transferencia" in tipo:
                self.tarjeta.monto += self.monto
                if self.tarjeta_destino:
                    self.tarjeta_destino.monto -= self.monto
                    self.tarjeta_destino.save()
            self.tarjeta.save()


class PresupuestoMensual(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="presupuestos")
    concepto = models.ForeignKey(Concepto, on_delete=models.PROTECT, related_name="presupuestos")
    monto_asignado = models.DecimalField(max_digits=12, decimal_places=2)
    mes = models.DateField()  # siempre primer día del mes

    class Meta:
        verbose_name = "presupuesto mensual"
        verbose_name_plural = "presupuestos mensuales"
        unique_together = ("usuario", "concepto", "mes")

    def __str__(self):
        return f"{self.usuario.username} | {self.concepto} | {self.mes:%Y-%m}"

    def monto_usado(self):
        from django.db.models import Sum
        from django.db.models.functions import Coalesce
        from decimal import Decimal
        return Movimiento.objects.filter(
            usuario=self.usuario,
            concepto=self.concepto,
            tipo__nombre__icontains="gasto",
            fecha__year=self.mes.year,
            fecha__month=self.mes.month,
        ).aggregate(total=Coalesce(Sum("monto"), Decimal("0.00")))["total"]

    def monto_restante(self):
        return self.monto_asignado - self.monto_usado()