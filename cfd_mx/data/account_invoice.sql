UPDATE account_invoice AS ai SET internal_number = ai.number;
UPDATE account_invoice AS ai SET tipo_comprobante='I' WHERE type='out_invoice';
UPDATE res_partner AS rp SET formapago_id=metodo_pago;