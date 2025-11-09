import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk


DB_NAME = "registros.db"

class Conexion:
    @staticmethod
    def get_conn():
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn


class Pedidos:
    def __init__(self, marca, categoria, color):
        self.marca = marca
        self.categoria = categoria
        self.color = color

    @staticmethod
    def _conn():
        conn = Conexion.get_conn()
        c = conn.cursor()
        c.execute('''
                  CREATE TABLE IF NOT EXISTS pedidos
                  (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      marca TEXT NOT NULL,
                      categoria TEXT NOT NULL,
                      color TEXT NOT NULL,
                      cantidad INTEGER DEFAULT 0,
                      estado TEXT DEFAULT 'en proceso'
                  )
                  ''')
        conn.commit()
        return conn

    def guardar(self):
        with self._conn() as conn:
            c = conn.cursor()
            c.execute(
                'INSERT INTO pedidos (marca, categoria, color) VALUES (?, ?, ?)',
                (self.marca, self.categoria, self.color)
            )
            conn.commit()  # ← se guarda bien ahora
            id_generado = c.lastrowid
            messagebox.showinfo("Éxito", "Pedido registrado correctamente")
            return id_generado

    @staticmethod
    def actualizar_total(corte_id):
        with Pedidos._conn() as conn:
            c = conn.cursor()
            c.execute(
                '''UPDATE pedidos 
                   SET cantidad = (SELECT COALESCE(SUM(cantidad),0) FROM bandos WHERE corte = ?)''',
                (corte_id,)
            )

    @staticmethod
    def listar():
        conn = Pedidos._conn()
        c = conn.cursor()
        c.execute("SELECT id, marca, categoria, color FROM pedidos")
        pedidos = c.fetchall()
        conn.close()

        if not pedidos:
            raise ValueError("No hay pedidos en proceso registrados.")
        return pedidos

    @staticmethod
    def buscar(id_corte):
        with Pedidos._conn() as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            cur = c.execute("SELECT * FROM pedidos WHERE id = ?", (id_corte,))
            return cur.fetchone()

    @staticmethod
    def actualizar_estado(id_corte, nuevo_estado):
        with Pedidos._conn() as conn:
            c = conn.cursor()
            c.execute("UPDATE pedidos SET estado = ? WHERE id = ?", (nuevo_estado, id_corte))
            conn.commit()


class TallasCorte:
    def __init__(self, corte, talla, cantidad):
        self.corte = corte
        self.talla = talla
        self.cantidad = cantidad

    @staticmethod
    def _conn():
        with Conexion.get_conn() as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS tallas_corte
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    corte INTEGER NOT NULL,
                    talla INTEGER NOT NULL,
                    cantidad_max INTEGER NOT NULL,
                    FOREIGN KEY(corte) REFERENCES pedidos (id)
                )
                    ''')
            conn.commit()
            return conn

    def agregar_talla(self):
        conn = self._conn()
        c = conn.cursor()

        tallas_permitidas = [0, 2, 4, 6, 8, 10, 12, 14, 16, 28, 30, 32, 34, 36, 38, 40, 42, 44]
        if self.talla not in tallas_permitidas:
            raise ValueError(f"Talla {self.talla} no permitida.")

        c.execute('''
            INSERT INTO tallas_corte (corte, talla, cantidad_max)
            VALUES (?, ?, ?)
        ''', (self.corte, self.talla, self.cantidad))
        conn.commit()
        conn.close()
        messagebox.showinfo("Éxito", f"Talla {self.talla} agregada correctamente")

    @staticmethod
    def obtener_tallas_corte(corte):
        with Pedidos._conn() as conn:
            c = conn.cursor()
            cur = c.execute('SELECT * FROM tallas_corte WHERE corte = ?', (corte,))
            tallas = cur.fetchall()
            if not tallas:
                raise ValueError("El corte no tiene tallas registradas.")
            return [fila[2] for fila in tallas]

    @staticmethod
    def obtener_tallas_cantidades(corte):
        with TallasCorte._conn() as conn:
            c = conn.cursor()
            datos = c.execute("SELECT talla, cantidad_max FROM tallas_corte WHERE corte=?", (corte,)).fetchall()
            return {t: cant for t, cant in datos}


class Bandos:
    def __init__(self, corte, talla, cantidad):
        self.corte = corte
        self.talla = talla
        self.cantidad = cantidad

    @staticmethod
    def _conn():
        with Conexion.get_conn() as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS bandos
                (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    corte INTEGER NOT NULL,
                    talla INTEGER NOT NULL,
                    cantidad INTEGER NOT NULL,
                    FOREIGN KEY(corte) REFERENCES pedidos(id)
                )
                    ''')
            conn.commit()
            return conn

    def agregar_bando(self):
        conn = self._conn()
        c = conn.cursor()

        c.execute(
            'SELECT cantidad_max FROM tallas_corte WHERE corte = ? AND talla = ?',
            (self.corte, self.talla)
        )
        talla_info = c.fetchone()
        if not talla_info:
            raise ValueError(f"El corte {self.corte} no contiene talla {self.talla}.")

        cantidad_max = talla_info["cantidad_max"]

        c.execute(
            'SELECT IFNULL(SUM(cantidad),0) as total FROM bandos WHERE corte = ? AND talla = ?',
            (self.corte, self.talla)
        )
        total_actual = c.fetchone()["total"]

        if total_actual + self.cantidad > cantidad_max:
            raise ValueError(f"No se puede agregar {self.cantidad} unidades. "
                  f"\nEl máximo permitido para talla {self.talla} es {cantidad_max}. "
                  f"\n(Actual: {total_actual})")

        c.execute(
            'INSERT INTO bandos (corte, talla, cantidad) VALUES (?, ?, ?)',
            (self.corte, self.talla, self.cantidad)
        )
        conn.commit()
        conn.close()

        Pedidos.actualizar_total(self.corte)
        messagebox.showinfo("'Exito", f"Bando agregado al corte {self.corte}"
                                      f"\nTalla {self.talla}: {self.cantidad} unidades.")

    @staticmethod
    def obtener_num_bandos_corte(corte):
        with Bandos._conn() as conn:
            c = conn.cursor()
            cur = c.execute('SELECT * FROM bandos WHERE corte = ?', (corte,))
            bandos = cur.fetchall()
            if not bandos:
                return "sin bandos"
            return bandos

    @staticmethod
    def obtener_bandos_corte(corte):
        with Bandos._conn() as conn:
            c = conn.cursor()
            datos = c.execute("SELECT id, talla, cantidad FROM bandos WHERE corte=?", (corte,)).fetchall()
            return [{"id": b, "talla": t, "cantidad": cant} for b, t, cant in datos]


class Operaciones:
    def __init__(self, nombre, small_price, big_price):
        self.nombre = nombre
        self.small_price = small_price
        self.big_price = big_price

    @staticmethod
    def _conn():
        c = Conexion.get_conn()
        c.execute('''
        CREATE TABLE IF NOT EXISTS operaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        small_price  REAL NOT NULL,
        big_price  REAL NOT NULL)
        ''')
        c.commit()
        return c

    def guardar(self):
        with self._conn() as cursor:
            cursor.execute(
                "INSERT INTO operaciones (nombre, small_price, big_price) VALUES (?, ?, ?)",
                (self.nombre, self.small_price, self.big_price)
            )

    @staticmethod
    def listar():
        conn = Operaciones._conn()
        cursor = conn.cursor()
        operaciones = cursor.execute("SELECT * FROM operaciones").fetchall()
        conn.close()

        if not operaciones:
            raise ValueError("No hay operaciones registradas.")
        return operaciones

    @staticmethod
    def buscar(id):
        with Operaciones._conn() as cursor:
            operacion = cursor.execute('SELECT * FROM operaciones Where id = ?', (id,)).fetchone()
            if not operacion:
                raise ValueError("No se encontró ninguna operación.")
            return operacion

    @staticmethod
    def modificar(id, nombre, small_price, big_price):
        with Operaciones._conn() as cursor:
            cur = cursor.execute('SELECT * FROM operaciones WHERE id = ?', (id,))
            fila = cur.fetchone()
            if not fila:
                raise ValueError("No se encontró ninguna operación con ese nombre!")
            cursor.execute(
                "UPDATE operaciones SET nombre = ?, small_price = ?, big_price = ? WHERE id = ?",
                (nombre, small_price, big_price, id)
            )
        messagebox.showinfo("Éxito", "Se guradaron los cambios correctamente")

    @staticmethod
    def eliminar(id):
        conn = Operaciones._conn()
        cursor = conn.cursor()
        cur = cursor.execute('DELETE FROM operaciones WHERE id = ?', (id,))
        if cur.rowcount == 0:
            raise ValueError("No se encontró ninguna operación con el nombre ingresado!")
        conn.commit()
        conn.close()
        messagebox.showinfo("Éxito", "Se eliminaron los datos de la operación.")


