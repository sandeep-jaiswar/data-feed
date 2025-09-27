-- Reference Data Insertion for NSE Data ETL Pipeline
-- Sample NSE symbols and reference data for development and testing
-- Based on actual NSE-listed companies

USE nse_data;

-- Insert major NSE symbols into symbol_master table
INSERT INTO symbol_master (
    symbol, company_name, isin, sector, industry, market_cap, face_value,
    listing_date, upper_circuit, lower_circuit, lot_size, tick_size, is_active
) VALUES
-- Large Cap IT Companies
('TCS', 'Tata Consultancy Services Limited', 'INE467B01029', 'Information Technology', 'IT Services & Consulting', 
 13000000000000, 1.0, '2004-08-25', 4200.0, 2800.0, 1, 0.05, 1),

('INFY', 'Infosys Limited', 'INE009A01021', 'Information Technology', 'IT Services & Consulting', 
 7500000000000, 5.0, '1993-02-11', 1800.0, 1200.0, 1, 0.05, 1),

('WIPRO', 'Wipro Limited', 'INE075A01022', 'Information Technology', 'IT Services & Consulting', 
 2500000000000, 2.0, '1980-11-08', 650.0, 400.0, 1, 0.05, 1),

('HCLTECH', 'HCL Technologies Limited', 'INE860A01027', 'Information Technology', 'IT Services & Consulting', 
 3500000000000, 2.0, '2000-01-06', 1650.0, 1100.0, 1, 0.05, 1),

-- Banking Sector
('HDFCBANK', 'HDFC Bank Limited', 'INE040A01034', 'Financial Services', 'Private Sector Bank', 
 9000000000000, 1.0, '1995-11-08', 1750.0, 1250.0, 1, 0.05, 1),

('ICICIBANK', 'ICICI Bank Limited', 'INE090A01021', 'Financial Services', 'Private Sector Bank', 
 6500000000000, 2.0, '1999-12-30', 1100.0, 800.0, 1, 0.05, 1),

('SBIN', 'State Bank of India', 'INE062A01020', 'Financial Services', 'Public Sector Bank', 
 4500000000000, 1.0, '1977-03-01', 650.0, 450.0, 1, 0.05, 1),

('AXISBANK', 'Axis Bank Limited', 'INE238A01034', 'Financial Services', 'Private Sector Bank', 
 3000000000000, 2.0, '1998-02-16', 1300.0, 900.0, 1, 0.05, 1),

-- Oil & Gas
('RELIANCE', 'Reliance Industries Limited', 'INE002A01018', 'Oil & Gas', 'Petroleum Products', 
 15000000000000, 10.0, '1977-11-29', 2750.0, 2250.0, 1, 0.05, 1),

('ONGC', 'Oil and Natural Gas Corporation Limited', 'INE213A01029', 'Oil & Gas', 'Oil Exploration & Production', 
 2800000000000, 5.0, '1995-07-19', 280.0, 180.0, 1, 0.05, 1),

-- FMCG
('HINDUNILVR', 'Hindustan Unilever Limited', 'INE030A01027', 'FMCG', 'Personal Products', 
 5500000000000, 1.0, '1956-07-01', 2800.0, 2200.0, 1, 0.05, 1),

('ITC', 'ITC Limited', 'INE154A01025', 'FMCG', 'Tobacco Products', 
 5000000000000, 1.0, '1956-08-24', 500.0, 350.0, 1, 0.05, 1),

('NESTLEIND', 'Nestle India Limited', 'INE239A01016', 'FMCG', 'Food Products', 
 2200000000000, 1.0, '1995-08-01', 2500.0, 2000.0, 1, 0.05, 1),

-- Pharmaceutical
('SUNPHARMA', 'Sun Pharmaceutical Industries Limited', 'INE044A01036', 'Healthcare', 'Pharmaceuticals', 
 2400000000000, 1.0, '1994-02-08', 1200.0, 800.0, 1, 0.05, 1),

('DRREDDY', 'Dr. Reddys Laboratories Limited', 'INE089A01023', 'Healthcare', 'Pharmaceuticals', 
 900000000000, 5.0, '1986-04-30', 6500.0, 4500.0, 1, 0.05, 1),

-- Automobiles
('MARUTI', 'Maruti Suzuki India Limited', 'INE585B01010', 'Automobile', 'Passenger Cars & Utility Vehicles', 
 3200000000000, 5.0, '2003-07-09', 12000.0, 8000.0, 1, 0.05, 1),

('TATAMOTORS', 'Tata Motors Limited', 'INE155A01022', 'Automobile', 'Passenger Cars & Utility Vehicles', 
 2800000000000, 2.0, '1998-07-22', 1000.0, 600.0, 1, 0.05, 1),

