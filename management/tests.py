from decimal import Decimal
from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from management.models import (
    Productor, Finca, Vivero,
    ProductoControl, ControlHongo, ControlPlaga, ControlFertilizante,
    Labor, LaborProducto
)
from datetime import date

# - - - - / PRODUCTOR / - - - - #
class ProductorModelTest(TestCase):
    def setUp(self):
        self.valid_data = {
            "tipo_documento": "CC",
            "numero_documento": "12345678",
            "nombre": "Luis",
            "apellido": "Gómez",
            "telefono": "3100000000",
            "correo": "luis@example.com"
        }

    def test_crear_productor_valido(self):
        p = Productor(**self.valid_data)
        # full_clean should pass for valid model
        p.full_clean()
        p.save()
        self.assertTrue(Productor.objects.filter(numero_documento="12345678").exists())

    def test_campos_obligatorios_faltantes(self):
        # quitar un campo obligatorio y esperar ValidationError
        data = self.valid_data.copy()
        data.pop("nombre")
        p = Productor(**data)
        with self.assertRaises(ValidationError):
            p.full_clean()

    def test_numero_documento_unico(self):
        Productor.objects.create(**self.valid_data)
        # intentar crear otro productor con mismo numero_documento provoca IntegrityError al guardar
        dup = Productor(**self.valid_data)
        with self.assertRaises(IntegrityError):
            # bypass full_clean to test constraint at DB level
            dup.save()

# - - - - / FINCA / - - - - #
class FincaModelTest(TestCase):
    def setUp(self):
        self.productor = Productor.objects.create(
            tipo_documento="CC", numero_documento="2222", nombre="Ana", apellido="Perez",
            telefono="3000000000", correo="ana@example.com"
        )
        self.valid_data = {
            "productor": self.productor,
            "numero_catastro": "F-001",
            "municipio": "Pereira"
        }

    def test_crear_finca_valida(self):
        f = Finca(**self.valid_data)
        f.full_clean()
        f.save()
        self.assertTrue(Finca.objects.filter(numero_catastro="F-001", productor=self.productor).exists())

    def test_campos_obligatorios_faltantes(self):
        data = self.valid_data.copy()
        data.pop("municipio")
        f = Finca(**data)
        with self.assertRaises(ValidationError):
            f.full_clean()

    def test_unique_together_productor_numero_catastro(self):
        Finca.objects.create(**self.valid_data)
        duplicate = Finca(**self.valid_data)
        with self.assertRaises(IntegrityError):
            duplicate.save()

# - - - - / VIVERO / - - - - #
class ViveroModelTest(TestCase):
    def setUp(self):
        self.productor = Productor.objects.create(
            tipo_documento="CC", numero_documento="3333", nombre="Carlos", apellido="Lopez",
            telefono="3000000001", correo="carlos@example.com"
        )
        self.finca = Finca.objects.create(
            productor=self.productor, numero_catastro="F-002", municipio="Armenia"
        )
        self.valid_data = {
            "finca": self.finca,
            "codigo": "V-01",
            "tipo_cultivo": "Café"
        }

    def test_crear_vivero_valido(self):
        v = Vivero(**self.valid_data)
        v.full_clean()
        v.save()
        self.assertTrue(Vivero.objects.filter(codigo="V-01", finca=self.finca).exists())

    def test_campos_obligatorios_faltantes(self):
        data = self.valid_data.copy()
        data.pop("tipo_cultivo")
        v = Vivero(**data)
        with self.assertRaises(ValidationError):
            v.full_clean()

    def test_unique_together_finca_codigo(self):
        Vivero.objects.create(**self.valid_data)
        dup = Vivero(**self.valid_data)
        with self.assertRaises(IntegrityError):
            dup.save()

