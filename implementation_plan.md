# Implementation Plan: Gold ERP System (Inspired by Daysum)

## Overview
A comprehensive ERP system for jewelry manufacturing and sales, integrating production, inventory, CRM, sales, and automated accounting. This system is designed to meet the high standards of specialized gold software like **Daysum (ديسم)**.

## 1. Core Modules & Functionality (Daysum-Aligned)

### 🏗️ Manufacturing Management (Core)
- **Production Tracking:** Stages for Casting (سبك), Crafting (صياغة), and Polishing (تلميع).
- **Costing:** Precise calculation of scrap/loss (الهالك) and labor costs.
- **Design Repository:** Management of molds and jewelry designs.
- **Scale Integration:** Real-time data sync with electronic scales for precise weight recording.

### 📦 Inventory & Warehouse (Smart Tracking)
- **Dual Tracking:** Raw materials (gold bars, stones) vs. Finished items.
- **Advanced ID:** Barcode & RFID support for instant stock takes.
- **Gold Weight vs. Value:** Detailed tracking of both gold weight (by carat) and monetary value.
- **Multi-Branch:** Tracking gold movement between branches and vaults with secure handover.

### 👥 CRM & Delegate Management (CRM/Mandoob)
- **Customer Profiles:** Purchase history, preferences, and special occasions.
- **Delegate (Mandoob) Support:** Specialized module to track stocks, sales, and collections for field representatives (الشريطية).
- **Service/Repair:** Tracking jewelry maintenance and warranty claims.

### 💰 Sales, POS & E-Commerce
- **Invoicing:** Support for Sales, Returns, and Exchanges (Gold for Gold).
- **Live Gold Prices:** Integration with global spot prices to update store prices automatically.
- **E-Commerce Sync:** APIs for Salla, Zid, and Shopify to sync inventory and prices.
- **POS Interface:** Touch-optimized UI for retail branches.

### 📑 Accounts & Finance (ZATCA Phase 2)
- **Automatic Ledger:** Real-time journal entries for every transaction (Gold Weight & SAR).
- **ZATCA Phase 2:** Full
### Fix Execution & Correction
#### [NEW] [fix_workshop_6_balance.py](file:///c:/Users/COMPU%20LINE/Desktop/mm/final/gold/fix_workshop_6_balance.py)
- A script to set the workshop balance to the audited value (Initially 100.290).

#### [NEW] [correct_laser_link.py](file:///c:/Users/COMPU%20LINE/Desktop/mm/final/gold/correct_laser_link.py)
- Correct the link between "Laser Treasury" and the Laser Workshop (ID 12).
- Subtract 100g from Workshop 6 and add it to Workshop 12.
 integration with Fatoora portal for Phase 2 (Integration Phase) compliance.
- **Financial Reports:** Balance Sheet, Income Statement, and specialized "Gold Stock" reports.

### 🛒 Purchases & Suppliers
- **Supply Chain:** Managing gold/material purchase orders.
- **Supplier Accounts:** Tracking debt in both Currency and Gold Weight.

## 2. Technical Stack
- **Backend:** Django (Python) - Robust ORM and accounting logic.
- **Frontend:** React + Vite (for POS/Dashboard) OR Modern Django Templates with Premium CSS/JS.
- **Database:** PostgreSQL (Production).
- **Integrations:** REST APIs for Scales, RFID Readers, and ZATCA.

## 3. Specialized Business Logic

### ⚖️ Live Gold Pricing Engine
- Automatically fetch current prices for 24k, 22k, 21k, 18k.
- Allow for "Labor Fees" (المصنعية) per gram or per piece.

### 📊 Automatic Accounting (Double-Entry)
| Event | Debit (من حـ/) | Credit (إلى حـ/) |
| :--- | :--- | :--- |
| **Sales** | Cash/Bank | Inventory (Cost) + Profits |
| **Sales (Gold Exchange)** | New Gold + Difference | Old Gold Inventory |
| **Start Production** | Work in Progress (WIP) | Raw Materials (Weight) |
| **Purchase** | Raw Materials | Accounts Payable (SAR/Weight) |

## 4. Implementation Phases

### Phase 1: Foundation (Current)
- [x] Django Project Setup.
- [ ] Base Models (Core, Manufacturing, Inventory, Sales, CRM, Finance).
- [ ] Authentication & Role-Based Access Control (RBAC).

### Phase 2: Gold-Specific Core
- [x] Analyze Workshop 6 gold balance discrepancies <!-- id: 0 -->
    - [x] Review `audit_workshop_6.py` <!-- id: 1 -->
    - [x] Review `manufacturing/signals.py` and `finance/signals.py` <!-- id: 2 -->
    - [x] Enhance `audit_workshop_6.py` to include missing components (tools, settlements, consumptions) <!-- id: 3 -->
- [x] Implement fix for Workshop 6 balance (Initial attempt) <!-- id: 4 -->
- [ ] Correct Treasury-Workshop mapping and reverse tool transfer <!-- id: 5 -->
    - [ ] Identify and fix `khazina al-laser` link to Workshop 12 <!-- id: 6 -->
    - [ ] Transfer 100g balance from Workshop 6 to Workshop 12 <!-- id: 7 -->
- [ ] Document findings and actions <!-- id: 8 -->
- [ ] Live Gold Price Sync Service.
- [ ] Weight-aware Inventory Management.
- [ ] RFID/Barcode Label Generation.

### Phase 3: Sales, POS & Mandoob
- [ ] POS Interface with Scale Integration.
- [ ] Mandoob (Delegate) Tracking Module.
- [ ] E-wallet & Multi-payment Support.

### Phase 4: Compliance & Reporting
- [ ] ZATCA Phase 2 Integration.
- [ ] Specialized Financial Reports.
- [ ] E-commerce Inventory Sync.