('M&M', 'Mahindra & Mahindra Limited', 'INE101A01026', 'Automobile', 'Passenger Cars & Utility Vehicles', 
 2500000000000, 5.0, '1992-01-03', 2000.0, 1400.0, 1, 0.05, 1),

-- Metals & Mining
('TATASTEEL', 'Tata Steel Limited', 'INE081A01020', 'Metals & Mining', 'Iron & Steel', 
 1800000000000, 1.0, '1992-11-18', 150.0, 100.0, 1, 0.05, 1),

('HINDALCO', 'Hindalco Industries Limited', 'INE038A01020', 'Metals & Mining', 'Aluminium', 
 1200000000000, 1.0, '1995-01-04', 650.0, 400.0, 1, 0.05, 1),

-- Cement
('ULTRACEMCO', 'UltraTech Cement Limited', 'INE481G01011', 'Construction Materials', 'Cement & Cement Products', 
 2100000000000, 10.0, '2004-08-24', 11000.0, 7500.0, 1, 0.05, 1),

('SHREECEM', 'Shree Cement Limited', 'INE070A01015', 'Construction Materials', 'Cement & Cement Products', 
 950000000000, 10.0, '1985-09-26', 27000.0, 20000.0, 1, 0.05, 1),

-- Power
('NTPC', 'NTPC Limited', 'INE733E01010', 'Power', 'Power Generation/Distribution', 
 3500000000000, 10.0, '2004-11-05', 400.0, 250.0, 1, 0.05, 1),

('POWERGRID', 'Power Grid Corporation of India Limited', 'INE752E01010', 'Power', 'Power Generation/Distribution', 
 2200000000000, 10.0, '2007-10-05', 350.0, 200.0, 1, 0.05, 1),

-- Telecom
('BHARTIARTL', 'Bharti Airtel Limited', 'INE397D01024', 'Telecommunication', 'Telecom Services', 
 4500000000000, 5.0, '2002-02-15', 1200.0, 800.0, 1, 0.05, 1),

-- Indices (for reference)
('NIFTY50', 'NIFTY 50 Index', '', 'Index', 'Equity Index', NULL, NULL, NULL, NULL, NULL, 1, 0.05, 1),
('BANKNIFTY', 'NIFTY Bank Index', '', 'Index', 'Sectoral Index', NULL, NULL, NULL, NULL, NULL, 1, 0.05, 1),
('NIFTYIT', 'NIFTY IT Index', '', 'Index', 'Sectoral Index', NULL, NULL, NULL, NULL, NULL, 1, 0.05, 1);

-- Insert some sample market events
INSERT INTO market_events (
    id, symbol, event_type, event_date, ex_date, record_date, 
    event_description, impact_factor, announcement_date, source
) VALUES
(1, 'TCS', 1, '2024-01-15', '2024-01-12', '2024-01-10', 'Interim Dividend Rs 9 per share', 9.0, '2024-01-08', 'NSE'),
(2, 'RELIANCE', 2, '2024-02-20', '2024-02-18', '2024-02-15', 'Bonus Issue 1:1', 1.0, '2024-02-10', 'NSE'),
(3, 'INFY', 1, '2024-03-10', '2024-03-08', '2024-03-05', 'Final Dividend Rs 16 per share', 16.0, '2024-03-01', 'NSE'),
(4, 'HDFCBANK', 1, '2024-03-25', '2024-03-22', '2024-03-20', 'Interim Dividend Rs 19.50 per share', 19.5, '2024-03-15', 'NSE'),
(5, 'MARUTI', 3, '2024-04-15', '2024-04-12', '2024-04-10', 'Stock Split 1:2', 2.0, '2024-04-05', 'NSE'),
(6, 'SUNPHARMA', 8, '2024-04-30', NULL, NULL, 'Q4 FY24 Results - Revenue up 12% YoY', NULL, '2024-04-30', 'BSE'),
(7, 'WIPRO', 1, '2024-05-20', '2024-05-17', '2024-05-15', 'Special Dividend Rs 5 per share', 5.0, '2024-05-10', 'NSE'),
(8, 'ICICIBANK', 8, '2024-06-15', NULL, NULL, 'Q1 FY25 Results - Net profit up 15% YoY', NULL, '2024-06-15', 'NSE');

-- Note: This is sample reference data for development and testing
-- In production, this data would be sourced from:
-- 1. NSE official symbol list
-- 2. Corporate announcements
-- 3. Stock exchange feeds
-- 4. Financial data providers

-- Verify the inserted data
-- SELECT COUNT(*) FROM symbol_master;
-- SELECT COUNT(*) FROM market_events;
-- SELECT sector, COUNT(*) FROM symbol_master GROUP BY sector ORDER BY COUNT(*) DESC;