
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
from presupuestos.models import Presupuesto
from presupuestos.views import PresupuestoViewSet

def verify_recycle_bin():
    User = get_user_model()
    factory = APIRequestFactory()
    
    # 1. Setup Data
    username = 'verify_recycle_user'
    try:
        u = User.objects.get(username=username)
        u.delete()
    except User.DoesNotExist:
        pass

    user = User.objects.create_user(username=username, password='password123')
    
    # Active Budget
    active_budget = Presupuesto.objects.create(
        nombre_proyecto="Active Budget",
        creado_por=user,
        validez_oferta="2025-12-31",
        tipo_proyecto="cotizacion",
        formas_pago="Contado",
        cliente="Client A",
        ubicacion_geografica="Loc A",
        activo=True
    )
    
    # Inactive Budget (Deleted)
    deleted_budget = Presupuesto.objects.create(
        nombre_proyecto="Deleted Budget",
        creado_por=user,
        validez_oferta="2025-12-31",
        tipo_proyecto="cotizacion",
        formas_pago="Contado",
        cliente="Client B",
        ubicacion_geografica="Loc B",
        activo=False
    )
    
    print(f"Created Active Budget: {active_budget.id}")
    print(f"Created Deleted Budget: {deleted_budget.id}")

    # 2. Test Default Behavior (Should see ONLY Active)
    print("\nTest 1: Default Request (No Params)")
    request = factory.get('/presupuestos/')
    request = Request(request)
    request.user = user
    view = PresupuestoViewSet()
    view.request = request
    view.format_kwarg = None
    view.action = 'list'
    
    qs_default = view.get_queryset()
    ids_default = list(qs_default.values_list('id', flat=True))
    
    if active_budget.id in ids_default and deleted_budget.id not in ids_default:
        print("PASS: Default returns only active budgets.")
    else:
        print(f"FAIL: Default returned IDs {ids_default}")

    # 3. Test Recycle Bin Behavior (Should see ONLY Deleted)
    print("\nTest 2: Recycle Bin Request (?activo=False)")
    request_recycle = factory.get('/presupuestos/', {'activo': 'False'})
    request_recycle = Request(request_recycle)
    request_recycle.user = user
    view = PresupuestoViewSet()
    view.request = request_recycle
    view.format_kwarg = None
    view.action = 'list'
    view.request = request_recycle
    
    print(f"DEBUG: query_params: {view.request.query_params}")
    
    qs_recycle = view.get_queryset()
    ids_recycle = list(qs_recycle.values_list('id', flat=True))
    
    if deleted_budget.id in ids_recycle and active_budget.id not in ids_recycle:
        print("PASS: ?activo=False returns only deleted budgets.")
    else:
        print(f"FAIL: Recycle bin returned IDs {ids_recycle}")

try:
    verify_recycle_bin()
except Exception as e:
    print(f"ERROR: Verification failed with {e}")
