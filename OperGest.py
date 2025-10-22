import sqlite3

DB_NAME = "registros.db"
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

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

    def guardar(self):
        conn.execute(
            'INSERT INTO pedidos VALUES (?, ?, ?)',
            (self.marca, self.categoria, self.cantidad)
        )
        conn.commit()
        return c.lastrowid

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

    def agregar_bando(self):
        conn.execute(
            'INSERT INTO bandos VALUES (?, ?, ?)',
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
    def __conn():
        conn.row_factory = sqlite3.Row
        conn.execute('''
        CREATE TABLE IF NOT EXISTS operaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        small_price  REAL NOT NULL,
        big_price  REAL NOT NULL)
        ''')
        conn.commit()

    @staticmethod
    def modificar(nombre):
        with Pedidos._conn() as cursor:
            cur = cursor.execute('SELECT * FROM operaciones WHERE nombre = ?', (nombre,))
            fila = cur.fetchone()
            if not fila:
                raise ValueError("No se encontró ninguna operación con ese nombre!")
            nombre = input(f"Actualizar nombre [{fila['nombre']}]: ") or fila['nombre']
            small_price = input(f"Actualizar precio talla pequeña [{fila['small_price']}]: ") or fila['small_price']
            big_price = input(f"Actualziar precio talla grande [{fila['big_price']}]: ") or fila['big_price']
            conn.execute(
                "UPDATE pedidos SET nombre, small_price, big_price = ? WHERE id = ?",
                (nombre, small_price, big_price, fila['id'])
            )

    @staticmethod
    def eliminar(nombre):
        with Pedidos._conn() as cursor:
            cur = cursor.execute('DELETE FROM operaciones WHERE nombre = ?', (nombre,))
            if cur.rowcount:
                raise ValueError("No se encontró ninguna operación con el nombre ingresado!")


class Empleado:
    def __init__(self, nombre, telefono, area):
        self.nombre = nombre
        self.telefono = telefono
        self.area = area

    @staticmethod
    def __conn():
        conn.row_factory = sqlite3.Row
        conn.execute('''
        CREATE TABLE IF NOT EXISTS empleados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        telefono INTEGER NOT NULL,
        area TEXT NOT NULL)
                     ''')

    @staticmethod
    def modificar(id):
        with Pedidos._conn() as cursor:
            cur = cursor.execute('SELECT * FROM empleados WHERE id = ?', (id,))
            fila = cur.fetchone()
            if not fila:
                raise ValueError("No se encontró a ningún empleado!")
            nombre = input(f"Actualizar nombre {fila['nombre']}: ") or fila['nombre']
            telefono = int(input(f"Actualizar teléfono {fila['telefono']}: ") or fila['telefono'])
            area = input(f"Actualizar area {fila['area']}: ") or fila['area']
            conn.execute(
                "UPDATE empleados SET nombre, telefono, area = ? WHERE id = ?",
                (nombre, telefono, fila['id'])
            )
