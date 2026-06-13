# Sales Intelligence Hub

A Streamlit-based web application for managing and analyzing sales data with role-based access control. This application allows admins from different branches to view, edit, and query sales data securely.

## Features

Multi-Level Authentication
- Super Admin: Full access to all branches
- Branch Admins: Limited to their own branch data

Dashboard with CRUD Operations
- View sales data in real-time
- Add new sales entries
- Edit existing records
- Delete records with branch-level restrictions

Sales Data Viewer
- Browse customer sales, payment splits, and branch information
- Role-based table access control

Query Center
- Pre-built SQL queries for common analytics
- Basic queries, aggregate queries, join-based queries, and financial tracking
- Auto-filters by branch for non-superadmin users

Insights and Reporting
- Overall business revenue metrics
- Branch-wise sales comparison and analysis
- Received vs Pending payment analysis
- Pending collection percentage tracking
- Payment method analysis (Cash, UPI, Card)
- Sales trends and growth visualization
- Branch performance summary with collection rates

Secure Database Connection
- PostgreSQL integration
- Primary key auto-detection
- Branch-level data isolation

## Prerequisites

- Python 3.8 or higher
- PostgreSQL database server
- pip (Python package manager)

## Installation

Clone or Download the Project
```bash
git clone <repository-url>
cd project
```

Create a Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

Install Required Dependencies
```bash
pip install -r requirements.txt
```

Or install packages individually:
```bash
pip install streamlit pandas psycopg2-binary plotly
```

## Database Setup

Create PostgreSQL Database
```sql
CREATE DATABASE sales_intelligence_hub;
```

Create Required Tables

branches table:
```sql
CREATE TABLE branches (
    branch_id SERIAL PRIMARY KEY,
    branch_name VARCHAR(100) NOT NULL,
    branch_admin_name VARCHAR(100)
);
```

customer_sales table:
```sql
CREATE TABLE customer_sales (
    sale_id SERIAL PRIMARY KEY,
    branch_id INT NOT NULL,
    gross_sales DECIMAL(10, 2),
    received_amount DECIMAL(10, 2),
    pending_amount DECIMAL(10, 2),
    status VARCHAR(50),
    date TIMESTAMP,
    FOREIGN KEY (branch_id) REFERENCES branches(branch_id)
);
```

payment_splits table:
```sql
CREATE TABLE payment_splits (
    split_id SERIAL PRIMARY KEY,
    sale_id INT NOT NULL,
    branch_id INT NOT NULL,
    payment_method VARCHAR(50),
    amount_paid DECIMAL(10, 2),
    FOREIGN KEY (sale_id) REFERENCES customer_sales(sale_id),
    FOREIGN KEY (branch_id) REFERENCES branches(branch_id)
);
```

users table:
```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    branch_id INT,
    FOREIGN KEY (branch_id) REFERENCES branches(branch_id)
);
```

## PostgreSQL Triggers

Triggers are automated database actions that execute when specific events occur. This project uses triggers to automatically update sales status based on payment status.

Trigger 1: Update Sales Status Based on Pending Amount

Purpose: Automatically update the status of a sale to 'open' or 'close' based on whether there is a pending amount remaining.

When it executes: After any INSERT or UPDATE on the payment_splits table

Logic:
- If pending_amount > 0: Set status to 'open' (payment still pending)
- If pending_amount = 0: Set status to 'close' (payment completed)

