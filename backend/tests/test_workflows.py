import os
from uuid import uuid4
os.environ['DATABASE_URL']='sqlite:///./test_asset_management.db'
from fastapi.testclient import TestClient
from app.main import app

def token(client): return client.post('/api/auth/login',json={'username':'admin','password':'ChangeMe123!'}).json()['access_token']
def headers(client): return {'Authorization':'Bearer '+token(client)}
def test_seeded_assets_and_qr_restrictions():
    with TestClient(app) as c:
        r=c.get('/api/assets',headers=headers(c)); assert r.status_code==200 and r.json()['total']>=5
        a=r.json()['items'][0]; detail=c.get('/api/assets/'+str(a['id']),headers=headers(c)).json(); qr=c.get('/q/'+detail['public_token']).json(); page=c.get('/q/'+detail['public_token']+'/page').text; assert 'purchase_value' not in qr and 'holding_class' not in qr and 'REPORT PROBLEM' in page and 'innerHTML' not in page
def test_public_qr_report_creates_operational_ticket():
    with TestClient(app) as c:
        h=headers(c); asset=c.get('/api/assets',headers=h).json()['items'][0];detail=c.get('/api/assets/'+str(asset['id']),headers=h).json()
        report=c.post('/q/'+detail['public_token']+'/report-problem',json={'asset_id':asset['id'],'complaint':'Public QR failure'});assert report.status_code==200
        assert c.get('/api/assets/'+str(asset['id']),headers=h).json()['operational_status']=='UNDER_REPAIR'
def test_asset_requires_and_links_primary_service_contact():
    with TestClient(app) as c:
        h=headers(c); masters={name:c.get('/api/masters/'+name,headers=h).json()[0]['id'] for name in ['sites','employees','contacts']};categories=c.get('/api/masters/categories',headers=h).json();types=c.get('/api/masters/types',headers=h).json();category=next(x['id'] for x in categories if x['name']=='IT');asset_type=next(x['id'] for x in types if x['name']=='Desktop')
        base={'asset_name':'Contact-validated demo asset','category_id':category,'asset_type_id':asset_type,'current_site_id':masters['sites'],'staff_incharge_employee_id':masters['employees']}
        assert c.post('/api/assets',headers=h,json=base).status_code==422
        created=c.post('/api/assets',headers=h,json={**base,'primary_service_contact_id':masters['contacts']});assert created.status_code==200
        detail=c.get('/api/assets/'+str(created.json()['id']),headers=h).json();qr=c.get('/q/'+detail['public_token']).json();assert qr['service_contacts']
def test_asset_rejects_type_from_another_category():
    with TestClient(app) as c:
        h=headers(c); categories=c.get('/api/masters/categories',headers=h).json(); types=c.get('/api/masters/types',headers=h).json();site=c.get('/api/masters/sites',headers=h).json()[0]['id'];employee=c.get('/api/masters/employees',headers=h).json()[0]['id'];contact=c.get('/api/masters/contacts',headers=h).json()[0]['id']
        it=next(x['id'] for x in categories if x['name']=='IT'); aircon=next(x['id'] for x in types if x['name']=='Air Conditioner')
        assert c.post('/api/assets',headers=h,json={'asset_name':'Invalid category type','category_id':it,'asset_type_id':aircon,'current_site_id':site,'staff_incharge_employee_id':employee,'primary_service_contact_id':contact}).status_code==422
def test_asset_codes_use_category_id_and_category_sequence():
    with TestClient(app) as c:
        h=headers(c);categories=c.get('/api/masters/categories',headers=h).json();types=c.get('/api/masters/types',headers=h).json();site=c.get('/api/masters/sites',headers=h).json()[0]['id'];employee=c.get('/api/masters/employees',headers=h).json()[0]['id'];contact=c.get('/api/masters/contacts',headers=h).json()[0]['id'];it=next(x['id'] for x in categories if x['name']=='IT');desktop=next(x['id'] for x in types if x['name']=='Desktop')
        payload={'category_id':it,'asset_type_id':desktop,'current_site_id':site,'staff_incharge_employee_id':employee,'primary_service_contact_id':contact}
        first=c.post('/api/assets',headers=h,json={**payload,'asset_name':'Sequence test one'}).json()['asset_code'];second=c.post('/api/assets',headers=h,json={**payload,'asset_name':'Sequence test two'}).json()['asset_code'];assert first.startswith(f'DBL-{it}-') and second.startswith(f'DBL-{it}-') and int(second.rsplit('-',1)[1])==int(first.rsplit('-',1)[1])+1
