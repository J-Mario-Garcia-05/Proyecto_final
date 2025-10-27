import sqlite3
import datetime
import tkinter as tk
from tkinter import messagebox, ttk


DB_NAME = "registros.db"
conn = sqlite3.connect(DB_NAME)
conn.execute("PRAGMA foreign_keys = ON")


class Pedidos:
    def __init__(self, marca, categoria):
        self.marca = marca
        self.categoria = categoria

    @staticmethod
    def _conn():
        conn.row_factory = sqlite3.Row
        conn.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        marca TEXT NOT NULL,
        categoria TEXT NOT NULL,
        cantidad INTEGER DEFAULT 0)
        ''')
        conn.commit()
        return conn

    def guardar(self):
        conn.execute(
            'INSERT INTO pedidos (marca, categoria) VALUES (?, ?)',
            (self.marca, self.categoria)
        )
        conn.commit()
        return conn

    @staticmethod
    def modifcar(corte):
        with Pedidos._conn() as cursor:
            cur = cursor.execute('SELECT * FROM pedidos WHERE id = ?', (corte,))
            fila = cur.fetchone()
            if not fila:
                raise ValueError("No se encontró el número de corte!")
            marca = input(f"Actualizar marca [{fila['marca']}]: ") or fila['marca']
            categoria = input(f"Actualizar categoria [{fila['categoria']}]: ") or fila['categoria']
            conn.execute(
                """UPDATE pedidos SET marca = ?, categoria = ? WHERE id = ?""",
                (marca, categoria, corte)
            )

class bandos:
    def __init__(self, corte, talla, cantidad):
        self.corte = corte
        self.talla = talla
        self.cantidad = cantidad

    @staticmethod
    def _conn():
        conn.row_factory = sqlite3.Row
        conn.execute('''
        CREATE TABLE IF NOT EXISTS bandos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        corte INTEGER NOT NULL,
        talla INTEGER NOT NULL,
        cantidad INTEGER NOT NULL,
        FOREIGN KEY (corte) REFERENCES pedidos (id))
        ''')
        conn.commit()
        return conn

    def agregar_bando(self):
        conn.execute(
            'INSERT INTO bandos (corte, talla, cantidad) VALUES (?, ?, ?)',
            (self.corte, self.talla, self.cantidad)
        )
        conn.execute(
            """UPDATE pedidos SET cantidad = (SELECT SUM(cantidad) FROM bandos WHERE corte = ?) WHERE id = ?""",
            (self.corte, self.corte))

    @staticmethod
    def modificar(corte):
        with Pedidos._conn() as cursor:
            cur = cursor.execute('SELECT * FROM pedidos WHERE id = ?', (corte,))
            filas = cur.fetchall()
            for i, (fila,) in enumerate(filas,start=1):
                print(f"Bando {i}:")
                talla = input(f"\tActualizar talla [{fila['talla']}]: ") or fila['talla']
                cantidad = input(f"\tActualizar cantidad [{fila['cantidad']}]: ") or fila['cantidad']
                conn.execute(
                    """UPDATE bandos SET talla = ?, cantidad = ? WHERE id = ?""",
                    (talla, cantidad, fila['id'])
                )
            conn.execute(
                """UPDATE pedidos SET cantidad = (SELECT SUM(cantidad) FROM bandos WHERE corte = ?) WHERE id = ?""",
                (corte, corte))


class Operaciones:
    def __init__(self, nombre, small_price, big_price):
        self.nombre = nombre
        self.small_price = small_price
        self.big_price = big_price

    @staticmethod
    def _conn():
        conn.row_factory = sqlite3.Row
        conn.execute('''
        CREATE TABLE IF NOT EXISTS operaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        small_price  REAL NOT NULL,
        big_price  REAL NOT NULL)
        ''')
        conn.commit()
        return conn

    def guardar(self):
        with self._conn() as cursor:
            cursor.execute(
                "INSERT INTO operaciones (nombre, small_price, big_price) VALUES (?, ?, ?)",
                (self.nombre, self.small_price, self.big_price)
            )

    @staticmethod
    def modificar(id):
        with Operaciones._conn() as cursor:
            cur = cursor.execute('SELECT * FROM operaciones WHERE id = ?', (id,))
            fila = cur.fetchone()
            if not fila:
                raise ValueError("No se encontró ninguna operación con ese nombre!")
            nombre = input(f"Actualizar nombre [{fila['nombre']}]: ") or fila['nombre']
            small_price = input(f"Actualizar precio talla pequeña [{fila['small_price']}]: ") or fila['small_price']
            big_price = input(f"Actualziar precio talla grande [{fila['big_price']}]: ") or fila['big_price']
            conn.execute(
                "UPDATE pedidos SET nombre, small_price, big_price = ? WHERE id = ?",
                (nombre, small_price, big_price, id)
            )

    @staticmethod
    def eliminar(id):
        with Operaciones._conn() as cursor:
            cur = cursor.execute('DELETE FROM operaciones WHERE nombre = ?', (id,))
            if cur.rowcount:
                raise ValueError("No se encontró ninguna operación con el nombre ingresado!")


class Empleados:
    def __init__(self, nombre, telefono, area):
        self.nombre = nombre
        self.telefono = telefono
        self.area = area

    @staticmethod
    def _conn():
        conn.row_factory = sqlite3.Row
        conn.execute('''
        CREATE TABLE IF NOT EXISTS empleados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        telefono INTEGER NOT NULL,
        area TEXT NOT NULL)
                     ''')
        conn.commit()
        return conn

    def guardar(self):
        with self._conn() as cursor:
            cursor.execute(
                "INSERT INTO empleados (nombre, telefono, area) VALUES (?, ?, ?)",
                (self.nombre, self.telefono, self.area)
            )

    @staticmethod
    def listar():
        with Empleados._conn() as cursor:
            cur = cursor.execute('SELECT * FROM empleados')
            lista = cur.fetchall()
            if not lista:
                raise ValueError("No hay empleados registrados!")
            print("\n--")

    @staticmethod
    def modificar(id):
        with Empleados._conn() as cursor:
            cur = cursor.execute('SELECT * FROM empleados WHERE id = ?', (id,))
            fila = cur.fetchone()
            if not fila:
                raise ValueError("No se encontró a ningún empleado!")
            nombre = input(f"Actualizar nombre {fila['nombre']}: ") or fila['nombre']
            telefono = int(input(f"Actualizar teléfono {fila['telefono']}: ") or fila['telefono'])
            area = input(f"Actualizar area {fila['area']}: ") or fila['area']
            conn.execute(
                "UPDATE empleados SET nombre, telefono, area = ? WHERE id = ?",
                (nombre, telefono, area, id)
            )

    @staticmethod
    def eliminar(id):
        with Empleados._conn() as cursor:
            cur = cursor.execute('DELETE FROM empleados WHERE id = ?', (id,))
            if cur.rowcount:
                raise ValueError("No se encontró ningún empleado!")

class Tareas:
    def __init__(self, id_empleado, corte, bandos, operacion, fecha):
        self.id_empleado = id_empleado
        self.corte = corte
        self.bandos = bandos
        self.operacion = operacion

    @staticmethod
    def _conn():
        conn.row_factory = sqlite3.Row
        conn.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_empleado INTEGER NOT NULL,
        corte INTEGER NOT NULL,
        bandos INTEGER NOT NULL,
        operacion INTEGER NOT NULL,
        FOREIGN KEY(id_empleado) REFERENCES empleados(id),
        FOREIGN KEY(corte) REFERENCES pedidos(id),
        FOREIGN KEY(bandos) REFERENCES bandos(id),
        FOREIGN KEY(operacion) REFERENCES operaciones(id))
        ''')
        conn.commit()
        return conn

    def guardar(self):
        with self._conn() as cursor:
            cursor.execute(
                "INSERT INTO tareas(id_empleado, corte, bandos, operacion) VALUES (?, ?, ?, ?)",
                (self.id_empleado, self.corte, self.bandos, self.operacion)
            )

    @staticmethod
    def listar(id_empleado):
        with Tareas._conn() as cursor:
            lista = cursor.execute('SELECT * FROM tareas WHERE id_empleado = id_empleado').fetchall()
            if not lista:
                raise ValueError("No se le han asignado tareas aún.")
            print("\n--")

    @staticmethod
    def editar(id_empleado):
        with Tareas._conn() as cursor:
            Tareas.listar(id_empleado)
            fila = cursor.execute("SELECT FROM tareas WHERE id_empleado = ? AND id = ?",
                                  (id_empleado, id)).fetchone()
            id_empleado = input(f"Actualizar id empleado {fila['id_empleado']}: ") or fila['id_empleado']
            corte = input(f"Actualizar corte {fila['corte']}: ") or fila['corte']
            bandos = input(f"Modificar bandos {fila['bandos']}: ") or fila['bandos']
            conn.execute(
                "UPDATE tareas SET id_empleado = ?, corte = ?, bandos = ? WHERE id = ?",
                (id_empleado, corte, bandos, fila['id'])
            )

    @staticmethod
    def eliminar(id_empleado):
        with Tareas._conn() as cursor:
            Tareas.listar(id_empleado)
            cursor.execute("DELETE FROM tareas WHERE id = ? AND id_empleado", (id_empleado, id))

