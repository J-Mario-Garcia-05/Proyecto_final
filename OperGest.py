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
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        conn.execute('''
        CREATE TABLE IF NOT EXISTS empleados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono INTEGER NOT NULL,
            area TEXT NOT NULL
        )
        ''')
        conn.commit()
        return conn

    def guardar(self):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO empleados (nombre, telefono, area) VALUES (?, ?, ?)",
            (self.nombre, self.telefono, self.area)
        )
        conn.commit()
        conn.close()

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
            messagebox.showerror("Error", "No se encontró a ningpun empleado")
        else:
            return empleado

    def obtener_id(self):
        conn = self._conn()
        cur = conn.cursor()
        cur.execute('SELECT * FROM empleados WHERE nombre = ?', (self.nombre,))
        fila = cur.fetchone()
        conn.close()
        if not fila:
            messagebox.showerror("Error", "No se encontró a ningún empleado")
        else:
            return fila['id']

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
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
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
            cursor.execute("DELETE FROM tareas WHERE id_empleado", (id_empleado,))

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
            return cur['rol']

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
            ("Calcular pago", self.calcular_pago),
            ("Crear cuenta", self.crear_cuenta)
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

    def calcular_pago(self):
        pass

    def ejecutar(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = InterfazGrafica()
    app.ejecutar()