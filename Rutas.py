import requests
import urllib.parse

route_url = "https://graphhopper.com/api/1/route?"
key = "3afb24aa-4c7b-4fec-8e4b-89f8d63b1d63"  # Reemplaza esto con tu clave API

def geocoding(location, key):
    geocode_url = "https://graphhopper.com/api/1/geocode?"
    url = geocode_url + urllib.parse.urlencode({"q": location, "limit": "1", "key": key})
   
    try:
        replydata = requests.get(url)
        replydata.raise_for_status()  # Verificar si la solicitud fue exitosa
        json_data = replydata.json()

        if 'hits' in json_data and len(json_data['hits']) > 0:
            lat = json_data["hits"][0]["point"]["lat"]
            lng = json_data["hits"][0]["point"]["lng"]
            return 200, lat, lng
        else:
            print(f"No se encontraron resultados para {location}.")
            return 404, None, None
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud HTTP: {e}")
        return replydata.status_code if 'replydata' in locals() else 500, None, None

# Calcular el combustible requerido
def calcular_combustible(distancia_km, eficiencia_combustible=12):
    return distancia_km / eficiencia_combustible

def calcular_distancia_duracion_indicaciones(origen, destino, key, medio_transporte):
    # Geocodificar origen y destino
    orig_status, orig_lat, orig_lng = geocoding(origen, key)
    dest_status, dest_lat, dest_lng = geocoding(destino, key)

    if orig_status != 200 or dest_status != 200:
        print("Error en la geocodificación. No se puede calcular la distancia y duración.")
        return None, None, None

    # Construir la URL de la ruta entre origen y destino
    route_params = {
        "point": [f"{orig_lat},{orig_lng}", f"{dest_lat},{dest_lng}"],
        "vehicle": medio_transporte,  # Modo de transporte
        "key": key,
        "instructions": "true",  # Incluir instrucciones detalladas
        "locale": "es"  # Instrucciones en español
    }
   
    try:
        route_response = requests.get(route_url, params=route_params)
        route_response.raise_for_status()
        route_data = route_response.json()

        if 'paths' not in route_data or len(route_data['paths']) == 0:
            print("No se encontró una ruta válida entre los puntos.")
            return None, None, None

        # Extraer la distancia y duración de la ruta
        distance_meters = route_data['paths'][0]['distance']
        duration_seconds = route_data['paths'][0]['time'] / 1000  # Convertir de milisegundos a segundos
        instrucciones = route_data['paths'][0]['instructions']  # Instrucciones de la ruta
       
        distance_km = distance_meters / 1000  # Convertir a kilómetros
        distance_miles = distance_km * 0.621371  # Convertir kilómetros a millas
        duration_hms = convertir_duracion(duration_seconds)
       
        return distance_km, distance_miles, duration_hms, instrucciones
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud HTTP para la ruta: {e}")
        return None, None, None

def convertir_duracion(segundos):
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segundos = int(segundos % 60)
    return f"{horas:02}:{minutos:02}:{segundos:02}"

def generar_narrativa(origen, destino, distancia_km, distancia_millas, duracion, instrucciones):
    narrativa = (f"El viaje desde {origen} hasta {destino} cubre una distancia de aproximadamente {distancia_km:.2f} kilómetros "
                 f"({distancia_millas:.2f} millas). La duración estimada del viaje es de {duracion} (horas:minutos:segundos). "
                 "Aquí están las indicaciones detalladas:\n")
    for instruccion in instrucciones:
        distancia_instruccion = instruccion['distance'] / 1000  # Convertir a kilómetros
        narrativa += f"{instruccion['text']} durante {distancia_instruccion:.2f} kilómetros.\n"
    return narrativa

# Bucle principal para solicitar origen y destino hasta que el usuario escriba "s"
while True:
    origen = input("Ingrese el origen (o escriba 's' para terminar): ").strip().lower()
    if origen == "s":
        break
    destino = input("Ingrese el destino (o escriba 's' para terminar): ").strip().lower()
    if destino == "s":
        break

    print("Elija el medio de transporte:")
    print("1. Auto")
    print("2. Avión")
    print("3. Bus")
    medio = input("Ingrese su elección: ").strip().lower()
    
    if medio == '1':
        medio_transporte = "car"
    elif medio == '2':
        medio_transporte = "air"
    elif medio == '3':
        medio_transporte = "bus"
    else:
        print("Opción no válida. Intente nuevamente.")
        continue

    # Calcular la distancia, duración y obtener las indicaciones entre el origen y el destino proporcionados por el usuario
    distancia_km, distancia_millas, duracion, instrucciones = calcular_distancia_duracion_indicaciones(origen, destino, key, medio_transporte)

    if distancia_km is not None and duracion is not None and instrucciones is not None:
        narrativa = generar_narrativa(origen.capitalize(), destino.capitalize(), distancia_km, distancia_millas, duracion, instrucciones)
        print(narrativa)
