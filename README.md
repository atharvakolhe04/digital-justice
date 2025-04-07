# Digital Justice System

A comprehensive digital platform for modernizing law enforcement processes, addressing issues of paper-based documentation, data inconsistency, corruption risks, and lack of transparency.

## Key Features

### 1. Document Digitalization Module
- Digital vault for storing verified documents
- QR code for document verification
- Role-based access control for government officials

### 2. Fine and Penalty Management System
- E-Challan generation and tracking
- Payment gateway integration
- Immutable logging of all transactions
- Real-time dashboards for citizens and officials

### 3. Dispute Resolution Platform
- Challan dispute filing system
- Case tracking and notification system
- Evidence management and submission

### 4. Communication Portal
- Messaging between citizens and government
- Notification system for pending documents/fines
- SOS feature for emergencies

## Setup Instructions

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Initialize the database:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```
4. Run the application:
   ```
   flask run
   ```

## User Roles

- **Citizens**: Regular users who can access their documents, pay fines, file disputes, and communicate with officials
- **Police Officers**: Can generate e-challans, verify documents, and respond to citizen queries
- **Court Officials**: Can manage dispute cases, review evidence, and make decisions
- **Administrators**: Have full system access for management and configuration
