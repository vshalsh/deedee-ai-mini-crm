import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from fastapi.testclient import TestClient
from deedee.api import create_app

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=str(Path(self.temp.name)/'crm.db')
        self.client=TestClient(create_app(self.path))
        self.client.__enter__()
        self.company=self.create('companies',{'name':'Example Co'})
        self.contact=self.create('contacts',{'name':'Alex','company_id':self.company['id']})

    def tearDown(self):
        self.client.__exit__(None,None,None)
        self.temp.cleanup()

    def create(self,kind,data):
        result=self.client.post('/api/v1/'+kind,json=data)
        self.assertEqual(result.status_code,201,result.text)
        return result.json()

    def test_deal_money_stage_history_and_persistence(self):
        deal=self.create('deals',{'title':'Pilot','company_id':self.company['id'],
            'contact_id':self.contact['id'],'amount':'123.45','currency':'MYR'})
        body={k:v for k,v in deal.items() if k not in {'id','workspace_id','created_at','updated_at'}}
        body['stage']='won'
        self.assertEqual(self.client.put('/api/v1/deals/'+deal['id'],json=body).status_code,200)
        self.client.put('/api/v1/deals/'+deal['id'],json=body)
        history=self.client.get('/api/v1/deals/'+deal['id']+'/history').json()['items']
        self.assertEqual([(h['from_stage'],h['to_stage']) for h in history],[(None,'lead'),('lead','won')])
        with TestClient(create_app(self.path)) as second:
            self.assertEqual(second.get('/api/v1/deals/'+deal['id']).json()['amount'],'123.45')
        self.assertEqual(self.client.delete('/api/v1/contacts/'+self.contact['id']).status_code,409)

    def test_work_crud_filters_and_references(self):
        deal=self.create('deals',{'title':'CRM Pilot'})
        task=self.create('tasks',{'title':'Send proposal','deal_id':deal['id'],'due_date':'2026-10-01'})
        activity=self.create('activities',{'type':'meeting','occurred_at':'2026-10-23T09:00:00+08:00',
            'note':'Discussed next steps.','deal_id':deal['id']})
        self.assertIn('01:00:00',activity['occurred_at'])
        self.assertEqual(self.client.get('/api/v1/tasks',params={'deal_id':deal['id']}).json()['total'],1)
        self.assertEqual(self.client.get('/api/v1/tasks',params={'status':'done'}).json()['total'],0)
        self.assertEqual(self.client.get('/api/v1/activities',params={'q':'next steps'}).json()['total'],1)
        self.assertEqual(self.client.delete('/api/v1/deals/'+deal['id']).status_code,409)
        for kind,record,body in [('tasks',task,{'title':'Send proposal','status':'done'}),
                                 ('activities',activity,{'note':'Updated','type':'note','occurred_at':'2026-10-23T00:00:00Z','contact_id':self.contact['id']})]:
            self.assertEqual(self.client.put('/api/v1/'+kind+'/'+record['id'],json=body).status_code,200)
            self.assertEqual(self.client.delete('/api/v1/'+kind+'/'+record['id']).status_code,204)
        self.assertEqual(self.client.delete('/api/v1/deals/'+deal['id']).status_code,204)

    def test_invalid_work_data_and_failed_writes(self):
        for kind,data in [('deals',{'title':'X','stage':'invalid'}),('deals',{'title':'X','amount':'0.001'}),
                          ('deals',{'title':'X','amount':'-1'}),('deals',{'title':'X','currency':'usd'}),
                          ('tasks',{'title':'X','due_date':'invalid'}),('tasks',{'title':'X','status':'unknown'}),
                          ('activities',{'note':'X','occurred_at':'2026-10-23T10:00:00'}),
                          ('activities',{'note':'X','occurred_at':'2026-10-23T10:00:00Z'})]:
            response=self.client.post('/api/v1/'+kind,json=data)
            self.assertEqual(response.status_code,422,response.text)
        for kind,data in [('deals',{'title':'X','contact_id':'missing'}),('tasks',{'title':'X','deal_id':'missing'}),
                          ('activities',{'note':'X','occurred_at':'2026-10-23T10:00:00Z','company_id':'missing'})]:
            self.assertEqual(self.client.post('/api/v1/'+kind,json=data).status_code,409)
            self.assertEqual(self.client.get('/api/v1/'+kind).json()['total'],0)

    def test_dashboard_currencies_and_backup(self):
        self.create('deals',{'title':'A','amount':'0.10','currency':'USD','stage':'proposal'})
        self.create('deals',{'title':'B','amount':'0.20','currency':'USD','stage':'proposal'})
        self.create('deals',{'title':'C','amount':'50.00','currency':'MYR','stage':'won'})
        self.create('tasks',{'title':'Past due','due_date':'2000-01-01'})
        self.create('tasks',{'title':'Already done','due_date':'2000-01-01','status':'done'})
        data=self.client.get('/api/v1/dashboard').json()
        self.assertEqual(data['pipeline_totals']['USD']['proposal'],'0.30')
        self.assertEqual(data['pipeline_totals']['MYR']['won'],'50.00')
        self.assertEqual(data['counts']['overdue_tasks'],1)
        backup=self.client.get('/api/v1/backup').json()
        self.assertEqual(len(backup['deals']),3)
        self.assertEqual(len(backup['deal_history']),3)
        self.assertEqual(backup['format_version'],1)

    def test_existing_foundation_database_upgrade(self):
        from importlib.resources import files
        legacy=str(Path(self.temp.name)/'legacy.db')
        with sqlite3.connect(legacy) as db:
            db.executescript(files('deedee').joinpath('migrations/001_foundation.sql').read_text())
            db.execute('CREATE TABLE schema_migrations(version TEXT PRIMARY KEY)')
            db.execute("INSERT INTO schema_migrations VALUES ('001_foundation.sql')")
            db.execute("INSERT INTO companies VALUES ('existing','local','Original',NULL,NULL,NULL,'then','then')")
        with TestClient(create_app(legacy)) as client:
            self.assertEqual(client.get('/api/v1/companies/existing').json()['name'],'Original')
            self.assertEqual(client.post('/api/v1/tasks',json={'title':'After upgrade'}).status_code,201)

    def test_static_ui_and_missing_records(self):
        self.assertEqual(self.client.get('/').status_code,200)
        self.assertIn('DeeDee',self.client.get('/').text)
        self.assertEqual(self.client.get('/static/app.js').status_code,200)
        for kind in ['deals','tasks','activities']:
            self.assertEqual(self.client.get('/api/v1/'+kind+'/missing').status_code,404)
        self.assertEqual(self.client.get('/api/v1/deals?stage=unknown').status_code,422)

if __name__=='__main__':
    unittest.main()