class Reportes:
    def __init__(self, id_tarea):
        self.id_tarea = id_tarea

    @staticmethod
    def __conn():
        conn.row_factory = sqlite3.Row
        conn.execute('''
        CREATE TABLE IF NOT EXISTS reportes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_tarea INTEGER NOT NULL,
        FOREIGN KEY(id_tarea) REFERENCES tareas(id))
                     ''')
        conn.commit()
        return conn

    def guardar(self):
        pass

class Cuentas:
    def __init__(self, id_empleado, usuario, password, rol):
        self.id_empleado = id_empleado
        self.usuario = usuario
        self.password = password
        self.rol = rol

    @staticmethod
    def _conn():
        conn.row_factory = sqlite3.Row
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
            return {cur['rol']}

    @staticmethod
    def eliminar(id_empleado):
        with Cuentas._conn() as cursor:
            cur = cursor.execute("DELETE FROM cuentas WHERE id_empleado = ?", (id_empleado,))

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
                boton_ver.config(text="👁️")
                self.mostrar = False
            else:
                self.entry_password.config(show='')
                boton_ver.config(text="🙈")
                self.mostrar = True

        boton_ver = tk.Button(frame, text="👁️", bg='white', relief='flat', cursor="hand2",
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
                self.tipo_usuario = rol
                self.usuario_actual = usuario
                if self.tipo_usuario == "administrador":
                    self.menu_administrador()
                else:
                    self.menu_administrador()
            except ValueError as e:
                messagebox.showerror("Error", f"Error: {e}")
        else:
            if usuario == "admin" and password == "admin":
                self.abrir_ventana_cambiar()
            else:
                messagebox.showerror("Error", "ERROR: Credenciales incorrectos")

    def abrir_ventana_cambiar(self):
        self.limpiar_contenedor()

        titulo = tk.Label(self.contenedor, text="Crear cuenta",
                          font=("Arial", 16, "bold"), bg='white')
        titulo.pack(pady=40)

        subtitulo = tk.Label(self.contenedor, text="Actualizar datos\nIngrese nuevos datos para actualizar la cuenta",
                             font=("Arial", 9), bg='white', fg='gray')
        subtitulo.pack(pady=10)

        frame = tk.Frame(self.contenedor, bg="white")
        frame.pack(pady=20, padx=50, fill="x")

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
                boton_ver.config(text="👁️")
                self.mostrar = False
            else:
                entry_new_pass.config(show='')
                boton_ver.config(text="🙈")
                self.mostrar = True

        boton_ver = tk.Button(frame, text="👁️", bg='white', relief='flat', cursor="hand2",
                              command=alternar_password)
        boton_ver.pack(anchor='e', pady=(5, 0))

        def guardar_nuevos_datos():
            nuevo_usuario = entry_nuevo_usuario.get().strip()
            new_pass = entry_new_pass.get().strip()

            if nuevo_usuario == "" or new_pass == "":
                messagebox.showwarning("Campos vacíos", "Por favor complete ambos campos.")
                return
            admin = Empleados("admin", 0000, "administrador")
            admin.guardar()
            cuenta = Cuentas(1, nuevo_usuario, new_pass, "administrador")
            cuenta.guardar()
            self.ventana_login()
            messagebox.showinfo("Éxito", "Usuario y contraseña actualizados\nInicie sesión nuevamente")

        boton_guardar = tk.Button(frame, text="Guardar cambios", bg="#0078D7", fg='white',
                                  font=("Arial", 10, "bold"), relief="flat", cursor="hand2",
                                  command=guardar_nuevos_datos)
        boton_guardar.pack(fill="x", pady=(30, 10), ipady=10)

        boton_cancelar = tk.Button(frame, text="Cancelar", bg="#FF8C00", fg='white',
                                   font=("Arial", 10, "bold"), relief="flat", cursor="hand2",
                                   command=self.ventana_login)
        boton_cancelar.pack(fill="x", ipady=10)

    def menu_administrador(self):
        self.limpiar_contenedor()

        cabecera = tk.Frame(self.contenedor, bg ='#0078D7', height=80)
        cabecera.pack(fill='x')
        cabecera.pack_propagate(False)

        tk.Label(cabecera, text=f"Bienvendio: {self.tipo_usuario}",
                 font=("Arial", 14, "bold"), bg='#0078D7', fg='white').pack(pady=25)

        frame_contenido = tk.Frame(self.contenedor, bg='white')
        frame_contenido.pack(fill='both', expand=True, padx=40, pady=30)

        tk.Label(frame_contenido, text="Seleccione una opción",
                 font=("Arial", 12), bg='white', fg='gray').pack(pady=20)

        botones = [
            ("👥 Gestión de Empleados", self.gestion_empleados),
            ("📦 Gestión de Pedidos", self.gestion_pedidos),
            ("⚙️ Gestión de Operaciones", self.gestion_operaciones),
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

    def gestion_empleados(self):
        self.limpiar_contenedor()

        self.crear_cabecera_submenu("👥 Gestión de Empleados")

        frame_contenido = tk.Frame(self.contenedor, bg='white')
        frame_contenido.pack(fill='both', expand=True, padx=40, pady=30)

        botones = [
            ("Registrar empleado", self.registrar_empleado),
            ("Listar empleados", self.listar_empleados),
            ("Despedir empleado", self.despedir_empleado),
            ("Calcular pago", self.calcular_pago_empleado)
        ]

        for texto, comando in botones:
            btn = tk.Button(frame_contenido, text=texto, bg="#0078D7", fg="white",
                            font=("Arial", 11, "bold"), relief='flat', cursor="hand2",
                            command=comando)
            btn.pack(fill='x', pady=8, ipady=12)

        self.crear_footer_volver(self.menu_administrador)

    def gestion_pedidos(self):
        self.limpiar_contenedor()

        self.crear_cabecera_submenu("📦 Gestión de Pedidos")

        frame_contenido = tk.Frame(self.contenedor, bg='white')
        frame_contenido.pack(fill='both', expand=True, padx=40, pady=30)

        botones = [
            ("Registrar operación", self.registrar_operacion),
            ("Listar operaciones", self.listar_operaciones),
            ("Asignar tarea", self.asignar_tarea),
            ("Consultar operación", self.consultar_operacion)
        ]

        for texto, comando in botones:
            btn = tk.Button(frame_contenido, text=texto, bg="#0078D7", fg="white",
                            font=("Arial", 11, "bold"), relief='flat', cursor="hand2",
                            command=comando)
            btn.pack(fill='x', pady=8, ipady=12)

        self.crear_footer_volver(self.menu_administrador)

    def crear_cabecera_submenu(self, titulo):
        cabecera = tk.Frame(self.contenedor, bg='#0078D7', height=80)
        cabecera.pack(fill='x')
        cabecera.pack_propagate(False)

        tk.Label(cabecera, text=titulo,
                 font=("Arial", 10, "bold"), bg='#0078D7', fg='white').pack(pady=25)

    def gestion_operaciones(self):
        self.limpiar_contenedor()

        self.crear_cabecera_submenu("⚙️ Gestión de Operaciones")

        frame_contenido = tk.Frame(self.contenedor, bg='white')
        frame_contenido.pack(fill='both', expand=True, padx=40, pady=30)

        botones = [
            ("Registrar operación", self.registrar_operacion),
            ("Consultar operación", self.listar_operaciones),
            ("Asignar tarea", self.asignar_tarea)
        ]

        for texto, comando in botones:
            boton = tk.Button(frame_contenido, text=texto, bg='#0078D7', fg='white',
                              font=("Arial", 11, "bold"), relief='flat', cursor="hand2",
                              command=comando)
            boton.pack(fill='x', pady=8, ipady=12)

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
            if seleccion_area.get().lower() == "corte" or seleccion_area.get().lower() == "empacar":
                label_salario.pack(anchor='w', pady=(10, 2))
                entry_salario.pack(fill='x', ipady=8, pady=(5, 15))
            else:
                label_salario.pack_forget()
                entry_salario.pack_forget()

        seleccion_area.bind("<<ComboboxSelected>>", solicitar_salario)

        def guardar():
            nombre = entry_nombre.get()
            area = seleccion_area.get()

            if not nombre or not area:
                messagebox.showerror("Error", "Complete todos los campos.")
                return
            try:
                if area.lower() == "corte" or area.lower() == "empacar":
                    salario = float(entry_salario.get())
            except ValueError as e:
                messagebox.showerror("Error", str(e))

        frame_btns = tk.Frame(frame, bg='white')
        frame_btns.pack(side='bottom', fill='x', pady=20)

        tk.Button(frame_btns, text="Guardar", bg="#FF8C00", fg="white",
                  font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                  command=guardar).pack(side='left', expand=True, fill='x', padx=5, ipady=8)

        tk.Button(frame_btns, text="Cancelar", bg="#0078D7", fg="white",
                  font=("Arial", 10, "bold"), relief='flat', cursor="hand2",
                  command=self.gestion_empleados).pack(side='left', expand=True, fill='x', padx=5, ipady=8)

    def ejecutar(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = InterfazGrafica()
    app.ejecutar()