def test_incharge_change_adds_history_event():
    with TestClient(app) as c:
        h=headers(c); asset=c.get('/api/assets',headers=h).json()['items'][0]; employees=c.get('/api/masters/employees',headers=h).json(); target=next(x for x in employees if x['name']!=asset['staff_incharge'])
        assert c.post(f"/api/assets/{asset['id']}/incharge",headers=h,json={'employee_id':target['id']}).status_code==200
        detail=c.get(f"/api/assets/{asset['id']}",headers=h).json();assert detail['staff_incharge']==target['name'] and any(e['type']=='INCHARGE_CHANGE' for e in detail['timeline'])
def test_transfer_updates_location_and_timeline():
    with TestClient(app) as c:
        h=headers(c); asset=c.get('/api/assets',headers=h).json()['items'][0]; sites=c.get('/api/masters/sites',headers=h).json();target=next(x for x in sites if x['name']!=asset['location'])
        assert c.post(f"/api/assets/{asset['id']}/transfer",headers=h,json={'site_id':target['id']}).status_code==200
        detail=c.get(f"/api/assets/{asset['id']}",headers=h).json();assert detail['location']==target['name'] and any(e['type']=='LOCATION_TRANSFER' for e in detail['timeline'])
def test_issue_and_return_update_current_custody():
    with TestClient(app) as c:
        h=headers(c); asset=next(x for x in c.get('/api/assets',headers=h).json()['items'] if not x['issued_to']);employee=c.get('/api/masters/employees',headers=h).json()[0]
        assert c.post(f"/api/assets/{asset['id']}/issue",headers=h,json={'employee_id':employee['id'],'condition':'Good'}).status_code==200
        assert c.get(f"/api/assets/{asset['id']}",headers=h).json()['issued_to']==employee['name']
        assert c.post(f"/api/assets/{asset['id']}/return",headers=h,json={'condition':'Good'}).status_code==200
        detail=c.get(f"/api/assets/{asset['id']}",headers=h).json();assert detail['issued_to'] is None and any(e['type']=='ASSET_RETURNED' for e in detail['timeline'])
def test_vendor_and_contact_can_be_created_for_asset_registration():
    with TestClient(app) as c:
        h=headers(c); suffix=uuid4().hex; vendor=c.post('/api/vendors',headers=h,json={'company_name':'New Service Vendor '+suffix,'phone':'123'});assert vendor.status_code==200
        contact=c.post('/api/contacts',headers=h,json={'name':'New Service Contact '+suffix,'vendor_id':vendor.json()['id'],'mobile':'123'});assert contact.status_code==200
        assert c.post('/api/vendors',headers=h,json={'company_name':'New Service Vendor '+suffix}).status_code==409
def test_admin_can_create_all_master_values_used_by_the_masters_screen():
    with TestClient(app) as c:
        h=headers(c); suffix=uuid4().hex
        category=c.post('/api/masters/categories',headers=h,json={'name':'Master Category '+suffix}); assert category.status_code==200
        asset_type=c.post('/api/masters/types',headers=h,json={'name':'Master Type '+suffix,'category_id':category.json()['id']}); assert asset_type.status_code==200
        for master in ['makes','sites','departments']:
            created=c.post('/api/masters/'+master,headers=h,json={'name':'Master '+master+' '+suffix}); assert created.status_code==200
            assert any(row['id']==created.json()['id'] for row in c.get('/api/masters/'+master,headers=h).json())
        assert c.post('/api/masters/types',headers=h,json={'name':'Master Type '+suffix,'category_id':category.json()['id']}).status_code==409
def test_ticket_restore_stops_downtime_and_close_follows():
    with TestClient(app) as c:
        h=headers(c); asset=c.get('/api/assets',headers=h).json()['items'][0]; ticket=c.post('/api/tickets',headers=h,json={'asset_id':asset['id'],'complaint':'test failure'}).json(); assert c.post(f"/api/tickets/{ticket['id']}/close",headers=h,json={}).status_code==400; assert c.post(f"/api/tickets/{ticket['id']}/restore",headers=h,json={}).status_code==200; assert c.post(f"/api/tickets/{ticket['id']}/close",headers=h,json={}).status_code==200
def test_ticket_escalation_and_parts_remain_on_one_ticket():
    with TestClient(app) as c:
        h=headers(c); asset=c.get('/api/assets',headers=h).json()['items'][0]; ticket=c.post('/api/tickets',headers=h,json={'asset_id':asset['id'],'complaint':'needs vendor'}).json()
        assert c.post(f"/api/tickets/{ticket['id']}/escalate",headers=h,json={'vendor_reference':'CASE-1'}).status_code==200
        assert c.post(f"/api/tickets/{ticket['id']}/parts",headers=h,json={'description':'Replacement battery','quantity':2,'unit_cost':100}).status_code==200
        detail=c.get(f"/api/tickets/{ticket['id']}",headers=h).json();assert detail['status']=='AWAITING_VENDOR' and detail['parts'][0]['description']=='Replacement battery'
