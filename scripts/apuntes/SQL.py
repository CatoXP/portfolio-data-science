import random
from datetime import datetime, timedelta

# Generar INSERT para todas las ventas (50 empleados × 14 días = 700 ventas)
def generar_ventas():
    fecha_inicio = datetime(2024, 11, 4)
    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    
    inserts = []
    
    for num_empleado in range(1, 51):  # 50 empleados
        for dia in range(14):  # 14 días (2 semanas)
            fecha = fecha_inicio + timedelta(days=dia)
            dia_semana = dias_semana[fecha.weekday()]
            
            # Semana 45 o 46
            semana = 45 if dia < 7 else 46
            
            # Ventas aleatorias entre 5000 y 12000
            total_vendido = round(random.uniform(5000, 12000), 2)
            
            insert = f"({num_empleado}, '{fecha.strftime('%Y-%m-%d')}', '{dia_semana}', {total_vendido}, {semana}, 2024)"
            inserts.append(insert)
    
    # Dividir en bloques de 100 para no hacer el INSERT muy largo
    sql_completo = ""
    for i in range(0, len(inserts), 100):
        bloque = inserts[i:i+100]
        sql = "INSERT INTO ventas_diarias (num_empleado, fecha_venta, dia_semana, total_vendido, semana, año) VALUES\n"
        sql += ",\n".join(bloque) + ";\n\n"
        sql_completo += sql
    
    return sql_completo

# Ejecutar generación
ventas_sql = generar_ventas()

# Guardar en archivo
with open('ventas_insert.sql', 'w', encoding='utf-8') as f:
    f.write(ventas_sql)

print("✓ Archivo 'ventas_insert.sql' generado exitosamente")
print(f"✓ Total de inserts: 700 ventas (50 empleados × 14 días)")
print("\nPrimeros 5 inserts de ejemplo:")
print(ventas_sql[:500] + "...")