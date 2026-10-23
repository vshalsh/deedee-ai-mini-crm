import socket
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from deedee.api import create_app
from deedee.domain import Company, Contact
from deedee.persistence import SQLiteRepository


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp.name) / 'crm.db')
        self.client = TestClient(create_app(self.db))
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.temp.cleanup()

    def company(self, name='Northstar'):
        response = self.client.post('/api/v1/companies', json={'name': name, 'notes': 'private note'})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def contact(self, company_id=None):
        response = self.client.post('/api/v1/contacts', json={
            'name': 'Jordan Lee', 'email': 'jordan@example.com', 'company_id': company_id,
            'tags': ['demo', 'demo'], 'phone': '+000-demo'})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_company_crud_and_restart_persistence(self):
        record = self.company()
        self.assertEqual(record['workspace_id'], 'local')
        self.assertIn('+00:00', record['created_at'])
        with TestClient(create_app(self.db)) as other:
            self.assertEqual(other.get('/api/v1/companies/'+record['id']).json()['name'], 'Northstar')
        response = self.client.put('/api/v1/companies/'+record['id'], json={'name':'Updated'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name'], 'Updated')
        self.assertEqual(self.client.delete('/api/v1/companies/'+record['id']).status_code, 204)
        self.assertEqual(self.client.get('/api/v1/companies/'+record['id']).status_code, 404)

    def test_contacts_crud_relationship_and_delete_restriction(self):
        company = self.company()
        contact = self.contact(company['id'])
        self.assertEqual(contact['tags'], ['demo'])
        self.assertEqual(self.client.delete('/api/v1/companies/'+company['id']).status_code, 409)
        response = self.client.put('/api/v1/contacts/'+contact['id'], json={'name':'Jordan New', 'company_id':None})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()['company_id'])
        self.assertEqual(self.client.delete('/api/v1/companies/'+company['id']).status_code, 204)
        self.assertEqual(self.client.delete('/api/v1/contacts/'+contact['id']).status_code, 204)
        self.assertEqual(self.client.get('/api/v1/contacts/'+contact['id']).status_code, 404)

    def test_unknown_company_rejected_and_failed_write_rolled_back(self):
        response = self.client.post('/api/v1/contacts', json={'name':'Invalid', 'company_id':'missing'})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.client.get('/api/v1/contacts').json()['total'], 0)
        contact = self.contact()
        self.assertEqual(self.client.put('/api/v1/contacts/'+contact['id'], json={
            'name':'Broken', 'company_id':'missing'}).status_code, 409)
        self.assertEqual(self.client.get('/api/v1/contacts/'+contact['id']).json()['name'], 'Jordan Lee')

    def test_search_pagination_and_sql_input(self):
        self.company('Alpha')
        company = self.company('Beta_100%')
        self.contact(company['id'])
        result = self.client.get('/api/v1/companies', params={'limit':1,'offset':1}).json()
        self.assertEqual(result['total'], 2)
        self.assertEqual(result['items'][0]['name'], 'Beta_100%')
        for q in ['Beta', '100%', 'Beta_']:
            self.assertEqual(self.client.get('/api/v1/companies',params={'q':q}).json()['total'], 1)
        for q in ['Beta', 'jordan@example.com', 'demo']:
            self.assertEqual(self.client.get('/api/v1/contacts',params={'q':q}).json()['total'], 1)
        self.assertEqual(self.client.get('/api/v1/contacts',params={'company_id':'other'}).json()['total'], 0)
        self.assertEqual(self.client.get('/api/v1/companies',params={'q':"' OR 1=1 --"}).json()['total'], 0)

    def test_input_errors_are_consistent_and_do_not_echo_payload(self):
        for payload in [{'name':'  '}, {'name':'Test','email':'invalid'},
                        {'name':'Test','workspace_id':'other'}, {'name':'Test','tags':['']}]:
            response = self.client.post('/api/v1/contacts', json=payload)
            self.assertEqual(response.status_code, 422)
            self.assertEqual(response.json()['error']['code'], 'invalid_request')
        for path in ['/api/v1/contacts?limit=101','/api/v1/companies?offset=-1']:
            self.assertEqual(self.client.get(path).status_code, 422)
        response = self.client.post('/api/v1/companies', json={'name':'X','website':'javascript:bad'})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn('javascript:bad', response.text)

    def test_missing_updates_and_deletes(self):
        for resource in ['companies','contacts']:
            path = '/api/v1/'+resource+'/missing'
            self.assertEqual(self.client.put(path,json={'name':'Test'}).status_code, 404)
            self.assertEqual(self.client.delete(path).status_code, 404)

    def test_selected_context_is_minimal_and_mock_has_no_network_or_writes(self):
        company = self.company()
        selected = self.contact(company['id'])
        other = self.contact()
        selection = {'contact_ids':[selected['id']], 'company_ids':[company['id']]}
        preview = self.client.post('/api/v1/ai/context',json=selection)
        self.assertEqual(preview.status_code, 200)
        self.assertNotIn('jordan@example.com', preview.text)
        self.assertNotIn('private note', preview.text)
        self.assertNotIn(other['id'], preview.text)
        self.assertEqual(self.client.post('/api/v1/ai/summarize',json=selection).status_code, 422)
        before = Path(self.db).read_bytes()
        with patch.object(socket.socket, 'connect', side_effect=AssertionError('No network allowed')):
            a = self.client.post('/api/v1/ai/summarize',json=dict(selection,confirm=True))
            b = self.client.post('/api/v1/ai/summarize',json=dict(selection,confirm=True))
        self.assertEqual(a.status_code, 200, a.text)
        self.assertEqual(a.json(), b.json())
        self.assertEqual(set(a.json()['source_ids']), {selected['id'],company['id']})
        self.assertTrue(a.json()['suggestion_only'])
        self.assertFalse(a.json()['external_request'])
        self.assertEqual(Path(self.db).read_bytes(), before)

    def test_context_selection_errors(self):
        self.assertEqual(self.client.post('/api/v1/ai/context',json={}).status_code, 422)
        self.assertEqual(self.client.post('/api/v1/ai/context',json={'contact_ids':['missing']}).status_code, 404)
        self.assertEqual(self.client.post('/api/v1/ai/context',json={'contact_ids':['a']*20,'company_ids':['b']}).status_code, 422)

    def test_migration_is_idempotent_and_health_available(self):
        SQLiteRepository(self.db).initialize()
        SQLiteRepository(self.db).initialize()
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM schema_migrations').fetchone()[0], 2)
        self.assertEqual(self.client.get('/health').json(), {'status':'ok','provider':'mock'})

    def test_domain_validation_without_http(self):
        for entity in [Company, Contact]:
            with self.assertRaises(ValueError):
                entity(name=' ')


if __name__ == '__main__':
    unittest.main()
