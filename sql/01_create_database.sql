/*
Inventory Reorder System
01_create_database.sql

Run this script first from a maintenance database such as postgres.

Example:
    psql -U postgres -d postgres -f sql/01_create_database.sql

This script uses psql's \gexec command because PostgreSQL does not support
CREATE DATABASE IF NOT EXISTS in a simple portable statement.
*/

SELECT 'CREATE DATABASE inventory_reorder_system'
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_database
    WHERE datname = 'inventory_reorder_system'
)\gexec

