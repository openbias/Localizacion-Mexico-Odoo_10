UPDATE account_invoice AS ai SET internal_number = ai.number;
UPDATE account_invoice AS ai SET tipo_comprobante='I' WHERE type='out_invoice';