Create the trigger function:
```sql
CREATE OR REPLACE FUNCTION update_sales_status()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE customer_sales
    SET status = CASE 
                    WHEN pending_amount > 0 THEN 'open'
                    WHEN pending_amount = 0 THEN 'close'
                 END
    WHERE customer_sales.sale_id = NEW.sale_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

Create the trigger:
```sql
CREATE TRIGGER trigger_update_sales_status
AFTER INSERT OR UPDATE ON payment_splits
FOR EACH ROW
EXECUTE FUNCTION update_sales_status();
```

How it works:
1. User inserts or updates a payment record in payment_splits table
2. Trigger automatically fires
3. It calculates pending_amount for that sale
4. Updates the status field in customer_sales based on pending_amount
5. No manual status updates needed - it's automatic

Example scenario:
- Sale has gross_sales = 10000, received_amount = 7000, pending_amount = 3000
- Status becomes 'open'
- User records another payment of 3000
- pending_amount becomes 0
- Trigger automatically updates status to 'close'

Benefits:
- Data consistency: Status always reflects actual payment status
- No manual updates: Automatic status changes
- Real-time accuracy: Instant updates whenever payments are recorded
- Error prevention: Eliminates manual status update mistakes

View created triggers:
```sql
SELECT trigger_name, event_object_table, action_statement 
FROM information_schema.triggers 
WHERE trigger_schema = 'public';
```

Drop a trigger if needed:
```sql
DROP TRIGGER trigger_update_sales_status ON payment_splits;
DROP FUNCTION update_sales_status();
```

Trigger 2: Update Received Amount Based on Payments

Purpose: Automatically calculate the total received amount by summing all payments from the payment_splits table for a specific sale.

When it executes: After any INSERT or UPDATE on the payment_splits table

Logic: Sum all amount_paid values in payment_splits where sale_id matches the new record, then update the received_amount in customer_sales.

Create the trigger function:
```sql
CREATE OR REPLACE FUNCTION update_received_amount()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE customer_sales
    SET received_amount = (
        SELECT SUM(payment_splits.amount_paid)
        FROM payment_splits
        WHERE payment_splits.sale_id = NEW.sale_id
    )
    WHERE customer_sales.sale_id = NEW.sale_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

Create the trigger:
```sql
CREATE TRIGGER trigger_update_received_amount
AFTER INSERT OR UPDATE ON payment_splits
FOR EACH ROW
EXECUTE FUNCTION update_received_amount();
```

How it works:
1. User records a payment in payment_splits table
2. Trigger automatically fires
3. It sums all payments for that sale_id
4. Updates the received_amount field in customer_sales
5. No manual calculation needed

Example scenario:
- Sale has gross_sales = 10000
- User records payment 1: 5000 (Cash)
- Trigger updates received_amount to 5000
- User records payment 2: 3000 (UPI)
- Trigger updates received_amount to 8000 (5000 + 3000)
- User records payment 3: 2000 (Card)
- Trigger updates received_amount to 10000 (5000 + 3000 + 2000)

Benefits:
- Accurate received amount tracking
- Handles multiple payment methods automatically
- No manual amount entry needed
- Real-time calculation
- Prevents calculation errors

Trigger 3: Calculate Pending Amount Automatically

Purpose: Automatically calculate the pending amount by subtracting received_amount from gross_sales.

When it executes: After any INSERT or UPDATE on the payment_splits table (after Trigger 2 updates received_amount)

Logic: pending_amount = gross_sales - received_amount

Create the trigger function:
```sql
CREATE OR REPLACE FUNCTION calculate_pending_amount()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE customer_sales
    SET pending_amount = gross_sales - received_amount
    WHERE customer_sales.sale_id = NEW.sale_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

Create the trigger:
```sql
CREATE TRIGGER trigger_calculate_pending_amount
AFTER INSERT OR UPDATE ON payment_splits
FOR EACH ROW
EXECUTE FUNCTION calculate_pending_amount();
```

How it works:
1. User records a payment in payment_splits table
2. Trigger 2 updates received_amount
3. Trigger 3 fires and calculates pending_amount
4. pending_amount = gross_sales - received_amount
5. No manual pending calculation needed

Example scenario:
- Sale has gross_sales = 10000, received_amount = 0, pending_amount = 10000
- User records payment of 3000
- Trigger 2 updates received_amount to 3000
- Trigger 3 calculates pending_amount = 10000 - 3000 = 7000
- User records payment of 4000
- Trigger 2 updates received_amount to 7000
- Trigger 3 calculates pending_amount = 10000 - 7000 = 3000

Benefits:
- Automatic pending calculation
- Always accurate
- No manual calculations
- Instant updates
- Eliminates rounding errors

Complete Trigger Execution Flow

When a payment is recorded:
```
Payment inserted into payment_splits
        ↓
Trigger 2 fires: Recalculates received_amount (SUM of all payments)
        ↓
Trigger 3 fires: Recalculates pending_amount (gross_sales - received_amount)
        ↓
Trigger 1 fires: Updates status ('open' or 'close' based on pending_amount)
        ↓