class Empleados:
    def __init__(self, nombre, telefono, area):
        self.nombre = nombre
        self.telefono = telefono
        self.area = area

    @staticmethod
    def _conn():
        c = Conexion.get_conn()
        c.execute('''
        CREATE TABLE IF NOT EXISTS empleados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono INTEGER NOT NULL,
            area TEXT NOT NULL
        )
        ''')
        c.commit()
        return c

    def guardar(self):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO empleados (nombre, telefono, area) VALUES (?, ?, ?)",
            (self.nombre, self.telefono, self.area)
        )
        conn.commit()
        conn.close()

    def obtener_id(self):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute('SELECT * FROM empleados WHERE nombre = ?', (self.nombre,))
        fila = cur.fetchone()
        conn.close()
        if not fila:
            raise ValueError("No se encontró a ningún empleado")
        else:
            return fila['id']

    @staticmethod
    def listar():
        conn = Empleados._conn()
        cur = conn.cursor()
        cur.execute('SELECT * FROM empleados')
        lista = cur.fetchall()
        conn.close()
        if len(lista) < 2:
            raise ValueError("No hay empleados registrados!")
        return lista

    @staticmethod
    def consultar(id_empleado):
        conn = Empleados._conn()
        cur = conn.cursor()
        cur.execute('SELECT * FROM empleados WHERE id = ?', (id_empleado,))
        empleado = cur.fetchone()
        if not empleado:
            raise ValueError("No se encontró a ningpun empleado")
        return empleado

    @staticmethod
    def buscar_empleado_costura():
        conn = Empleados._conn()
        cur = conn.cursor()
        cur.execute("SELECT id, nombre FROM empleados WHERE area = 'Costura'")
        empleados_costura = cur.fetchall()
        if not empleados_costura:
            raise ValueError("No hay empleados en el área de costura")
        return [f"{e['id']} - {e['nombre']}" for e in empleados_costura]

    @staticmethod
    def modificar(id, nombre, telefono, area):
        conn = Empleados._conn()
        cur = conn.cursor()
        cur.execute('SELECT * FROM empleados WHERE id = ?', (id,))
        fila = cur.fetchone()
        if not fila:
            conn.close()
            raise ValueError("No se encontró a ningún empleado!")
        cur.execute(
            "UPDATE empleados SET nombre=?, telefono=?, area=? WHERE id=?",
            (nombre, telefono, area, id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def eliminar(id):
        conn = Empleados._conn()
        cur = conn.cursor()
        cur.execute('DELETE FROM empleados WHERE id = ?', (id,))
        if cur.rowcount == 0:
            conn.close()
            raise ValueError("No se encontró ningún empleado!")
        conn.commit()
        conn.close()
        messagebox.showinfo("Éxito", f"Se eliminó al empleado {id} del registro")


class Salarios:
    def __init__(self, id_empleado, salario):
        self.id_empleado = id_empleado
        self.salario = salario

    @staticmethod
    def _conn():
        conn = Conexion.get_conn()
        conn.execute('''
        CREATE TABLE IF NOT EXISTS salarios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_empleado INTEGER NOT NULL,
            salario REAL NOT NULL,
            FOREIGN KEY(id_empleado) REFERENCES empleados(id)
        )
        ''')
        conn.commit()
        return conn

    def agregar_salario(self):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO salarios(id_empleado, salario) VALUES (?, ?)",
            (self.id_empleado, self.salario)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def modificar_salario(id_empleado, nuevo_salario):
        conn = Salarios._conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM salarios WHERE id_empleado = ?", (id_empleado,))
        fila = cur.fetchone()
        if not fila:
            conn.close()
            messagebox.showerror("Error", "No se encontró el salario del empleado")
            return
        cur.execute(
            "UPDATE salarios SET salario = ? WHERE id_empleado = ?",
            (nuevo_salario, id_empleado)
        )
        conn.commit()
        conn.close()
        messagebox.showinfo("Éxito", "El salario se modificó correctamente")

    @staticmethod
    def mostrar_salario(id_empleado):
        conn = Salarios._conn()
        cur = conn.cursor()
        cur.execute("SELECT salario FROM salarios WHERE id_empleado = ?", (id_empleado,))
        fila = cur.fetchone()
        conn.close()
        if fila:
            return fila['salario']
        else:
            return 0.0

    @staticmethod
    def eliminar(id_empleado):
        conn = Salarios._conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM salarios WHERE id_empleado = ?", (id_empleado,))
        if cur.rowcount == 0:
            conn.close()
            return
        conn.commit()
        conn.close()

class Tareas:
    def __init__(self, id_empleado, corte, bando, operacion, fecha=None):
        self.id_empleado = id_empleado
        self.corte = corte
        self.bando = bando
        self.operacion = operacion
        self.fecha = fecha

    @staticmethod
    def _conn():
        conn = Conexion.get_conn()
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_empleado INTEGER NOT NULL,
            corte INTEGER NOT NULL,
            bando TEXT NOT NULL,
            operacion INTEGER NOT NULL,
            fecha TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(id_empleado) REFERENCES empleados(id),
            FOREIGN KEY(corte) REFERENCES pedidos(id),
            FOREIGN KEY(bando) REFERENCES bandos(id),
            FOREIGN KEY(operacion) REFERENCES operaciones(id)
        )
        ''')
        conn.commit()
        return conn

    def guardar(self):
        with self._conn() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO tareas (id_empleado, corte, bando, operacion, fecha) VALUES (?, ?, ?, ?, datetime('now'))",
                (self.id_empleado, self.corte, self.bando, self.operacion)
            )
            conn.commit()
            messagebox.showinfo("Éxito", "Tarea asignada correctamente")

    @staticmethod
    def listar_por_empleado(id_empleado):
        with Tareas._conn() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM tareas WHERE id_empleado = ?", (id_empleado,))
            lista = c.fetchall()
            if not lista:
                raise ValueError("No se le han asignado tareas aún.")
            return lista

    @staticmethod
    def eliminar(id_tarea):
        with Tareas._conn() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM tareas WHERE id = ?", (id_tarea,))
            conn.commit()
            messagebox.showinfo("Éxito", "Tarea eliminada correctamente")



class Reportes:
    def __init__(self, id_tarea, fecha, estado):
        self.id_tarea = id_tarea
        self.fecha = fecha
        self.estado = estado

    @staticmethod
    def _conn():
        conn = Conexion.get_conn()
        conn.execute('''
        CREATE TABLE IF NOT EXISTS reportes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_tarea INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            estado TEXT NOT NULL,
            FOREIGN KEY(id_tarea) REFERENCES tareas(id)
        )
        ''')
        conn.commit()
        return conn

    def guardar(self):
        with self._conn() as cursor:
            cursor.execute(
                "INSERT INTO reportes(id_tarea, fecha, estado) VALUES (?, ?, ?)",
                (self.id_tarea, self.fecha, self.estado)
            )

    @staticmethod
    def listar():
        with Reportes._conn() as cursor:
            datos = cursor.execute(
                '''SELECT r.id, t.id_empleado, t.corte, t.bandos, t.operacion, 
                          r.fecha, r.estado
                   FROM reportes r 
                   INNER JOIN tareas t ON r.id_tarea = t.id'''
            ).fetchall()
            return datos

    @staticmethod
    def eliminar(id_reporte):
        with Reportes._conn() as cursor:
            cursor.execute("DELETE FROM reportes WHERE id = ?", (id_reporte,))

    @staticmethod
    def buscar_por_empleado(id_empleado):
        with Reportes._conn() as cursor:
            datos = cursor.execute(
                '''SELECT r.id, t.id_empleado, t.corte, t.bandos, t.operacion, 
                          r.fecha, r.estado
                   FROM reportes r 
                   INNER JOIN tareas t ON r.id_tarea = t.id
                   WHERE t.id_empleado = ?''',
                (id_empleado,)
            ).fetchall()
            return datos

    @staticmethod
    def registrar_tarea(id_tarea):
        with Reportes._conn() as cursor:
            tarea = cursor.execute("SELECT * FROM tareas WHERE id = ?", (id_tarea,)).fetchone()
            if tarea is None:
                raise ValueError("La tarea no existe o ya fue procesada.")

            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            estado = "Completada"
            cursor.execute(
                "INSERT INTO reportes(id_tarea, fecha, estado) VALUES (?, ?, ?)",
                (id_tarea, fecha, estado)
            )
            cursor.execute("DELETE FROM tareas WHERE id = ?", (id_tarea,))


class Cuentas:
    def __init__(self, id_empleado, usuario, password, rol):
        self.id_empleado = id_empleado
        self.usuario = usuario
        self.password = password
        self.rol = rol

    @staticmethod
    def _conn():
        conn = Conexion.get_conn()
        conn.execute('''
        CREATE TABLE IF NOT EXISTS cuentas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_empleado INTEGER NOT NULL,
        usuario TEXT NOT NULL,
        password TEXT NOT NULL,
        rol TEXT NOT NULL,
        FOREIGN KEY(id_empleado) REFERENCES empleados(id));
                     ''')
        conn.commit()
        return conn

    def guardar(self):
        with self._conn() as cursor:
            cursor.execute(
                "INSERT INTO cuentas(id_empleado, usuario, password, rol) VALUES (?, ?, ?, ?)",
                (self.id_empleado, self.usuario, self.password, self.rol)
            )
        messagebox.showinfo("Éxito", "Cuenta creada correctamente!")

    @staticmethod
    def listar():
        with Cuentas._conn() as cursor:
            cur = cursor.execute("SELECT * FROM cuentas").fetchall()
            if not cur:
                return False
            return True

    @staticmethod
    def buscar(usuario, password):
        with Cuentas._conn() as cursor:
            cur = cursor.execute("SELECT rol FROM cuentas WHERE usuario = ? AND password = ?" ,
                                 (usuario, password)).fetchone()
            if not cur:
                raise ValueError("Usuario o contraseña incorrectos!")
            return cur['rol']

    @staticmethod
    def eliminar(id_empleado):
        with Cuentas._conn() as cursor:
            cur = cursor.execute("DELETE FROM cuentas WHERE id_empleado = ?", (id_empleado,))


class VentanaConfirmacion(tk.Toplevel):
    def __init__(self, parent, mensaje):
        super().__init__(parent)
        self.title("Confirmación")
        self.geometry("320x150")
        self.configure(bg='white')
        self.resizable(False, False)
        self.resultado = False

        tk.Label(self, text=mensaje, bg='white', fg='black', font=("Arial", 10), wraplength=280, justify="center").pack(pady=20)

        frame_botones = tk.Frame(self, bg='white')
        frame_botones.pack(pady=10)

        tk.Button(frame_botones, text="Confirmar", bg="#28A745", fg="white", font=("Arial", 9, "bold"),
                  relief='flat', width=12, command=self.confirmar).pack(side='left', padx=10)
        tk.Button(frame_botones, text="Cancelar", bg="#DC3545", fg="white", font=("Arial", 9, "bold"),
                  relief='flat', width=12, command=self.cancelar).pack(side='left', padx=10)

        self.transient(parent)
        self.grab_set()
        self.wait_window(self)

    def confirmar(self):
        self.resultado = True
        self.destroy()

    def cancelar(self):
        self.resultado = False
        self.destroy()


class InterfazGrafica:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OPERGest")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        self.root.configure(bg='white')

        self.centrar_ventana(500, 600)

        self.usuario_actual = None
        self.tipo_usuario = None

        self.contenedor = tk.Frame(self.root, bg='white')
        self.contenedor.pack(fill='both', expand=True)

        self.ventana_login()

    def centrar_ventana(self, ancho, alto):
        ancho_pantalla = self.root.winfo_screenwidth()
        alto_pantalla = self.root.winfo_screenheight()
        x = (ancho_pantalla // 2) - (ancho // 2)
        y = (alto_pantalla // 2) - (alto // 2)
        self.root.geometry(f'{ancho}x{alto}+{x}+{y}')

    def limpiar_contenedor(self):
        for widget in self.contenedor.winfo_children():
            widget.destroy()

    def crear_cabecera_submenu(self, titulo):
        cabecera = tk.Frame(self.contenedor, bg='#0078D7', height=80)
        cabecera.pack(fill='x')
        cabecera.pack_propagate(False)

        tk.Label(cabecera, text=titulo,
                 font=("Arial", 10, "bold"), bg='#0078D7', fg='white').pack(pady=25)

    def crear_footer_volver(self, comando_volver):
        pied_pagina = tk.Frame(self.contenedor, bg='white')
        pied_pagina.pack(fill='x', padx=40, pady=20)

        boton_volver = tk.Button(pied_pagina, text="← Volver", bg='#FF8C00', fg='white',
                                  font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                                  command=comando_volver)
        boton_volver.pack(fill='x', ipady=10)

    def cerrar_sesion(self):
        self.usuario_actual = None
        self.usuario_actual = None
        self.ventana_login()

    def ventana_login(self):
        self.limpiar_contenedor()

        titulo = tk.Label(self.contenedor, text="INICIAR SESIÓN",
                          font=("Arial", 16, "bold"), fg="gray")
        titulo.pack(pady=40)

        subtitulo = tk.Label(self.contenedor, text="Iniciar sesión\nIngrese usuario y contraseña",
                             font=("Arial", 9), bg='white', fg='gray')
        subtitulo.pack(pady=10)

        frame = tk.Frame(self.contenedor, bg='white')
        frame.pack(pady=20, padx=50, fill='x')

        tk.Label(frame, text="Usuario:", font=("Arial", 10), bg='white').pack(anchor='w', pady=(10, 5))
        self.entry_usuario = tk.Entry(frame, font=("Arial", 10), relief='solid', bd=1)
        self.entry_usuario.pack(fill="x", ipady=8)

        tk.Label(frame, text="Contraseña:", font=("Arial", 10), bg='white').pack(anchor='w', pady=(20, 5))
        self.entry_password = tk.Entry(frame, show="*", font=("Arial", 10), relief='solid', bd=1)
        self.entry_password.pack(fill='x', ipady=8)
        self.entry_password.bind('<Return>', lambda e: self.iniciar_sesion())
        self.mostrar = False

        def alternar_password():
            if self.mostrar:
                self.entry_password.config(show='*')
                boton_ver.config(text="👁️mostrar")
                self.mostrar = False
            else:
                self.entry_password.config(show='')
                boton_ver.config(text="🙈ocultar")
                self.mostrar = True

        boton_ver = tk.Button(frame, text="👁️mostrar", bg='white', relief='flat', cursor="hand2",
                              command=alternar_password)
        boton_ver.pack(anchor='e', pady=(5, 0))

        boton_ingresar = tk.Button(frame, text="Ingresar", bg="#0078D7", fg='white',
                                   font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                                   command=self.iniciar_sesion)
        boton_ingresar.pack(fill='x', pady=(30, 10), ipady=10)

        boton_salir = tk.Button(frame, text="Salir", bg="#FF8C00", fg='white',
                                font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                                command=self.root.quit)
        boton_salir.pack(fill='x', ipady=10)

    def iniciar_sesion(self):
        usuario = self.entry_usuario.get()
        password = self.entry_password.get()
        lista_cuentas = Cuentas.listar()

        if usuario == "" or password == "":
            messagebox.showwarning("Campos vacíos", "Por favor complete todos los campos.")
        elif lista_cuentas:
            try:
                rol = Cuentas.buscar(usuario, password)
                self.tipo_usuario = str(rol)
                self.usuario_actual = usuario
                if self.tipo_usuario.lower() == "administrador":
                    self.menu_administrador()
                else:
                    self.menu_empleado()
            except ValueError as e:
                messagebox.showerror("Error", f"Error: {e}")
        else:
            if usuario == "admin" and password == "admin":
                self.crear_cuenta()
            else:
                messagebox.showerror("Error", "ERROR: Credenciales incorrectos")

    def crear_cuenta(self):
        self.limpiar_contenedor()

        titulo = tk.Label(self.contenedor, text="Crear cuenta",
                          font=("Arial", 16, "bold"), bg='white')
        titulo.pack(pady=40)

        subtitulo = tk.Label(self.contenedor, text="Ingresar datos\nIngrese nuevos datos para crear la cuenta",
                             font=("Arial", 9), bg='white', fg='gray')
        subtitulo.pack(pady=10)

        frame = tk.Frame(self.contenedor, bg="white")
        frame.pack(pady=20, padx=50, fill="x")

        usuario_actual = getattr(self, "tipo_usuario", None)

        if usuario_actual == "administrador":
            lista_emp = Empleados.listar()
            tk.Label(frame, text="Seleccione un empleado:", font=("Arial", 10), bg="white").pack(anchor="w", pady=(10, 5))
            empleados_disp = [f"{e['id']} - {e['nombre']}" for e in lista_emp if e['id'] != 1]
            combo_empleado = ttk.Combobox(frame, values=empleados_disp, state="readonly", font=("Arial", 10))
            combo_empleado.pack(fill="x", ipady=8, pady=(0, 15))
        else:
            combo_empleado = None

        tk.Label(frame, text="Nuevo usuario:", font=("Arial", 10), bg="white").pack(anchor="w", pady=(10, 5))
        entry_nuevo_usuario = tk.Entry(frame, font=("Arial", 10), relief="solid", bd=1)
        entry_nuevo_usuario.pack(fill="x", ipady=8)

        tk.Label(frame, text="Nueva contraseña:", font=("Arial", 10), bg="white").pack(anchor="w", pady=(20, 5))
        entry_new_pass = tk.Entry(frame, show="*", font=("Arial", 10), relief="solid", bd=1)
        entry_new_pass.pack(fill="x", ipady=8)
        self.mostrar = False

        def alternar_password():
            if self.mostrar:
                entry_new_pass.config(show='*')
                boton_ver.config(text="👁️mostrar")
                self.mostrar = False
            else:
                entry_new_pass.config(show='')
                boton_ver.config(text="🙈ocultar")
                self.mostrar = True

        boton_ver = tk.Button(frame, text="👁️mostrar", bg='white', relief='flat', cursor="hand2",
                              command=alternar_password)
        boton_ver.pack(anchor='e', pady=(5, 0))

        def guardar_nuevos_datos():
            nuevo_usuario = entry_nuevo_usuario.get().strip()
            new_pass = entry_new_pass.get().strip()

            if nuevo_usuario == "" or new_pass == "":
                messagebox.showwarning("Campos vacíos", "Por favor complete ambos campos.")
                return

            if usuario_actual == "administrador" and combo_empleado:
                seleccion = combo_empleado.get()
                if not seleccion:
                    messagebox.showwarning("Selección requerida", "Seleccione un empleado para crear la cuenta.")
                    return
                id_empleado = seleccion.split(" - ")[0]
            else:
                id_empleado = 1

            if not Cuentas.listar():
                admin = Empleados("admin", 0000, "administrador")
                admin.guardar()

            cuenta = Cuentas(id_empleado, nuevo_usuario, new_pass, "administrador" if id_empleado == 1 else "empleado")
            cuenta.guardar()

            if usuario_actual is None:
                self.ventana_login()
                boton_cancelar.config(command=self.ventana_login)
            else:
                self.gestion_empleados()
                boton_cancelar.config(command=self.gestion_empleados)

            messagebox.showinfo("Éxito", "Usuario y contraseña creada")

        boton_guardar = tk.Button(frame, text="Guardar cambios", bg="#0078D7", fg='white',
                                  font=("Arial", 10, "bold"), relief="flat", cursor="hand2",
                                  command=guardar_nuevos_datos)
        boton_guardar.pack(fill="x", pady=(30, 10), ipady=10)

        boton_cancelar = tk.Button(frame, text="Cancelar", bg="#FF8C00", fg='white',
                                   font=("Arial", 10, "bold"), relief="flat", cursor="hand2",
                                   command=self.ventana_login)
        boton_cancelar.pack(fill="x", ipady=10)

        if usuario_actual is None:
            boton_cancelar.config(command=self.ventana_login)
        else:
            boton_cancelar.config(command=self.gestion_empleados)

    #====VENTANA ADMINISTRADOR===
    def menu_administrador(self):
        self.limpiar_contenedor()

        cabecera = tk.Frame(self.contenedor, bg ='#0078D7', height=80)
        cabecera.pack(fill='x')
        cabecera.pack_propagate(False)

        tk.Label(cabecera, text=f"Bienvenido: {self.usuario_actual}",
                 font=("Arial", 14, "bold"), bg='#0078D7', fg='white').pack(pady=25)

        frame_contenido = tk.Frame(self.contenedor, bg='white')
        frame_contenido.pack(fill='both', expand=True, padx=40, pady=30)

        tk.Label(frame_contenido, text="Seleccione una opción",
                 font=("Arial", 12), bg='white', fg='gray').pack(pady=20)

        botones = [
            ("👥 Gestión de Empleados", self.gestion_empleados),
            ("📦 Gestión de Pedidos", self.gestion_pedidos),
            ("⚙️ Gestión de Operaciones", self.gestion_operaciones),
            ("✍️ Gestión de Tareas", self.gestion_tareas)
        ]

        for texto, comando in botones:
            boton = tk.Button(frame_contenido, text=texto, bg='#0078D7', fg='white',
                              font=("Arial", 11, "bold"), relief='flat', cursor="hand2",
                              command=comando)
            boton.pack(fill='x', pady=8, ipady=12)

        pied_pagina = tk.Frame(self.contenedor, bg='white')
        pied_pagina.pack(fill='x',padx=40, pady=20)

        boton_cerrar = tk.Button(pied_pagina, text="Cerrar Sesión", bg='#E84C3C', fg='white',
                                 font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                                 command=self.cerrar_sesion)
        boton_cerrar.pack(fill='x', ipady=10)

    #===VENTANA EMPLEADO===
    def menu_empleado(self):
        self.limpiar_contenedor()

        cabecera = tk.Frame(self.contenedor,bg='#0078D7', height=80)
        cabecera.pack(fill='x')
        cabecera.pack_propagate(False)

        tk.Label(cabecera, text=f"Bienvenidos: {self.tipo_usuario}",
                 font=("Arial", 14, "bold"), bg='#0078D7', fg='white').pack(pady=25)

        frame_contenido = tk.Frame(self.contenedor, bg='white')
        frame_contenido.pack(fill='both', expand=True, padx=40, pady=30)

        tk.Label(frame_contenido, text="Seleccione una opción",
                 font=("Arial", 12), bg='white', fg='gray').pack(pady=20)

        botones = [
            ("📋 Ver mis tareas", self.ver_tareas_empleado),
            ("✅ Completar operación", self.completar_operacion_empleado)
        ]

        for texto, comando in botones:
            boton = tk.Button(frame_contenido, text=texto, bg='#0078D7', fg='white',
                              font=("Arial", 11, "bold"), relief='flat', cursor="hand2",
                              command=comando)
            boton.pack(fill='x', pady=8, ipady=12)

        pied_pagina = tk.Frame(self.contenedor, bg='white')
        pied_pagina.pack(fill='x', padx=40, pady=20)

        boton_cerrar = tk.Button(pied_pagina, text="Cerrar Sesión", bg='#E74C3C', fg='white',
                                 font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                                 command=self.cerrar_sesion)
        boton_cerrar.pack(fill='x', ipady=10)

#===Ventanas de submenú administrador===
       #==SUBMENÚ GESTIÓN DE EMPLEADOS===
    def gestion_empleados(self):
        self.limpiar_contenedor()

        self.crear_cabecera_submenu("👥 Gestión de Empleados")

        frame_contenido = tk.Frame(self.contenedor, bg='white')
        frame_contenido.pack(fill='both', expand=True, padx=40, pady=30)

        botones = [
            ("Registrar empleado", self.registrar_empleado),
            ("Listar empleados", self.listar_empleados),
            ("Despedir empleado", self.despedir_empleado),
            ("Calcular pago", self.pagar),
            ("Crear cuenta", self.crear_cuenta)
        ]

        for texto, comando in botones:
            btn = tk.Button(frame_contenido, text=texto, bg="#0078D7", fg="white",
                            font=("Arial", 11, "bold"), relief='flat', cursor="hand2",
                            command=comando)
            btn.pack(fill='x', pady=8, ipady=12)

        self.crear_footer_volver(self.menu_administrador)

    #===SUBMENÚ GESTIÓN DE PEDIDOS===
    def gestion_pedidos(self):
        self.limpiar_contenedor()

        self.crear_cabecera_submenu("📦 Gestión de Pedidos")

        frame_contenido = tk.Frame(self.contenedor, bg='white')
        frame_contenido.pack(fill='both', expand=True, padx=40, pady=30)

        botones = [
            ("Registrar corte", self.registrar_corte),
            ("Agregar bandos", self.agregar_bandos),
            ("Ver cortes en proceso", self.listar_pedidos),
            ("Entregar Pedido", self.entregar_pedido)
        ]

        for texto, comando in botones:
            btn = tk.Button(frame_contenido, text=texto, bg="#0078D7", fg="white",
                            font=("Arial", 11, "bold"), relief='flat', cursor="hand2",
                            command=comando)
            btn.pack(fill='x', pady=8, ipady=12)

        self.crear_footer_volver(self.menu_administrador)

    #===SUBMENÚ GESTIÓN DE OPERACIONES===
    def gestion_operaciones(self):
        self.limpiar_contenedor()

        self.crear_cabecera_submenu("⚙️ Gestión de Operaciones")

        frame_contenido = tk.Frame(self.contenedor, bg='white')
        frame_contenido.pack(fill='both', expand=True, padx=40, pady=30)

        botones = [
            ("Registrar operación", self.registrar_operacion),
            ("Consultar operación", self.consultar_operacion)
        ]

        for texto, comando in botones:
            boton = tk.Button(frame_contenido, text=texto, bg='#0078D7', fg='white',
                              font=("Arial", 11, "bold"), relief='flat', cursor="hand2",
                              command=comando)
            boton.pack(fill='x', pady=8, ipady=12)

        self.crear_footer_volver(self.menu_administrador)

    #===SUBMENÚ GESTIÓN DE TAREAS===
    def gestion_tareas(self):
        self.limpiar_contenedor()
        self.crear_cabecera_submenu("✍️ Gestión de Tareas")

        try:
            Operaciones.listar()
            Pedidos.listar()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            self.menu_administrador()
            return

        frame_contenido = tk.Frame(self.contenedor, bg='white')
        frame_contenido.pack(fill='both', expand=True, padx=40, pady=30)

        botones = [
            ("Asignar Tareas", self.asignar_tareas),
            ("Lista de tareas", self.marcar_tareas),
            ("Ver reportes", self.ver_reportes)
        ]

        for texto, comando in botones:
            btn = tk.Button(frame_contenido, text=texto, bg="#0078D7", fg="white",
                            font=("Arial", 11, "bold"), relief='flat', cursor="hand2",
                            command=comando)
            btn.pack(fill='x', pady=8, ipady=12)

        self.crear_footer_volver(self.menu_administrador)

    #=====GESTIÓN EMPLEADOS=====
    def registrar_empleado(self):
        self.limpiar_contenedor()
        self.crear_cabecera_submenu("Registrar empleado")

        frame = tk.Frame(self.contenedor, bg='white')
        frame.pack(pady=20, padx=40, fill='both', expand=True)

        tk.Label(frame, text="Nombre:", font=("Arial", 10), bg='white', fg='gray').pack(anchor='w', pady=(10, 2))
        entry_nombre = tk.Entry(frame, font=("Arial", 10), relief='solid', bd=1)
        entry_nombre.pack(fill='x', ipady=8, pady=(5,15))

        tk.Label(frame, text="Teléfono:", font=("Arial", 10), bg='white', fg='gray').pack(anchor='w', pady=(10, 2))
        entry_telefono = tk.Entry(frame, font=("Arial", 10), relief='solid', bd=1)
        entry_telefono.pack(fill='x', ipady=8, pady=(5,15))

        areas = ["Corte", "Costura", "Empacar"]

        tk.Label(frame, text="Área:", font=("Arial", 10), bg='white', fg='gray').pack(anchor='w', pady=(10, 2))
        seleccion_area = ttk.Combobox(frame, values=areas, state='readonly', font=("Arial", 10))
        seleccion_area.pack(fill='x', ipady=8, pady=(5, 15))

        label_salario = tk.Label(frame, text='Salario por hora:', font=("Arial", 10), bg='white', fg='gray')
        entry_salario = tk.Entry(frame, font=("Arial", 10), relief='solid', bd=1)

        def solicitar_salario(evento):
            if seleccion_area.get().lower() in ('corte', 'empacar'):
                label_salario.pack(anchor='w', pady=(10, 2))
                entry_salario.pack(fill='x', ipady=8, pady=(5, 15))
            else:
                label_salario.pack_forget()
                entry_salario.pack_forget()

        seleccion_area.bind("<<ComboboxSelected>>", solicitar_salario)

        def guardar():
            nombre = entry_nombre.get()
            telefono = entry_telefono.get()
            try:
                if len(telefono) != 8:
                    messagebox.showerror("Error", "El número de telefono debe ser de 8 dígitos")
                    return
                telefono = int(telefono)
            except ValueError:
                messagebox.showerror("Error", "Número de teléfono no válido")
                return
            area = seleccion_area.get()

            if not nombre or not area:
                messagebox.showerror("Error", "Complete todos los campos.")
                return
            agregar_empleado = Empleados(nombre, telefono, area)
            agregar_empleado.guardar()
            try:
                if area.lower() == "corte" or area.lower() == "empacar":
                    salario = float(entry_salario.get())
                    agregar_salario = Salarios(agregar_empleado.obtener_id(), salario)
                    agregar_salario.agregar_salario()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
            messagebox.showinfo("Éxito", f"{nombre} Registrado correctamente")

        frame_btns = tk.Frame(frame, bg='white')
        frame_btns.pack(side='bottom', fill='x', pady=20)

        tk.Button(frame_btns, text="Guardar", bg="#FF8C00", fg="white",
                  font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                  command=guardar).pack(side='left', expand=True, fill='x', padx=5, ipady=8)

        tk.Button(frame_btns, text="Regresar", bg="#0078D7", fg="white",
                  font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                  command=self.gestion_empleados).pack(side='left', expand=True, fill='x', padx=5, ipady=8)

    def listar_empleados(self):
        self.limpiar_contenedor()
        self.crear_cabecera_submenu("Lista de empleados")

        try:
            lista_emp = Empleados.listar()

            frame = tk.Frame(self.contenedor, bg='white')
            frame.pack(pady=20, padx=20, fill='both', expand=True)

            columnas = ("ID", "Nombre", "Teléfono", "Área", "Salario por hora", "")
            filas = ttk.Treeview(frame, columns=columnas, show="headings", height=12)

            for col in columnas:
                filas.heading(col, text=col)

            filas.column("ID", width=60, anchor="center")
            filas.column("Nombre", width=150)
            filas.column("Teléfono", width=100, anchor='center')
            filas.column("Área", width=100, anchor='center')
            filas.column("Salario por hora", width=120, anchor='center')
            filas.column("", width=100, anchor='center')

            for emp in lista_emp:
                if emp['id'] != 1:
                    if emp['area'].lower() in ['corte', 'empacar']:
                        salario = f"{Salarios.mostrar_salario(emp['id']):.2f}"
                    else:
                        salario = "Por pieza"

                    filas.insert('', 'end', values=(
                        emp['id'], emp['nombre'], emp['telefono'], emp['area'], salario, "Modificar"
                    ))

            filas.pack(fill='both', expand=True)

            scroll_y = ttk.Scrollbar(frame, orient="vertical", command=filas.yview)
            scroll_y.pack(side='right', fill='y')
            filas.configure(yscrollcommand=scroll_y.set)

            scroll_x = ttk.Scrollbar(frame, orient="horizontal", command=filas.xview)
            scroll_x.pack(side='bottom', fill='x')
            filas.configure(xscrollcommand=scroll_x.set)

            def al_hacer_click(event):
                item = filas.identify_row(event.y)
                columna = filas.identify_column(event.x)
                if not item or columna != '#6':
                    return
                valores = filas.item(item, "values")
                id_emp = valores[0]
                self.mostrar_ventana_modificar(id_emp)

            filas.bind("<Button-1>", al_hacer_click)

            self.crear_footer_volver(self.gestion_empleados)

        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def mostrar_ventana_modificar(self, id_empleado):
        self.limpiar_contenedor()
        self.crear_cabecera_submenu("Modificar empleado")

        emp = Empleados.consultar(id_empleado)

        if not emp:
            messagebox.showerror("Error", "Empleado no encontrado")
            return

        frame = tk.Frame(self.contenedor, bg='white')
        frame.pack(padx=40, pady=30, fill='both', expand=True)

        tk.Label(frame, text="Nombre:", bg='white').pack(anchor='w')
        entry_nombre = tk.Entry(frame, font=("Arial", 10))
        entry_nombre.pack(fill='x', ipady=8, pady=(0, 10))
        entry_nombre.insert(0, emp['nombre'])

        tk.Label(frame, text="Teléfono:", bg='white').pack(anchor='w')
        entry_telefono = tk.Entry(frame, font=("Arial", 10))
        entry_telefono.pack(fill='x', ipady=8, pady=(0, 10))
        entry_telefono.insert(0, emp['telefono'])

        tk.Label(frame, text="Área:", bg='white').pack(anchor='w')
        combo_area = ttk.Combobox(frame, values=["Corte", "Empacar", "Costura"], state="readonly")
        combo_area.pack(fill='x', ipady=8, pady=(0, 10))
        combo_area.set(emp['area'])

        label_salario = tk.Label(frame, text="Salario por hora:", bg='white')
        entry_salario = tk.Entry(frame, font=("Arial", 10))

        salario_actual = Salarios.mostrar_salario(id_empleado)
        if emp['area'].lower() in ['corte', 'empacar']:
            label_salario.pack(anchor='w', pady=(10, 2))
            entry_salario.pack(fill='x', ipady=8, pady=(0, 10))
            entry_salario.insert(0, salario_actual)

        def actualizar_campos(event):
            area_sel = combo_area.get().lower()
            if area_sel in ['corte', 'empacar']:
                label_salario.pack(anchor='w', pady=(10, 2))
                entry_salario.pack(fill='x', ipady=8, pady=(0, 10))
            else:
                label_salario.pack_forget()
                entry_salario.pack_forget()

        combo_area.bind("<<ComboboxSelected>>", actualizar_campos)

        def guardar_cambios():
            nombre = entry_nombre.get().strip()
            telefono = entry_telefono.get().strip()
            area = combo_area.get()

            if not nombre or not telefono or not area:
                messagebox.showerror("Error", "Complete todos los campos")
                return

            try:
                if len(telefono) != 8:
                    messagebox.showerror("Error", "El número de teléfono debe ser de 8 dígitos")
                    return
                telefono = int(telefono)
            except ValueError:
                messagebox.showerror("Error", "Número de teléfono no válido")
                return

            try:
                Empleados.modificar(id_empleado, nombre, telefono, area)

                if area.lower() in ['corte', 'empacar']:
                    salario = entry_salario.get().strip()
                    if not salario:
                        messagebox.showerror("Error", "Ingrese un salario válido")
                        return
                    try:
                        salario = float(salario)
                    except ValueError:
                        messagebox.showerror("Error", "El salario debe ser numérico")
                        return
                    Salarios.modificar_salario(id_empleado, salario)
                else:
                    Salarios.eliminar(id_empleado)

                messagebox.showinfo("Éxito", "Empleado actualizado correctamente")
                self.gestion_empleados()

            except Exception as e:
                messagebox.showerror("Error", str(e))

        frame_botones = tk.Frame(frame, bg='white')
        frame_botones.pack(fill='x', pady=10)

        tk.Button(frame_botones, text="Guardar cambios", bg="#0078D7", fg="white",
                  font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                  command=guardar_cambios).pack(side='left', expand=True, fill='x', padx=5, ipady=8)

        tk.Button(frame_botones, text="Cancelar", bg="#FF8C00", fg="white",
                  font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                  command=self.listar_empleados).pack(side='left', expand=True, fill='x', padx=5, ipady=8)

    def despedir_empleado(self):
        self.limpiar_contenedor()
        self.crear_cabecera_submenu("Despedir empleado")

        try:
            lista_emp = Empleados.listar()

            frame = tk.Frame(self.contenedor, bg='white')
            frame.pack(pady=20, padx=40, fill='both', expand=True)

            tk.Label(frame, text="Seleccione un empleado:", font=("Arial", 10),
                     bg='white', fg='gray').pack(anchor='w', pady=(10, 2))
            nombres = [f"{e['id']} - {e['nombre']}" for e in lista_emp if e['id'] != 1]

            seleccion_empleado = ttk.Combobox(frame, values=nombres, state="readonly", font=("Arial", 10))
            seleccion_empleado.pack(fill='x', ipady=8, pady=(5, 20))

            def despedir():
                seleccion = seleccion_empleado.get()
                if not seleccion:
                    messagebox.showerror("Error", "Seleccione un empleado")
                    return

                id_emp = seleccion.split(" - ")[0]
                Empleados.eliminar(id_emp)
                Salarios.eliminar(id_emp)

            frame_btns = tk.Frame(frame, bg='white')
            frame_btns.pack(side='bottom', fill='x', pady=20)

            tk.Button(frame_btns, text="Despedir", bg="#FF8C00", fg="white",
                      font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                      command=despedir).pack(side='left', expand=True, fill='x', padx=5, ipady=8)

            tk.Button(frame_btns, text="Cancelar", bg="#0078D7", fg="white",
                      font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                      command=self.gestion_empleados).pack(side='left', expand=True, fill='x', padx=5, ipady=8)

        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def pagar(self):
        pass

    #=====GESTIÓN PEDIDOS=====
    def registrar_corte(self):
        self.limpiar_contenedor()
        self.crear_cabecera_submenu("✂️ Registrar nuevo corte")

        frame = tk.Frame(self.contenedor, bg='white')
        frame.pack(padx=40, pady=20, fill='both', expand=True)

        marcas = ['Pepe', 'Jhon Mike', 'Wrangler', "Levi's", "Lee"]
        tk.Label(frame, text="Marca:", font=("Arial", 10), bg='white', fg='gray').pack(anchor='w', pady=(10, 2))
        seleccion_marca = ttk.Combobox(frame, values=marcas, state="readonly", font=("Arial", 10))
        seleccion_marca.pack(fill='x', ipady=8, pady=(5, 15))

        categorias = ['Dama', 'Niño', 'Juvenil', 'Caballero']
        tk.Label(frame, text="Categoría:", font=("Arial", 10), bg='white', fg='gray').pack(anchor='w', pady=(10, 2))
        seleccion_categoria = ttk.Combobox(frame, values=categorias, state="readonly", font=("Arial", 10))
        seleccion_categoria.pack(fill='x', ipady=8, pady=(5, 15))

        tk.Label(frame, text="Color:", font=("Arial", 10), bg='white', fg='gray').pack(anchor='w', pady=(10, 2))
        entry_color = tk.Entry(frame, font=("Arial", 10), relief='solid', bd=1)
        entry_color.pack(fill='x', ipady=8, pady=(5, 15))

        tallas_elegidas = {}

        def seleccionar_tallas():
            top = tk.Toplevel(self.contenedor)
            top.title("Seleccionar tallas")
            top.geometry("380x420")
            top.config(bg='white')
            top.grab_set()

            tk.Label(top, text="Selecciona las tallas disponibles:",
                     bg='white', font=("Arial", 11, "bold"), fg='gray').pack(pady=10)

            tallas_validas = [0, 2, 4, 6, 8, 10, 12, 14, 16,
                              28, 30, 32, 34, 36, 38, 40, 42, 44]

            frame_tallas = tk.Frame(top, bg='white')
            frame_tallas.pack(padx=20, pady=10)

            seleccion = {}
            columnas = 4

            for i, t in enumerate(tallas_validas):
                fila = i // columnas
                columna = i % columnas
                var = tk.BooleanVar()
                chk = tk.Checkbutton(frame_tallas, text=f"Talla {t}", variable=var,
                                     bg='white', activebackground='white')
                chk.grid(row=fila, column=columna, sticky='w', padx=10, pady=5)
                seleccion[t] = var

            def confirmar():
                seleccionadas = [t for t, v in seleccion.items() if v.get()]
                if not seleccionadas:
                    messagebox.showwarning("Obligatorio", "Selecciona al menos una talla.")
                    return
                top.destroy()

                for widget in frame.pack_slaves():
                    if isinstance(widget, tk.LabelFrame):
                        widget.destroy()

                lf = tk.LabelFrame(frame, text="Cantidades por talla", bg="white",
                                   font=("Arial", 10, "bold"), fg='gray')
                lf.pack(fill='both', expand=True, pady=10, ipady=10, ipadx=5)

                canvas = tk.Canvas(lf, bg='white', highlightthickness=0, height=250)  # ← altura mayor
                scrollbar = tk.Scrollbar(lf, orient="vertical", command=canvas.yview)
                scrollable_frame = tk.Frame(canvas, bg='white')

                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                )

                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)

                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")

                for t in seleccionadas:
                    f = tk.Frame(scrollable_frame, bg="white")
                    f.pack(fill='x', pady=3)
                    tk.Label(f, text=f"Talla {t}:", width=10, bg="white", fg='gray').pack(side='left', padx=10)
                    e = tk.Entry(f, width=12, font=("Arial", 10), relief='solid', bd=1)
                    e.pack(side='left', padx=5)
                    tallas_elegidas[t] = e

            tk.Button(top, text="Confirmar", bg="#0078D7", fg="white",
                      font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                      command=confirmar).pack(pady=10, fill='x', padx=20, ipady=6)

        btn_agregar_tallas = tk.Button(frame, text="➕ Agregar tallas", bg="#0078D7", fg="white",
                                       font=("Arial", 9, "bold"), relief='flat', cursor="hand2",
                                       padx=10, pady=5, command=seleccionar_tallas)
        btn_agregar_tallas.pack(anchor='w', pady=(5, 10))

        def guardar_corte():
            marca = seleccion_marca.get().strip()
            categoria = seleccion_categoria.get().strip()
            color = entry_color.get().strip()

            if not (marca and categoria and color):
                messagebox.showwarning("Campos vacíos", "Completa todos los campos.")
                return

            if not tallas_elegidas:
                messagebox.showwarning("Tallas", "Debes agregar tallas antes de guardar.")
                return

            pedido = Pedidos(marca, categoria, color)
            id_pedido = pedido.guardar()

            for talla, entry in tallas_elegidas.items():
                try:
                    cantidad = int(entry.get())
                except:
                    cantidad = 0
                if cantidad > 0:
                    TallasCorte(id_pedido, talla, cantidad).agregar_talla()
            pedido.actualizar_total(id_pedido)

            messagebox.showinfo("Éxito", "Corte registrado correctamente.")
            self.gestion_pedidos()

        frame_btns = tk.Frame(frame, bg='white')
        frame_btns.pack(side='bottom', fill='x', pady=20)

        tk.Button(frame_btns, text="Guardar", bg="#FF8C00", fg="white",
                  font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                  command=guardar_corte).pack(side='left', expand=True, fill='x', padx=5, ipady=8)

        tk.Button(frame_btns, text="Regresar", bg="#0078D7", fg="white",
                  font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                  command=self.gestion_pedidos).pack(side='left', expand=True, fill='x', padx=5, ipady=8)

    def agregar_bandos(self):
        self.limpiar_contenedor()
        self.crear_cabecera_submenu("➕ Agregar Bandos")

        frame = tk.Frame(self.contenedor, bg='white')
        frame.pack(padx=40, pady=20, fill='both', expand=True)

        try:
            cortes = [f"{c['id']} - {c['marca']} - {c['categoria']}" for c in Pedidos.listar()]
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        tk.Label(frame, text="Seleccione el corte:", font=("Arial", 10), bg='white', fg='gray').pack(anchor='w',
                                                                                                     pady=(10, 2))
        seleccion_corte = ttk.Combobox(frame, values=cortes, state="readonly", font=("Arial", 10))
        seleccion_corte.pack(fill='x', ipady=8, pady=(5, 15))

        bandos_elegidos = {}

        def seleccionar_bandos():
            corte_sel = seleccion_corte.get().strip()
            if not corte_sel:
                messagebox.showwarning("Seleccionar corte", "Debes seleccionar un corte antes de continuar.")
                return

            id_corte = corte_sel.split(" - ")[0]

            try:
                tallas_disp = TallasCorte.obtener_tallas_corte(id_corte)
            except ValueError as e:
                messagebox.showwarning("Sin tallas", str(e))
                return

            bandos_existentes = Bandos.obtener_num_bandos_corte(id_corte)
            disponibles = [i for i in range(1, 100) if i not in bandos_existentes]

            if not disponibles:
                messagebox.showinfo("Sin bandos", "Ya se registraron todos los bandos para este corte.")
                return

            top = tk.Toplevel(self.contenedor)
            top.title("Seleccionar bandos")
            top.geometry("450x500")
            top.config(bg='white')
            top.grab_set()

            tk.Label(top, text="Selecciona los bandos a agregar:",
                     bg='white', font=("Arial", 11, "bold"), fg='gray').pack(pady=10)

            contenedor_scroll = tk.Frame(top, bg='white')
            contenedor_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

            canvas = tk.Canvas(contenedor_scroll, bg='white', highlightthickness=0)
            scrollbar = tk.Scrollbar(contenedor_scroll, orient="vertical", command=canvas.yview)
            frame_bandos = tk.Frame(canvas, bg='white')

            frame_bandos.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=frame_bandos, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            seleccion = {}
            columnas = 8
            for i, bando_num in enumerate(disponibles):
                fila = i // columnas
                columna = i % columnas
                var = tk.BooleanVar()
                chk = tk.Checkbutton(frame_bandos, text=str(bando_num), variable=var, bg='white',
                                     activebackground='white')
                chk.grid(row=fila, column=columna, padx=5, pady=3, sticky='w')
                seleccion[bando_num] = var

            def confirmar_bandos():
                seleccionados = [b for b, v in seleccion.items() if v.get()]
                if not seleccionados:
                    messagebox.showwarning("Obligatorio", "Selecciona al menos un bando.")
                    return
                top.destroy()

                for widget in frame.pack_slaves():
                    if isinstance(widget, tk.LabelFrame):
                        widget.destroy()

                lf = tk.LabelFrame(frame, text="Agregar tallas y cantidades por bando", bg="white",
                                   font=("Arial", 10, "bold"), fg='gray')
                lf.pack(fill='both', expand=True, pady=10, ipady=10, ipadx=5)

                canvas2 = tk.Canvas(lf, bg='white', highlightthickness=0, height=300)
                scrollbar2 = tk.Scrollbar(lf, orient="vertical", command=canvas2.yview)
                scrollable_frame = tk.Frame(canvas2, bg='white')

                scrollable_frame.bind("<Configure>", lambda e: canvas2.configure(scrollregion=canvas2.bbox("all")))
                canvas2.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas2.configure(yscrollcommand=scrollbar2.set)
                canvas2.pack(side="left", fill="both", expand=True)
                scrollbar2.pack(side="right", fill="y")

                for bando in seleccionados:
                    f = tk.Frame(scrollable_frame, bg="white")
                    f.pack(fill='x', pady=4)

                    tk.Label(f, text=f"Bando {bando}:", width=10, bg="white", fg='gray').pack(side='left', padx=10)
                    combo_talla = ttk.Combobox(f, values=tallas_disp, state="readonly", width=10, font=("Arial", 10))
                    combo_talla.pack(side='left', padx=5)

                    entry_cant = tk.Entry(f, width=8, font=("Arial", 10), relief='solid', bd=1)
                    entry_cant.pack(side='left', padx=5)
                    entry_cant.insert(0, "0")

                    bandos_elegidos[bando] = {"talla": combo_talla, "cantidad": entry_cant, "corte": id_corte}

            tk.Button(top, text="Confirmar selección", bg="#0078D7", fg="white",
                      font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                      command=confirmar_bandos).pack(pady=10, fill='x', padx=20, ipady=6)

        btn_agregar_bandos = tk.Button(frame, text="➕ Seleccionar bandos", bg="#0078D7", fg="white",
                                       font=("Arial", 9, "bold"), relief='flat', cursor="hand2",
                                       padx=10, pady=5, command=seleccionar_bandos)
        btn_agregar_bandos.pack(anchor='w', pady=(5, 10))

        def guardar_bandos():
            if not bandos_elegidos:
                messagebox.showwarning("Sin bandos", "Debes seleccionar y llenar los bandos antes de guardar.")
                return

            resumen = []
            try:
                for bando, datos in bandos_elegidos.items():
                    talla = datos["talla"].get()
                    try:
                        cantidad = int(datos["cantidad"].get())
                    except ValueError:
                        cantidad = 0

                    if not talla or cantidad <= 0:
                        raise ValueError(f"Bando {bando}: Debes indicar una talla y una cantidad válida.")

                    nuevo_bando = Bandos(datos["corte"], talla, cantidad)
                    nuevo_bando.agregar_bando()

                    resumen.append(f"Bando {bando} → Talla {talla}: {cantidad} unidades")

                messagebox.showinfo("Éxito", "Se agregaron los siguientes bandos:\n\n" + "\n".join(resumen))
                self.gestion_pedidos()

            except Exception as e:
                messagebox.showerror("Error", f"No se completó el registro:\n{e}")

        frame_btns = tk.Frame(frame, bg='white')
        frame_btns.pack(side='bottom', fill='x', pady=20)

        tk.Button(frame_btns, text="Guardar", bg="#FF8C00", fg="white",
                  font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                  command=guardar_bandos).pack(side='left', expand=True, fill='x', padx=5, ipady=8)

        tk.Button(frame_btns, text="Regresar", bg="#0078D7", fg="white",
                  font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                  command=self.gestion_pedidos).pack(side='left', expand=True, fill='x', padx=5, ipady=8)

    def listar_pedidos(self):
        self.limpiar_contenedor()
        self.crear_cabecera_submenu("📋 Cortes en proceso")

        frame = tk.Frame(self.contenedor, bg='white')
        frame.pack(fill='both', expand=True, padx=30, pady=20)

        tk.Label(frame, text="Mostrar por:", bg='white', fg='gray', font=("Arial", 10, "bold")).pack(anchor='w')
        seleccion_filtro = ttk.Combobox(frame, values=["Tallas", "Bandos"], state="readonly", font=("Arial", 10))
        seleccion_filtro.current(0)
        seleccion_filtro.pack(fill='x', pady=(0, 10), ipady=6)

        contenedor_tabla = tk.Frame(frame, bg='white')
        contenedor_tabla.pack(fill='both', expand=True, pady=10)

        canvas = tk.Canvas(contenedor_tabla, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(contenedor_tabla, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg='white')

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def mostrar_pedidos():
            for widget in scroll_frame.winfo_children():
                widget.destroy()

            try:
                pedidos = Pedidos.listar()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
                self.gestion_pedidos()
                return

            filtro = seleccion_filtro.get().lower()

            if not pedidos:
                tk.Label(scroll_frame, text="No hay cortes en proceso.", bg='white', fg='gray').pack(pady=20)
                return

            for pedido in pedidos:
                id_corte, marca, categoria, color = pedido[0], pedido[1], pedido[2], pedido[3]

                lf = tk.LabelFrame(scroll_frame, text=f"Corte {id_corte} - {marca} ({categoria}) - {color}",
                                   font=("Arial", 10, "bold"), bg='white', fg='gray')
                lf.pack(fill='x', padx=10, pady=8, ipadx=10, ipady=5)

                encabezado = tk.Frame(lf, bg="#F0F0F0")
                encabezado.pack(fill='x', pady=(0, 5))
                if filtro == "tallas":
                    columnas = ["Talla", "Cantidad"]
                else:
                    columnas = ["Bando", "Talla", "Cantidad"]

                for c in columnas:
                    tk.Label(encabezado, text=c, bg="#F0F0F0", font=("Arial", 9, "bold"), width=15).pack(side='left')

                if filtro == "tallas":
                    tallas = TallasCorte.obtener_tallas_cantidades(id_corte)
                    total_tallas = 0
                    for t, cant in tallas.items():
                        fila = tk.Frame(lf, bg='white')
                        fila.pack(fill='x')
                        tk.Label(fila, text=t, width=15, bg='white').pack(side='left')
                        tk.Label(fila, text=cant, width=15, bg='white').pack(side='left')
                        total_tallas += cant

                    tk.Label(lf, text=f"Cantidad total: {total_tallas}", bg='white',
                             fg='black', font=("Arial", 9, "bold")).pack(anchor='e', pady=(5, 0))

                else:
                    bandos = Bandos.obtener_bandos_corte(id_corte)
                    total_bandos = 0
                    contador_bando = 1
                    for b in bandos:
                        f = tk.Frame(lf, bg='white')
                        f.pack(fill='x')
                        tk.Label(f, text=f"Bando {contador_bando}", width=15, bg='white').pack(side='left')
                        tk.Label(f, text=b["talla"], width=15, bg='white').pack(side='left')
                        tk.Label(f, text=b["cantidad"], width=15, bg='white').pack(side='left')
                        total_bandos += b["cantidad"]
                        contador_bando += 1

                    tallas = TallasCorte.obtener_tallas_cantidades(id_corte)

                    faltantes_por_talla = {}
                    for t, cant_talla in tallas.items():
                        cantidad_bandos_talla = sum(b["cantidad"] for b in bandos if b["talla"] == t)
                        if cantidad_bandos_talla < cant_talla:
                            faltantes_por_talla[t] = cant_talla - cantidad_bandos_talla

                    frame_total = tk.Frame(lf, bg='white')
                    frame_total.pack(fill='x', pady=(5, 0))

                    tk.Label(frame_total, text=f"cantridad total: {total_bandos}",
                             bg='white', fg='black', font=("Arial", 9, "bold")).pack(side='left', padx=(10, 0))

                    if faltantes_por_talla:
                        detalles = ", ".join([f"Talla {t} ({f})" for t, f in faltantes_por_talla.items()])
                        tk.Label(frame_total,
                                 text=f"⚠Faltan: {detalles}",
                                 bg='white', fg='red', font=("Arial", 9, "bold"),
                                 wraplength=400, justify='left').pack(side='left', padx=10)

        mostrar_pedidos()
        seleccion_filtro.bind("<<ComboboxSelected>>", lambda e: mostrar_pedidos())

        self.crear_footer_volver(self.gestion_pedidos)

    def entregar_pedido(self):
        self.limpiar_contenedor()
        self.crear_cabecera_submenu("🚚 Entregar Pedido")

        frame = tk.Frame(self.contenedor, bg='white')
        frame.pack(padx=40, pady=30, fill='both', expand=True)

        # --- Label y ComboBox para seleccionar corte ---
        tk.Label(frame, text="Seleccionar corte:", font=("Arial", 10), bg='white', fg='gray').pack(anchor='w',
                                                                                                   pady=(10, 2))

        pedidos = Pedidos.listar()
        if not pedidos:
            tk.Label(frame, text="No hay cortes registrados.", bg='white', fg='gray').pack(pady=20)
            self.crear_footer_volver(self.gestion_pedidos)
            return

        lista_cortes = [f"Corte {p[0]} - {p[1]} - {p[2]} - {p[3]}" for p in pedidos]
        seleccion_corte = ttk.Combobox(frame, values=lista_cortes, state='readonly', font=("Arial", 10))
        seleccion_corte.pack(fill='x', ipady=8, pady=(5, 15))

        lbl_estado = tk.Label(frame, text="", bg='white', fg='gray', font=("Arial", 10))
        lbl_estado.pack(anchor='w', pady=(5, 20))

        def actualizar_estado(event=None):
            valor = seleccion_corte.get()
            if not valor:
                lbl_estado.config(text="")
                return
            id_corte = int(valor.split()[1])
            pedido = Pedidos.buscar(id_corte)
            if pedido:
                lbl_estado.config(text=f"Estado actual: {pedido['estado']}")
            else:
                lbl_estado.config(text="Estado no disponible.")

        seleccion_corte.bind("<<ComboboxSelected>>", actualizar_estado)

        def entregar():
            valor = seleccion_corte.get()
            if not valor:
                messagebox.showwarning("Seleccionar corte", "Seleccione un corte para entregar.")
                return
            id_corte = int(valor.split()[1])
            pedido = Pedidos.buscar(id_corte)
            if not pedido:
                messagebox.showerror("Error", "No se encontró el corte seleccionado.")
                return

            if pedido['estado'] == 'entregado':
                messagebox.showinfo("Información", "Este pedido ya fue entregado.")
                return

            Pedidos.actualizar_estado(id_corte, "entregado")
            messagebox.showinfo("Éxito", f"Corte {id_corte} entregado correctamente.")
            self.entregar_pedido()

        frame_btns = tk.Frame(frame, bg='white')
        frame_btns.pack(side='bottom', fill='x', pady=20)

        tk.Button(frame_btns, text="Entregar", bg="#FF8C00", fg="white",
                  font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                  command=entregar).pack(side='left', expand=True, fill='x', padx=5, ipady=8)

        tk.Button(frame_btns, text="Regresar", bg="#0078D7", fg="white",
                  font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                  command=self.gestion_pedidos).pack(side='left', expand=True, fill='x', padx=5, ipady=8)

    #====GESTIÓN OPERACIONES====
    def registrar_operacion(self):
        self.limpiar_contenedor()
        self.crear_cabecera_submenu("🧮 Registrar Operación")

        frame = tk.Frame(self.contenedor, bg='white')
        frame.pack(padx=40, pady=30, fill='both', expand=True)

        tk.Label(frame, text="Nombre de la operación:", bg='white', fg='gray', anchor='w', font=("Arial", 10)).pack(
            fill='x', pady=(5, 2))
        entry_nombre = tk.Entry(frame, font=("Arial", 10))
        entry_nombre.pack(fill='x', ipady=8, pady=(0, 10))

        tk.Label(frame, text="Precio talla pequeña:", bg='white', fg='gray', anchor='w', font=("Arial", 10)).pack(
            fill='x', pady=(5, 2))
        entry_small = tk.Entry(frame, font=("Arial", 10))
        entry_small.pack(fill='x', ipady=8, pady=(0, 10))

        tk.Label(frame, text="Precio talla grande:", bg='white', fg='gray', anchor='w', font=("Arial", 10)).pack(
            fill='x', pady=(5, 2))
        entry_big = tk.Entry(frame, font=("Arial", 10))
        entry_big.pack(fill='x', ipady=8, pady=(0, 20))

        def guardar_operacion():
            nombre = entry_nombre.get().strip()
            small = entry_small.get().strip()
            big = entry_big.get().strip()

            if not nombre or not small or not big:
                messagebox.showwarning("Campos incompletos", "Por favor complete todos los campos.")
                return

            try:
                small_price = float(small)
                big_price = float(big)
            except ValueError:
                messagebox.showerror("Error", "Los precios deben ser números.")
                return

            nueva_op = Operaciones(nombre, small_price, big_price)
            nueva_op.guardar()
            messagebox.showinfo("Éxito", f"Operación '{nombre}' registrada correctamente.")
            entry_nombre.delete(0, tk.END)
            entry_small.delete(0, tk.END)
            entry_big.delete(0, tk.END)

        frame_btns = tk.Frame(frame, bg='white')
        frame_btns.pack(side='bottom', fill='x', pady=20)

        tk.Button(frame_btns, text="Guardar", bg="#FF8C00", fg="white",
                  font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                  command=guardar_operacion).pack(side='left', expand=True, fill='x', padx=5, ipady=8)

        tk.Button(frame_btns, text="Regresar", bg="#0078D7", fg="white",
                  font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                  command=self.gestion_operaciones).pack(side='left', expand=True, fill='x', padx=5, ipady=8)

    def consultar_operacion(self):
        self.limpiar_contenedor()
        self.crear_cabecera_submenu("🔍 Consultar Operaciones")

        frame = tk.Frame(self.contenedor, bg='white')
        frame.pack(padx=30, pady=20, fill='both', expand=True)

        try:
            operaciones = Operaciones.listar()
        except ValueError as e:
            messagebox.showwarning("Sin registros", str(e))
            self.gestion_operaciones()
            return

        tk.Label(frame, text="Seleccionar operación:", bg='white', fg='gray', font=("Arial", 10, "bold")).pack(
            anchor='w')
        opciones = ["Mostrar todo"] + [op[1] for op in operaciones]
        seleccion = ttk.Combobox(frame, values=opciones, state="readonly", font=("Arial", 10))
        seleccion.current(0)
        seleccion.pack(fill='x', pady=(0, 15), ipady=5)

        contenedor_scroll = tk.Frame(frame, bg='white')
        contenedor_scroll.pack(fill='both', expand=True)

        canvas = tk.Canvas(contenedor_scroll, bg='white', highlightthickness=0)
        canvas.pack(side='left', fill='both', expand=True)

        scroll_y = tk.Scrollbar(contenedor_scroll, orient='vertical', command=canvas.yview)
        scroll_y.pack(side='right', fill='y')

        scroll_x = tk.Scrollbar(frame, orient='horizontal', command=canvas.xview)
        scroll_x.pack(fill='x')

        canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        contenedor_tabla = tk.Frame(canvas, bg='white')
        canvas.create_window((0, 0), window=contenedor_tabla, anchor='nw')

        def mostrar_resultados():
            for w in contenedor_tabla.winfo_children():
                w.destroy()

            try:
                operaciones = Operaciones.listar()
            except ValueError as e:
                messagebox.showwarning("Sin registros", str(e))
                self.gestion_operaciones()
                return

            filtro = seleccion.get()
            if filtro == "Mostrar todo":
                datos = operaciones
            else:
                datos = [op for op in operaciones if op[1] == filtro]

            encabezado = tk.Frame(contenedor_tabla, bg="#E9ECEF")
            encabezado.pack(fill='x', pady=(0, 5))

            columnas = ["ID", "Nombre", "Precio Pequeña", "Precio Grande", "Acciones"]
            anchos = [8, 25, 18, 18, 25]

            for c, w in zip(columnas, anchos):
                tk.Label(encabezado, text=c, font=("Arial", 9, "bold"), bg="#E9ECEF",
                         width=w, anchor='center').pack(side='left', padx=1)

            for op in datos:
                fila = tk.Frame(contenedor_tabla, bg='white')
                fila.pack(fill='x', pady=1)

                tk.Label(fila, text=op[0], width=anchos[0], bg='white', anchor='center').pack(side='left', padx=1)
                tk.Label(fila, text=op[1], width=anchos[1], bg='white', anchor='w').pack(side='left', padx=1)
                tk.Label(fila, text=f"Q{op[2]:.3f}", width=anchos[2], bg='white', anchor='e').pack(side='left', padx=1)
                tk.Label(fila, text=f"Q{op[3]:.3f}", width=anchos[3], bg='white', anchor='e').pack(side='left', padx=1)

                acciones = tk.Frame(fila, bg='white')
                acciones.pack(side='left', padx=3)

                tk.Button(acciones, text="✏ Modificar", bg="#FFC107", fg="black", font=("Arial", 9),
                          relief='flat', width=10,
                          command=lambda oid=op[0]: modificar_operacion(oid)).pack(side='left', padx=2)

                tk.Button(acciones, text="🗑 Eliminar", bg="#DC3545", fg="white", font=("Arial", 9),
                          relief='flat', width=10,
                          command=lambda oid=op[0]: eliminar_operacion(oid)).pack(side='left', padx=2)

            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))

        def modificar_operacion(id):
            ventana_modificar = tk.Toplevel(self.contenedor)
            ventana_modificar.title("Modificar Operación")
            ventana_modificar.geometry("300x250")
            ventana_modificar.configure(bg='white')

            operacion = Operaciones.buscar(id)

            tk.Label(ventana_modificar, text="Nombre:", bg='white').pack()
            e_nombre = tk.Entry(ventana_modificar)
            e_nombre.insert(0, operacion[1])
            e_nombre.pack(pady=5)

            tk.Label(ventana_modificar, text="Precio pequeña:", bg='white').pack()
            e_small = tk.Entry(ventana_modificar)
            e_small.insert(0, operacion[2])
            e_small.pack(pady=5)

            tk.Label(ventana_modificar, text="Precio grande:", bg='white').pack()
            e_big = tk.Entry(ventana_modificar)
            e_big.insert(0, operacion[3])
            e_big.pack(pady=5)

            def guardar_cambios():
                v = VentanaConfirmacion(self.contenedor, "¿Seguro que desea modificar esta operación?")
                if not v.resultado:
                    messagebox.showinfo("Cancelado", "La modificación fue cancelada.")
                    return

                nombre = e_nombre.get().strip()
                small = e_small.get().strip()
                big = e_big.get().strip()

                if not nombre or not small or not big:
                    messagebox.showwarning("Error", "Todos los campos son obligatorios.")
                    return

                Operaciones.modificar(id, nombre, small, big)
                ventana_modificar.destroy()
                mostrar_resultados()

            tk.Button(ventana_modificar, text="Guardar cambios", bg="#28A745", fg="white",
                      relief='flat', command=guardar_cambios).pack(pady=15)

        def eliminar_operacion(id):
            v = VentanaConfirmacion(self.contenedor, "¿Seguro que desea eliminar esta operación?")
            if not v.resultado:
                messagebox.showinfo("Cancelado", "La eliminación fue cancelada.")
                return

            try:
                Operaciones.eliminar(id)
                mostrar_resultados()
            except ValueError as e:
                messagebox.showwarning("Error", str(e))

        mostrar_resultados()
        seleccion.bind("<<ComboboxSelected>>", lambda e: mostrar_resultados())

        self.crear_footer_volver(self.gestion_operaciones)

    #===GESTIÓN DE TAREAS===
    def asignar_tareas(self):
        self.limpiar_contenedor()
        self.crear_cabecera_submenu("🧵 Asignar Tarea")

        frame = tk.Frame(self.contenedor, bg='white')
        frame.pack(padx=40, pady=20, fill='both', expand=True)

        tk.Label(frame, text="Completa los datos para asignar la tarea:",
                 bg='white', font=("Arial", 11, "bold"), fg='gray').pack(anchor='w', pady=(0, 5))

        campos = tk.Frame(frame, bg='white')
        campos.pack(fill='x', pady=5)

        tk.Label(campos, text="Empleado:", font=("Arial", 10), bg='white', fg='gray').pack(anchor='w', pady=(10, 2))
        empleados = Empleados.buscar_empleado_costura()
        cb_empleado = ttk.Combobox(campos, values=empleados, state="readonly", font=("Arial", 10))
        cb_empleado.pack(fill='x', ipady=5, pady=(0, 5))

        tk.Label(campos, text="Corte:", font=("Arial", 10), bg='white', fg='gray').pack(anchor='w', pady=(10, 2))
        cortes = [f"{p['id']} - {p['marca']} {p['categoria']}" for p in Pedidos.listar()]
        cb_corte = ttk.Combobox(campos, values=cortes, state="readonly", font=("Arial", 10))
        cb_corte.pack(fill='x', ipady=5, pady=(0, 5))

        tk.Label(campos, text="Operación:", font=("Arial", 10), bg='white', fg='gray').pack(anchor='w', pady=(10, 2))
        operaciones = [f"{o['id']} - {o['nombre']}" for o in Operaciones.listar()]
        cb_oper = ttk.Combobox(campos, values=operaciones, state="readonly", font=("Arial", 10))
        cb_oper.pack(fill='x', ipady=5, pady=(0, 5))

        tk.Label(campos, text="Bandos a realizar:", font=("Arial", 10), bg='white', fg='gray').pack(anchor='w',
                                                                                                    pady=(10, 2))
        cb_bando = ttk.Combobox(campos, state="readonly", font=("Arial", 10))
        cb_bando.pack(fill='x', ipady=5, pady=(0, 5))

        def seleccionar_bando():
            val_corte = cb_corte.get()
            if not val_corte:
                messagebox.showwarning("Atención", "Primero selecciona un corte.")
                return
            corte_id = int(val_corte.split(" - ")[0])
            self.abrir_ventana_bandos(corte_id, cb_bando)

        btn_bandos = tk.Button(frame, text="➕ Seleccionar Bandos",
                               bg="#0078D7", fg="white", font=("Arial", 9, "bold"),
                               relief='flat', cursor="hand2", padx=10, pady=6,
                               command=seleccionar_bando)
        btn_bandos.pack(anchor='w', pady=(10, 20))

        frame_botones = tk.Frame(frame, bg='white')
        frame_botones.pack(side='bottom', fill='x', pady=20)

        def guardar_tarea():
            if not (cb_empleado.get() and cb_corte.get() and cb_oper.get() and cb_bando.get()):
                messagebox.showwarning("Atención", "Completa todos los campos antes de guardar.")
                return

            id_empleado = int(cb_empleado.get().split(" - ")[0])
            id_corte = int(cb_corte.get().split(" - ")[0])
            id_oper = int(cb_oper.get().split(" - ")[0])
            id_bando = cb_bando.get().strip()

            tarea = Tareas(id_empleado, id_corte, id_bando, id_oper)
            tarea.guardar()

            messagebox.showinfo("Éxito", "Tarea asignada correctamente.")
            self.asignar_tareas()

        tk.Button(frame_botones, text="Confirmar",
                  bg="#D2691E", fg="white", font=("Arial", 10, "bold"),
                  relief='flat', cursor="hand2", padx=10, pady=8,
                  command=guardar_tarea).pack(side='left', expand=True, fill='x', padx=5)

        tk.Button(frame_botones, text="Cancelar",
                  bg="#0078D7", fg="white", font=("Arial", 10, "bold"),
                  relief='flat', cursor="hand2", padx=10, pady=8,
                  command=self.gestion_tareas).pack(side='left', expand=True, fill='x', padx=5)

    def abrir_ventana_bandos(self, corte_id, cb_bando):
        ventana = tk.Toplevel(self.root)
        ventana.title("Seleccionar Bandos Disponibles")
        ventana.config(bg="white")

        ventana.update_idletasks()
        w, h = 400, 400
        x = (ventana.winfo_screenwidth() // 2) - (w // 2)
        y = (ventana.winfo_screenheight() // 2) - (h // 2)
        ventana.geometry(f"{w}x{h}+{x}+{y}")
        ventana.resizable(False, False)

        tk.Label(ventana, text="Selecciona los bandos disponibles:", bg="white", font=("Arial", 11, "bold")).pack(
            pady=10)

        frame_lista = tk.Frame(ventana, bg="white")
        frame_lista.pack(fill="both", expand=True)

        try:
            bandos = Bandos.obtener_bandos_corte(corte_id)
        except Exception:
            bandos = []

        vars_bandos = []
        for b in bandos:
            var = tk.BooleanVar()
            chk = tk.Checkbutton(frame_lista, text=f"No.{b['id']} - Cantidad={b['cantidad']} - talla={b['talla']}",
                                 variable=var, bg="white")
            chk.pack(anchor="w", padx=20, pady=2)
            vars_bandos.append((var, b['id']))

        def confirmar_seleccion():
            seleccionados = [str(b_id) for var, b_id in vars_bandos if var.get()]
            if not seleccionados:
                messagebox.showwarning("Atención", "Selecciona al menos un bando.")
                return
            cb_bando.set(", ".join(seleccionados))
            ventana.destroy()

        frame_botones = tk.Frame(ventana, bg="white")
        frame_botones.pack(pady=15)
        tk.Button(frame_botones, text="Confirmar", command=confirmar_seleccion, bg="#d2691e", fg="white").pack(side="left",
                                                                                                          padx=10)
        tk.Button(frame_botones, text="Cancelar", command=ventana.destroy, bg="#007ACC", fg="white").pack(
            side="left", padx=10)

    def marcar_tareas(self):
        pass

    def ver_reportes(self):
        pass

#====MÉTODO PARA EJECUTAR====
    def ejecutar(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = InterfazGrafica()
    app.ejecutar()