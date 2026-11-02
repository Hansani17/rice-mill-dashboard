# Data dictionary (synthetic data, 1 May to 31 Oct 2026)

Money is in Rs. Dates are ISO (yyyy-mm-dd). `paddy_type`: Samba, Nadu, Red. `process_type`: Parboiled, Raw.

| File | Columns |
|---|---|
| dim_partner | partner_id, partner_name, partner_type, phone, town, is_supplier, is_customer |
| dim_product | product_id, product_name, sale_form |
| opening_paddy | paddy_type, quantity_kg |
| opening_rice | product_id, quantity_kg |
| fact_paddy_purchase | purchase_id, purchase_date, partner_id, paddy_type, weight_kg, price_per_kg, total_amount |
| fact_payment_paddy | payment_id, payment_date, purchase_id, amount, method |
| fact_production_batch | batch_id, batch_date, paddy_type, process_type, product_id, input_kg, output_kg, husk_kg, polisher_kg, broken_kg (by-product columns blank in about 12% of batches) |
| fact_rice_sale | sale_id, sale_date, partner_id, total_amount |
| fact_rice_sale_line | line_id, sale_id, product_id, pack_size_kg, packs, quantity_kg, price_per_kg, line_total (pack columns blank for loose rice) |
| fact_payment_rice | payment_id, payment_date, sale_id, amount, method |
| fact_byproduct_sale | sale_id, sale_date, partner_id, byproduct_type, quantity_kg, price_per_kg, total_amount |
| fact_payment_byproduct | payment_id, payment_date, sale_id, amount, method |
| fact_expense | expense_id, expense_date, category, amount, description |

Balances are not stored: balance = total minus the sum of payments.
