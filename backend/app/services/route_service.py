# app/services/route_service.py
import httpx
from ortools.constraint_solver import routing_enums_pb2, pywrapcp
from app.database import supabase
from app.config import settings


async def get_distance_matrix(locations: list) -> list:
    """Call Google Maps Distance Matrix API. Returns NxN seconds matrix."""
    coords = [f"{loc['lat']},{loc['lng']}" for loc in locations]
    origins = destinations = '|'.join(coords)


    async with httpx.AsyncClient() as c:
        r = await c.get(
            'https://maps.googleapis.com/maps/api/distancematrix/json',
            params={
                'origins': origins, 'destinations': destinations,
                'key': settings.google_maps_api_key,
                'departure_time': 'now'
            }
        )
        data = r.json()


    return [
        [elem['duration']['value'] for elem in row['elements']]
        for row in data['rows']
    ]




def solve_vrp(distance_matrix: list, num_vehicles: int) -> dict:
    """Run OR-Tools VRP solver. Returns {vehicle_index: [stop_node_indices]}."""
    manager = pywrapcp.RoutingIndexManager(
        len(distance_matrix), num_vehicles, 0)
    routing = pywrapcp.RoutingModel(manager)


    def distance_callback(from_idx, to_idx):
        return distance_matrix[manager.IndexToNode(from_idx)][manager.IndexToNode(to_idx)]


    cb = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(cb)


    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    params.time_limit.seconds = 30  # Hard cap from TSD Section 5.3


    solution = routing.SolveWithParameters(params)
    if not solution:
        return {}


    routes = {}
    for v in range(num_vehicles):
        idx, route = routing.Start(v), []
        while not routing.IsEnd(idx):
            route.append(manager.IndexToNode(idx))
            idx = solution.Value(routing.NextVar(idx))
        routes[v] = route[1:]  # Exclude depot at index 0
    return routes




async def optimize_daily_routes(date: str, business_id: str) -> list:
    jobs  = supabase.table('jobs').select('id, scheduled_at, clients(address)') \
        .eq('business_id', business_id) \
        .gte('scheduled_at', f'{date}T00:00:00') \
        .lte('scheduled_at', f'{date}T23:59:59') \
        .neq('status', 'cancelled').execute()


    techs = supabase.table('technicians').select('id, full_name, home_lat, home_lng') \
        .eq('business_id', business_id).eq('is_active', True).execute()


    if not jobs.data or not techs.data:
        return []


    # Location index 0 = depot (office). Indices 1..N = jobs.
    # In production: geocode client addresses to lat/lng via Google Geocoding API.
    locations = [{'lat': 33.44, 'lng': -84.44}]  # Depot
    locations += [{'lat': 33.45 + i*0.01, 'lng': -84.44 + i*0.01}
                  for i, _ in enumerate(jobs.data)]


    matrix      = await get_distance_matrix(locations)
    routes      = solve_vrp(matrix, len(techs.data))
    assignments = []


    for v_idx, stops in routes.items():
        tech   = techs.data[v_idx]
        job_list = [jobs.data[i - 1] for i in stops if i > 0]
        assignments.append({'technician': tech, 'jobs': job_list})


    return assignments