def test_pm_requires_report():
    with TestClient(app) as c:
        h=headers(c); schedule=c.get('/api/pm/schedules',headers=h).json()[0]; payload={'completed_at':'2026-08-19T10:00:00','performed_by':'Technician','remarks':'Done'}; assert c.post(f"/api/pm/schedules/{schedule['id']}/complete",headers=h,json=payload).status_code==422
def test_pm_completion_accepts_uploaded_report():
    with TestClient(app) as c:
        h=headers(c); uploaded=c.post('/api/uploads',headers=h,files={'file':('report.pdf',b'%PDF-1.4 test','application/pdf')});assert uploaded.status_code==200 and c.get('/api/uploads/'+uploaded.json()['path']).status_code==401 and c.get('/api/uploads/'+uploaded.json()['path'],headers=h).status_code==200
        schedule=c.get('/api/pm/schedules',headers=h).json()[0]; payload={'completed_at':'2026-08-19T10:00:00','performed_by':'Technician','remarks':'Done','service_report_path':uploaded.json()['path']};assert c.post(f"/api/pm/schedules/{schedule['id']}/complete",headers=h,json=payload).status_code==200
def test_lifecycle_requires_and_applies_approval():
    with TestClient(app) as c:
        h=headers(c); a=c.get('/api/assets',headers=h).json()['items'][1]; req=c.post(f"/api/assets/{a['id']}/lifecycle/LOST",headers=h).json(); approvals=c.get('/api/approvals',headers=h).json(); approval=next(x for x in approvals if x['approval_number']==req['approval_number']); assert c.post(f"/api/approvals/{approval['id']}/approve",headers=h,json={}).status_code==200
def test_calibration_schedule_and_completion():
    with TestClient(app) as c:
        h=headers(c); asset=c.get('/api/assets',headers=h).json()['items'][2]
        response=c.post('/api/calibration/schedules',headers=h,json={'asset_id':asset['id'],'frequency_days':90,'next_due':'2026-09-01'})
        assert response.status_code in (200,409)
        schedule=next(x for x in c.get('/api/calibration/schedules',headers=h).json() if x['asset']==asset['asset_code'])
        assert c.post(f"/api/calibration/schedules/{schedule['id']}/complete",headers=h,json={'completed_at':'2026-08-19T10:00:00','performed_by':'Technician','result':'PASS'}).status_code==200
def test_contract_covers_multiple_assets_and_renewal_requires_approval():
    with TestClient(app) as c:
        h=headers(c); assets=c.get('/api/assets',headers=h).json()['items'][:2];vendor=c.get('/api/masters/vendors',headers=h).json()[0]
        created=c.post('/api/contracts',headers=h,json={'contract_type':'AMC','vendor_id':vendor['id'],'start_date':'2026-01-01','end_date':'2026-12-31','asset_ids':[x['id'] for x in assets]});assert created.status_code==200
        renewal=c.post(f"/api/contracts/{created.json()['id']}/renew",headers=h);assert renewal.status_code==200
        assert any(x['approval_number']==renewal.json()['approval_number'] and x['action_type']=='CONTRACT_RENEWAL' for x in c.get('/api/approvals',headers=h).json())
def test_external_movement_and_return_restore_asset_status():
    with TestClient(app) as c:
        h=headers(c); asset=c.get('/api/assets',headers=h).json()['items'][0]
        movement=c.post('/api/movements',headers=h,json={'asset_id':asset['id'],'movement_type':'REPAIR','destination':'Service centre','expected_return':'2026-09-01'});assert movement.status_code==200
        assert c.get('/api/assets/'+str(asset['id']),headers=h).json()['operational_status']=='OUTSIDE'
        assert c.post(f"/api/movements/{movement.json()['id']}/return",headers=h).status_code==200
        assert c.get('/api/assets/'+str(asset['id']),headers=h).json()['operational_status']=='OPERATIONAL'
def test_reports_show_repeat_breakdowns():
    with TestClient(app) as c:
        h=headers(c); asset=c.get('/api/assets',headers=h).json()['items'][0]
        for complaint in ('repeat issue one','repeat issue two'):
            c.post('/api/tickets',headers=h,json={'asset_id':asset['id'],'complaint':complaint})
        report=c.get('/api/reports/summary',headers=h)
        assert report.status_code==200 and any(row['asset']==asset['asset_code'] for row in report.json()['repeat_breakdowns'])
def test_due_alerts_are_generated_for_seeded_pm():
    with TestClient(app) as c:
        h=headers(c); alerts=c.get('/api/alerts',headers=h)
        assert alerts.status_code==200 and any(a['type'].startswith('PM_') for a in alerts.json())