All three amounts and status are now updated automatically
```

View all triggers:
```sql
SELECT trigger_name, event_object_table, action_statement 
FROM information_schema.triggers 
WHERE trigger_schema = 'public'
ORDER BY event_object_table;
```



Trigger Summary Table

| Trigger Name | Function | Executes | Updates |
|---|---|---|---|
| trigger_update_received_amount | Sum all payments | After INSERT/UPDATE on payment_splits | received_amount |
| trigger_calculate_pending_amount | Subtract from gross | After INSERT/UPDATE on payment_splits | pending_amount |
| trigger_update_sales_status | Check if fully paid | After INSERT/UPDATE on payment_splits | status |

## Configuration

Update Database Credentials

Open each Python file and update the connection parameters in the get_connection() function:

```python
def get_connection():
    return psycopg2.connect(
        user='postgres',        # Your PostgreSQL username
        host='localhost',       # Your database host
        database='sales_intelligence_hub',  # Database name
        port='5432',           # PostgreSQL port
        password='*****'     # Your PostgreSQL password
    )
```

Update User Credentials

Edit LOGIN_interface.py to change default login credentials:

```python
USERS = {
    "superadmin":       {"password": "super", "branch_id": 0},
    "admin_chennai":    {"password": "che", "branch_id": 1},
    "admin_bangalore":  {"password": "ban", "branch_id": 2},
    # ... add or modify as needed
}
```

## Running the Application

Start the Streamlit Application
```bash
streamlit run LOGIN_interface.py
```

The application will open in your default browser at http://localhost:8501

Access the Pages

Once logged in, you can navigate through:
- Dashboard (1_Dashboard.py): Edit, add, delete records
- Query Centre (2_query_centre.py): Run pre-built SQL queries
- View Sales Data (View_sales_data.py): Browse sales data
- Insights & Reporting (3_Insights_and_report.py): Analyze sales metrics and trends

## User Roles and Permissions

Super Admin (superadmin)
- Branch ID: 0 (all branches)
- Access: All tables (customer_sales, payment_splits, users, branches)
- Permissions: View, edit, add, delete across all branches
- Reports: Access to company-wide insights and metrics

Branch Admin (e.g., admin_chennai)
- Branch ID: 1-8 (specific branch)
- Access: Limited to their branch data
- Permissions: 
  - View own branch data only
  - Edit/add/delete only within own branch
  - Cannot modify branch_id field
- Reports: Access only to their branch metrics and analytics

## Project Structure

```
project/
├── LOGIN_interface.py         Main login page and authentication
├── 1_Dashboard.py            CRUD operations page
├── 2_query_centre.py         Pre-built query center
├── View_sales_data.py        Data viewer page
├── 3_Insights_and_report.py  Analytics and reporting page
├── requirements.txt          Python dependencies
└── README.md                Documentation
```

File Descriptions

LOGIN_interface.py
- User authentication and session management
- Role-based access control
- Dashboard welcome page

1_Dashboard.py
- View tables with pagination
- Edit existing records
- Add new sales entries
- Delete records with branch-level restrictions

2_query_centre.py
- Pre-built SQL queries organized by category
- Basic queries, aggregate queries, join-based queries
- Financial tracking queries
- Automatic branch filtering for non-superadmin users

View_sales_data.py
- Display sales data in read-only format
- Branch-specific data isolation
- Multi-table viewing

3_Insights_and_report.py
- Overall business revenue metrics
- Branch-wise sales comparison analysis
- Received vs pending payment visualization
- Pending collection percentage tracking
- Payment method analysis with charts
- Sales trends and growth tracking
- Branch performance summary with collection rates

## Security Features

Session-Based Authentication
- Users remain logged in during their session
- Logout clears session data immediately

Branch-Level Data Isolation
- Branch admins can only see their own branch data
- Cannot modify branch_id of existing records
- Queries automatically filtered by branch access level

Parameterized SQL Queries
- All queries use parameterized statements to prevent SQL injection
- No direct string concatenation for user inputs

Role-Based Access Control (RBAC)
- Different features available based on user role
- Super admins have unrestricted access
- Branch admins have restricted access

Important Note: Change default passwords before production deployment. Consider implementing additional security measures such as environment-based configuration files and password hashing for production use.

## Query Categories

Basic Queries
- Retrieve all records from customer_sales, branches, payment_splits tables
- Display records with specific status filters

Aggregate Queries
- Total gross sales across all branches
- Total received and pending amounts
- Sales count per branch
- Collection totals by category

Join-Based Queries
- Sales data with branch names
- Branch-wise total gross sales
- Sales with payment method information
- Sales with branch admin names

Financial Tracking Queries
- Sales with pending amount above threshold
- Top performing sales records
- Payment method-wise collection totals

## Reporting and Analytics Features

Revenue Metrics
- Total orders count
- Total revenue across branches
- Total received amount
- Total pending amount

Branch Performance Analysis
- Branch-wise sales comparison
- Branch performance ranking
- Average order value per branch
- Collection rate percentage per branch

Payment Analysis
- Payment method breakdown
- Transaction count by method
- Amount received by payment method
- Payment method distribution charts

Sales Trends
- Monthly sales trend visualization
- Month-over-month growth percentage
- Sales order trend analysis

Collection Status
- Received vs pending visualization
- Collection percentage by branch
- Pending amount tracking
- Outstanding payment analysis

## Troubleshooting

### Error: psycopg2.OperationalError - could not connect to server

Ensure PostgreSQL is running and connection credentials are correct.

```bash
psql -U postgres -h localhost -d postgres -c "SELECT 1"
```

### Error: Please login first from the main page

This indicates you are accessing a page directly. Always start from LOGIN_interface.py:

```bash
streamlit run LOGIN_interface.py
```

### Error: Could not find primary key for table name

Ensure your database tables have a PRIMARY KEY constraint defined.

### Error: Wrong username or password

Verify credentials match those in the USERS dictionary in LOGIN_interface.py.

## Python Dependencies

requirements.txt:
```
streamlit>=1.28.0
pandas>=1.5.0
psycopg2-binary>=2.9.0
plotly>=5.0.0
```

Install all dependencies:
```bash
pip install -r requirements.txt
```

## Usage Workflow

1. Run the application: streamlit run LOGIN_interface.py
2. Login with your credentials (e.g., superadmin / super)
3. Navigate using the left sidebar to access Dashboard, Query Centre, View Sales Data, or Insights & Reporting
4. View data relevant to your role and branch
5. Perform data management operations in Dashboard (add, edit, delete records)
6. Run pre-built queries in Query Centre
7. Analyze metrics and trends in Insights & Reporting
8. Click logout button to exit

## Best Practices

- Always start the application with LOGIN_interface.py
- Store database credentials in environment variables for production
- Regularly backup PostgreSQL database
- Change all default passwords before going live
- Test SQL queries before adding them to the application
- Monitor data changes and user activities
- Use HTTPS in production deployments
- Restrict database user permissions to minimum required access
- Review and audit branch-level data access regularly



## System Requirements

Session Management
- Session data is stored in st.session_state
- Session is cleared immediately upon logout
- Session timeout can be configured for production

Performance Considerations
- Recommended screen resolution: 1920x1080 or higher
- Large datasets may require pagination for optimal performance
- Database query optimization recommended for datasets with 100,000+ records
- Plotly charts may require optimization for datasets with 10,000+ rows

Data Handling
- All timestamps follow the server's local timezone
- Currency is displayed in Indian Rupees (₹)
- Decimal values are rounded to 2 places for financial calculations

## Project Information

Created: June 2026
Version: 1.0
Type: Production Ready

## Support and Documentation

For issues and troubleshooting:
1. Review the Troubleshooting section
2. Verify database connectivity
3. Check user credentials and permissions
4. Review PostgreSQL error logs
5. Verify all required tables exist and have proper constraints

For additional documentation:
- Streamlit documentation: https://docs.streamlit.io
- PostgreSQL documentation: https://www.postgresql.org/docs
- Plotly documentation: https://plotly.com/python

## Quick Command Reference

Start application:
```bash
streamlit run LOGIN_interface.py
```

Check installed packages:
```bash
pip list
```

Test database connection:
```bash
psql -U postgres -h localhost -d sales_intelligence_hub
```

Stop application:
```
Ctrl + C
```

Update all dependencies:
```bash
pip install --upgrade -r requirements.txt
```

## License

This project is proprietary and confidential. All rights reserved.