# - - - - / PRODUCTO CONTROL / - - - - #
class ProductoControlModelTest(TestCase):
    def setUp(self):
        # datos mínimos válidos (valida creación de cada subtipo)
        self.base_data = {
            "registro_ica": "ICA-001",
            "nombre": "Producto X",
            "frecuencia_aplicacion": 30,
            "valor": Decimal("10000.00"),
        }

    def test_crear_control_hongo_valido(self):
        data = self.base_data.copy()
        hongo = ControlHongo(**data, periodo_carencia=21, nombre_hongo="Helminthosporium")
        hongo.full_clean()
        hongo.save()
        # al guardar, debe existir como ProductoControl también
        self.assertTrue(ProductoControl.objects.filter(id=hongo.productocontrol_ptr_id).exists())

    def test_crear_control_plaga_valido(self):
        data = self.base_data.copy()
        plaga = ControlPlaga(**data, periodo_carencia=14)
        plaga.full_clean()
        plaga.save()
        self.assertTrue(ProductoControl.objects.filter(id=plaga.productocontrol_ptr_id).exists())

    def test_crear_control_fertilizante_valido(self):
        data = self.base_data.copy()
        fert = ControlFertilizante(**data, fecha_aplicacion=date.today())
        fert.full_clean()
        fert.save()
        self.assertTrue(ProductoControl.objects.filter(id=fert.productocontrol_ptr_id).exists())

    def test_campos_obligatorios_faltantes_en_base(self):
        # Quitar el campo 'nombre' que debería ser obligatorio en la base
        data = self.base_data.copy()
        data.pop("nombre")
        prod = ProductoControl(**data)
        with self.assertRaises(ValidationError):
            prod.full_clean()

    def test_frecuencia_aplicacion_debe_ser_positiva(self):
        data = self.base_data.copy()
        data["frecuencia_aplicacion"] = -1
        prod = ProductoControl(**data)
        with self.assertRaises(ValidationError):
            prod.full_clean()

# - - - - / LABOR / - - - - #
class LaborModelTest(TestCase):
    def setUp(self):
        self.productor = Productor.objects.create(
            tipo_documento="CC", numero_documento="4444", nombre="María", apellido="Diaz",
            telefono="3000000002", correo="maria@example.com"
        )
        self.finca = Finca.objects.create(productor=self.productor, numero_catastro="F-003", municipio="Cali")
        self.vivero = Vivero.objects.create(finca=self.finca, codigo="V-02", tipo_cultivo="Tomate")
        self.valid_data = {
            "vivero": self.vivero,
            "fecha": date.today(),
            "descripcion": "Aplicación preventiva",
            "tipo": "PLAGA"
        }

    def test_crear_labor_valida(self):
        l = Labor(**self.valid_data)
        l.full_clean()
        l.save()
        self.assertTrue(Labor.objects.filter(vivero=self.vivero, tipo="PLAGA").exists())

    def test_campos_obligatorios_faltantes(self):
        data = self.valid_data.copy()
        data.pop("fecha")
        l = Labor(**data)
        with self.assertRaises(ValidationError):
            l.full_clean()

    def test_relacion_vivero_obligatoria(self):
        data = self.valid_data.copy()
        data["vivero"] = None
        l = Labor(**data)
        # al no tener vivero, al intentar full_clean/save debe fallar
        with self.assertRaises(ValidationError):
            l.full_clean()

# - - - - / LABOR <---> PRODUCTP / - - - - #
class LaborProductoModelTest(TestCase):
    def setUp(self):
        # crear productor/finca/vivero/labor y un producto
        self.prod = Productor.objects.create(tipo_documento="CC", numero_documento="5555",
                                             nombre="Pedro", apellido="Sanchez", telefono="3000000003",
                                             correo="pedro@example.com")
        self.finca = Finca.objects.create(productor=self.prod, numero_catastro="F-004", municipio="Bogotá")
        self.vivero = Vivero.objects.create(finca=self.finca, codigo="V-03", tipo_cultivo="Plátano")
        self.labor = Labor.objects.create(vivero=self.vivero, fecha=date.today(),
                                          descripcion="Aplicación X", tipo="HONGO")
        self.producto = ControlHongo.objects.create(
            registro_ica="ICA-900", nombre="Fungicida Y", frecuencia_aplicacion=30,
            valor=Decimal("5000.00"), periodo_carencia=10, nombre_hongo="Fusarium"
        )
        self.valid_data = {
            "labor": self.labor,
            "producto": self.producto,
            "cantidad": Decimal("1.50"),
            "fecha_aplicacion": date.today()
        }

    def test_crear_labor_producto_valido(self):
        lp = LaborProducto(**self.valid_data)
        lp.full_clean()
        lp.save()
        self.assertTrue(LaborProducto.objects.filter(labor=self.labor, producto=self.producto).exists())

    def test_campos_obligatorios_faltantes(self):
        data = self.valid_data.copy()
        data.pop("cantidad")
        lp = LaborProducto(**data)
        with self.assertRaises(ValidationError):
            lp.full_clean()

    def test_relaciones_obligatorias(self):
        # intentar crear sin labor o sin producto
        data = self.valid_data.copy()
        data["labor"] = None
        lp = LaborProducto(**data)
        with self.assertRaises(ValidationError):
            lp.full_clean()

        data = self.valid_data.copy()
        data["producto"] = None
        lp2 = LaborProducto(**data)
        with self.assertRaises(ValidationError):
            lp2.full_clean()
