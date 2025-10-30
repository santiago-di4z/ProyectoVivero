from django.db import models

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
class Productor(models.Model):
    tipo_documento = models.CharField(max_length=20)
    numero_documento = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    correo = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.numero_documento})"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
class Finca(models.Model):
    productor = models.ForeignKey(Productor, on_delete=models.CASCADE, related_name='fincas')
    numero_catastro = models.CharField(max_length=100)
    municipio = models.CharField(max_length=200)

    class Meta:
        unique_together = ('productor', 'numero_catastro')
    
    def __str__(self):
        return f"Finca {self.numero_catastro} - {self.municipio}"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
class Vivero(models.Model):
    finca = models.ForeignKey(Finca, on_delete=models.CASCADE, related_name='viveros')
    codigo = models.CharField(max_length=100)
    tipo_cultivo = models.CharField(max_length=200)

    class Meta:
        unique_together = ('finca', 'codigo')

    def __str__(self):
        return f"Vivero {self.codigo} ({self.tipo_cultivo})"

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
class ProductoControl(models.Model):
    registro_ica = models.CharField(max_length=100, blank=True, null=True)
    nombre = models.CharField(max_length=200)
    frecuencia_aplicacion = models.PositiveIntegerField(help_text="Dias entre aplicaciones")
    valor = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre}"
    
class ControlHongo(ProductoControl):
    periodo_carencia = models.PositiveIntegerField(help_text="Dias de carencia")
    nombre_hongo = models.CharField(max_length=200)

class ControlPlaga(ProductoControl):
    periodo_carencia = models.PositiveIntegerField(help_text="Dias de carencia")

class ControlFertilizante(ProductoControl):
    fecha_aplicacion = models.DateField(blank=True, null=True)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
class Labor(models.Model):
    TIPO_LABOR = [
        ('HONGO', 'Aplicacion Hongo'),
        ('PLAGA', 'Aplicacion Plaga'),
        ('FERTILIZANTE', 'Aplicacion Fertilizante'),
        ('OTRA', 'Otra Labor'),
    ]

    vivero = models.ForeignKey(Vivero, on_delete=models.CASCADE, related_name='labores')
    fecha = models.DateField()
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=20, choices=TIPO_LABOR)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"Labor {self.tipo} - {self.fecha}"
    
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - #
class LaborProducto(models.Model):
    labor = models.ForeignKey(Labor, on_delete=models.CASCADE, related_name="productos_usados")
    producto = models.ForeignKey(ProductoControl, on_delete=models.CASCADE, related_name="labores_asociadas")
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_aplicacion = models.DateField()

    def __str__(self):
        return f"{self.producto.nombre} aplicado el {self.fecha_aplicacion}"
