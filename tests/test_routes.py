def test_dashboard_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Financial Dashboard" in response.data

def test_income_crud_routes(client):
    # Add income via POST
    res = client.post('/income', data={
        'source': 'Salary',
        'amount': '45000',
        'date': '2026-09-01',
        'notes': 'Monthly income'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Salary" in res.data
    assert b"45,000" in res.data

def test_expense_crud_routes(client):
    # Add expense via POST
    res = client.post('/expenses', data={
        'category': 'Rent',
        'amount': '12000',
        'date': '2026-09-02',
        'description': 'Apartment rent'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Rent" in res.data
    assert b"12,000" in res.data

def test_budgets_route(client):
    res = client.get('/budgets')
    assert res.status_code == 200
    assert b"Budget Management" in res.data
    assert b"Automatic Budget Recommendation System" in res.data

def test_savings_route(client):
    res = client.get('/savings')
    assert res.status_code == 200
    assert b"Savings &amp; Goals" in res.data or b"Savings & Goals" in res.data

def test_advisor_route_offline_resilience(client):
    # Requesting advisor page and running analysis without Gemini key
    res = client.post('/advisor', data={
        'custom_query': 'What is my financial health?'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Spending Observations" in response_text_check(res.data)
    assert b"Disclaimer" in res.data

def response_text_check(data):
    return data

def test_reports_route(client):
    res = client.get('/reports')
    assert res.status_code == 200
    assert b"Monthly Financial Statement" in res.data

def test_transactions_and_csv_export(client):
    # Populate an income and expense
    client.post('/income', data={'source': 'Freelance', 'amount': '5000', 'date': '2026-09-10'})
    client.post('/expenses', data={'category': 'Food', 'amount': '800', 'date': '2026-09-11'})

    res = client.get('/transactions')
    assert res.status_code == 200
    assert b"Freelance" in res.data
    assert b"Food" in res.data

    csv_res = client.get('/transactions/export')
    assert csv_res.status_code == 200
    assert csv_res.headers['Content-Type'].startswith('text/csv')
    assert b"Freelance" in csv_res.data
    assert b"Food" in csv_res.data

def test_demo_data_flow(client):
    # Load demo data
    res_load = client.get('/demo/load', follow_redirects=True)
    assert res_load.status_code == 200
    assert b"Salary" in res_load.data
    assert b"35,000" in res_load.data

    # Clear demo data
    res_clear = client.get('/demo/clear', follow_redirects=True)
    assert res_clear.status_code == 200
